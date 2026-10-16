/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

/* The menus of the Function Library dropdowns of the Formulas tab, like Excel's: Recently Used,
   Financial, Logical, Text, Date & Time, Lookup & Reference, Math & Trig and More Functions.
   One popup menu controller serves all of them: the command it is created for names the
   function category. A menu is built each time it opens, from the function manager, so it lists
   the functions in the language of the formulas (localized or English names) and the current
   recently used list. Each function item inserts its function into the cell the way the
   Functions sidebar does; the last item of each menu is "Function...", the Function Wizard. */

#include <com/sun/star/awt/MenuEvent.hpp>
#include <com/sun/star/awt/XPopupMenu.hpp>
#include <com/sun/star/uno/XComponentContext.hpp>
#include <svtools/popupmenucontrollerbase.hxx>
#include <toolkit/awt/vclxmenu.hxx>
#include <unotools/charclass.hxx>
#include <vcl/commandinfoprovider.hxx>
#include <vcl/svapp.hxx>

#include <compiler.hxx>
#include <funcdesc.hxx>
#include <global.hxx>
#include <scfuncs.hxx>
#include <scmod.hxx>

#include <iterator>
#include <optional>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace css;

namespace
{
// Not a category of scfuncs.hxx (they start at 1): the recently used functions of ScAppOptions.
constexpr sal_uInt16 RECENTLY_USED = 0;

// Menu command -> function category. Lookup & Reference is LibreOffice's Spreadsheet category,
// Math & Trig its Mathematical one and Engineering its Add-in one (the Analysis add-in).
constexpr std::pair<std::u16string_view, sal_uInt16> CATEGORY_MENUS[] = {
    { u".uno:FormulasRecentlyUsedMenu", RECENTLY_USED },
    { u".uno:FormulasFinancialMenu", ID_FUNCTION_GRP_FINANCIAL },
    { u".uno:FormulasLogicalMenu", ID_FUNCTION_GRP_LOGIC },
    { u".uno:FormulasTextMenu", ID_FUNCTION_GRP_TEXT },
    { u".uno:FormulasDateTimeMenu", ID_FUNCTION_GRP_DATETIME },
    { u".uno:FormulasLookupMenu", ID_FUNCTION_GRP_TABLE },
    { u".uno:FormulasMathMenu", ID_FUNCTION_GRP_MATH },
    { u".uno:FormulasStatisticalMenu", ID_FUNCTION_GRP_STATISTIC },
    { u".uno:FormulasEngineeringMenu", ID_FUNCTION_GRP_ADDINS },
    { u".uno:FormulasInformationMenu", ID_FUNCTION_GRP_INFO },
    { u".uno:FormulasDatabaseMenu", ID_FUNCTION_GRP_DATABASE },
    { u".uno:FormulasArrayMenu", ID_FUNCTION_GRP_MATRIX },
};

// More Functions has one submenu per category: Excel's Statistical, Engineering and Information,
// then LibreOffice's Database and Array. Excel's Cube, Compatibility and Web have no category.
constexpr std::u16string_view MORE_FUNCTIONS = u".uno:FormulasMoreFunctionsMenu";
constexpr std::u16string_view MORE_FUNCTIONS_SUBMENUS[]
    = { u".uno:FormulasStatisticalMenu", u".uno:FormulasEngineeringMenu",
        u".uno:FormulasInformationMenu", u".uno:FormulasDatabaseMenu", u".uno:FormulasArrayMenu" };

constexpr OUString FUNCTION_DIALOG = u".uno:FunctionDialog"_ustr;

std::optional<sal_uInt16> categoryOf(std::u16string_view aCommand)
{
    for (const auto& [rCommand, nCategory] : CATEGORY_MENUS)
        if (rCommand == aCommand)
            return nCategory;
    return {};
}

OUString labelOf(const OUString& rCommand, const OUString& rModule)
{
    return vcl::CommandInfoProvider::GetPopupLabelForCommand(
        vcl::CommandInfoProvider::GetCommandProperties(rCommand, rModule));
}

class FunctionMenuController : public svt::PopupMenuControllerBase
{
public:
    explicit FunctionMenuController(const uno::Reference<uno::XComponentContext>& rxContext)
        : svt::PopupMenuControllerBase(rxContext)
    {
    }

    // XServiceInfo
    OUString SAL_CALL getImplementationName() override
    {
        return u"com.sun.star.comp.Calc.FunctionMenuController"_ustr;
    }
    uno::Sequence<OUString> SAL_CALL getSupportedServiceNames() override
    {
        return { u"com.sun.star.frame.PopupMenuController"_ustr };
    }

    // XStatusListener: the menu commands have no slot, so no state ever arrives
    void SAL_CALL statusChanged(const frame::FeatureStateEvent&) override {}

    // XPopupMenuController: called each time the dropdown opens
    void SAL_CALL updatePopupMenu() override;

    // XMenuListener: the menu and each of its submenus report to this controller
    void SAL_CALL itemSelected(const awt::MenuEvent& rEvent) override;

private:
    void fillCategory(VCLXPopupMenu& rMenu, sal_uInt16 nCategory, sal_Int16& rItemId);
    void addFunction(VCLXPopupMenu& rMenu, const ScFuncDesc& rDesc, sal_Int16& rItemId);

    // The function (ScFuncDesc::nFIndex) of each function item, for the recently used list. Item
    // ids are unique across the menu and its submenus. Guarded by the SolarMutex.
    std::unordered_map<sal_Int16, sal_uInt16> m_aFunctionOfItem;
};

void FunctionMenuController::updatePopupMenu()
{
    rtl::Reference<VCLXPopupMenu> xMenu;
    OUString aCommand, aModule;
    {
        std::unique_lock aLock(m_aMutex);
        throwIfDisposed(aLock);
        xMenu = m_xPopupMenu;
        aCommand = m_aCommandURL;
        aModule = m_aModuleName;
    }

    SolarMutexGuard aGuard;
    if (!xMenu.is() || !ScModule::get()) // the function manager needs the Calc module
        return;

    m_aFunctionOfItem.clear();
    if (aCommand == MORE_FUNCTIONS)
    {
        // VCLXMenu holds on to every submenu it is given, clear() included, so the submenus are
        // made once and only their functions are filled anew each time
        if (xMenu->getItemCount() == 0)
        {
            sal_Int16 nItemId = 1;
            for (std::u16string_view aSubmenu : MORE_FUNCTIONS_SUBMENUS)
            {
                const OUString aSubCommand(aSubmenu);
                xMenu->insertItem(nItemId, labelOf(aSubCommand, aModule), 0, -1);
                xMenu->setCommand(nItemId, aSubCommand);
                rtl::Reference<VCLXPopupMenu> xSubmenu = new VCLXPopupMenu;
                xSubmenu->addMenuListener(uno::Reference<awt::XMenuListener>(this));
                xMenu->setPopupMenu(nItemId++, xSubmenu);
            }
            xMenu->insertSeparator(-1);
            xMenu->insertItem(nItemId, labelOf(FUNCTION_DIALOG, aModule), 0, -1);
            xMenu->setCommand(nItemId, FUNCTION_DIALOG);
        }
        sal_Int16 nItemId = xMenu->getItemCount() + 1; // past the ids of the menu's own items
        for (sal_Int16 nPos = 0; nPos < sal_Int16(std::size(MORE_FUNCTIONS_SUBMENUS)); ++nPos)
        {
            const sal_Int16 nSubmenuId = xMenu->getItemId(nPos);
            uno::Reference<awt::XPopupMenu> xSubmenu = xMenu->getPopupMenu(nSubmenuId);
            auto pSubmenu = dynamic_cast<VCLXPopupMenu*>(xSubmenu.get());
            std::optional<sal_uInt16> oCategory = categoryOf(xMenu->getCommand(nSubmenuId));
            if (!pSubmenu || !oCategory)
                continue;
            resetPopupMenu(xSubmenu);
            fillCategory(*pSubmenu, *oCategory, nItemId);
        }
        return;
    }

    std::optional<sal_uInt16> oCategory = categoryOf(aCommand);
    if (!oCategory)
        return;
    resetPopupMenu(xMenu);
    sal_Int16 nItemId = 1;
    fillCategory(*xMenu, *oCategory, nItemId);
    if (xMenu->getItemCount() > 0)
        xMenu->insertSeparator(-1);
    xMenu->insertItem(nItemId, labelOf(FUNCTION_DIALOG, aModule), 0, -1);
    xMenu->setCommand(nItemId, FUNCTION_DIALOG);
}

void FunctionMenuController::fillCategory(VCLXPopupMenu& rMenu, sal_uInt16 nCategory,
                                          sal_Int16& rItemId)
{
    const ScFunctionMgr* pFuncMgr = ScGlobal::GetStarCalcFunctionMgr();
    if (nCategory == RECENTLY_USED)
    {
        std::vector<const formula::IFunctionDescription*> aRecent;
        pFuncMgr->fillLastRecentlyUsedFunctions(aRecent);
        for (const formula::IFunctionDescription* pDesc : aRecent)
            if (auto pFuncDesc = dynamic_cast<const ScFuncDesc*>(pDesc))
                addFunction(rMenu, *pFuncDesc, rItemId);
        return;
    }
    // sorted by name, like the Function Wizard and the Functions sidebar
    for (const ScFuncDesc* pDesc = pFuncMgr->First(nCategory); pDesc; pDesc = pFuncMgr->Next())
        addFunction(rMenu, *pDesc, rItemId);
}

void FunctionMenuController::addFunction(VCLXPopupMenu& rMenu, const ScFuncDesc& rDesc,
                                         sal_Int16& rItemId)
{
    if (rDesc.isHidden()) // as in the Function Wizard
        return;
    // SID_INS_FUNCTION looks the upper-case name up among all functions (category 0), with
    // this character class. A function name is a formula identifier: it has no '&', '=' or '%'
    // that would end or escape the URL argument.
    const CharClass* pCharClass = ScGlobal::GetStarCalcFunctionList()->IsEnglishFunctionNames()
                                      ? ScCompiler::GetCharClassEnglish()
                                      : ScCompiler::GetCharClassLocalized();
    const OUString aName = pCharClass->uppercase(rDesc.getFunctionName());
    if (aName.isEmpty())
        return;

    rMenu.insertItem(rItemId, aName, 0, -1);
    rMenu.setCommand(rItemId, ".uno:InsertFunction?FunctionName:string=" + aName
                                  + "&FunctionCategory:short=0");
    // The tooltip, as in Excel: the signature, then the short description. An add-in function
    // read from the configuration has no argument names yet, so its signature would be wrong.
    OUString aTip = rDesc.getDescription();
    if (!rDesc.bIncomplete)
        aTip = aTip.isEmpty() ? rDesc.getSignature() : rDesc.getSignature() + "\n" + aTip;
    rMenu.setTipHelpText(rItemId, aTip);
    m_aFunctionOfItem[rItemId] = rDesc.nFIndex;
    ++rItemId;
}

void FunctionMenuController::itemSelected(const awt::MenuEvent& rEvent)
{
    OUString aCommand;
    {
        SolarMutexGuard aGuard;
        uno::Reference<awt::XPopupMenu> xMenu(rEvent.Source, uno::UNO_QUERY);
        if (!xMenu.is())
            return;
        aCommand = xMenu->getCommand(rEvent.MenuId);
        // a function used from a menu goes to the top of the recently used list, as from the
        // Functions sidebar
        auto it = m_aFunctionOfItem.find(rEvent.MenuId);
        ScModule* pScMod = ScModule::get();
        if (it != m_aFunctionOfItem.end() && pScMod)
            pScMod->InsertEntryToLRUList(it->second);
    }
    if (!aCommand.isEmpty())
        dispatchCommand(aCommand, {});
}
}

extern "C" SAL_DLLPUBLIC_EXPORT css::uno::XInterface*
Calc_FunctionMenuController_get_implementation(css::uno::XComponentContext* pContext,
                                               css::uno::Sequence<css::uno::Any> const&)
{
    return cppu::acquire(new FunctionMenuController(pContext));
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
