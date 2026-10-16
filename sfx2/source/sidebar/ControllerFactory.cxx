/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * This file incorporates work covered by the following license notice:
 *
 *   Licensed to the Apache Software Foundation (ASF) under one or more
 *   contributor license agreements. See the NOTICE file distributed
 *   with this work for additional information regarding copyright
 *   ownership. The ASF licenses this file to you under the Apache
 *   License, Version 2.0 (the "License"); you may not use this file
 *   except in compliance with the License. You may obtain a copy of
 *   the License at http://www.apache.org/licenses/LICENSE-2.0 .
 */

#include <sidebar/ControllerFactory.hxx>
#include <sidebar/Tools.hxx>
#include <svl/itempool.hxx>
#include <unoctitm.hxx>

#include <com/sun/star/beans/PropertyValue.hpp>
#include <com/sun/star/frame/XToolbarController.hpp>
#include <com/sun/star/frame/XFrame.hpp>
#include <com/sun/star/frame/theToolbarControllerFactory.hpp>
#include <com/sun/star/lang/XMultiServiceFactory.hpp>

#include <framework/sfxhelperfunctions.hxx>
#include <framework/generictoolbarcontroller.hxx>
#include <vcl/toolbox.hxx>
#include <vcl/commandinfoprovider.hxx>
#include <vcl/weld/Toolbar.hxx>
#include <vcl/weld/TransportAsXWindow.hxx>
#include <comphelper/processfactory.hxx>
#include <toolkit/helper/vclunohelper.hxx>

using namespace css;
using namespace css::uno;

namespace sfx2::sidebar {

namespace {

/// Whether a disabled state that update() gave the item will be kept up to date: the frame has a
/// dispatch for the command, asked the way ToolboxController::bindListener asks it (the command,
/// else its real command when it is an alias), and it is not a master command (".uno:X.y"), whose
/// dispatch is not bound to the slot's state cache and never sends a state again.
bool HasStatefulDispatch(const Reference<frame::XFrame>& rxFrame, const OUString& rsCommandName,
                         const Sequence<beans::PropertyValue>& rProperties)
{
    try
    {
        util::URL aURL(Tools::GetURL(rsCommandName));
        if (SfxOfficeDispatch::IsMasterUnoCommand(aURL))
            return false;
        if (Tools::GetDispatch(rxFrame, aURL).is())
            return true;
        const OUString sRealCommand(vcl::CommandInfoProvider::GetRealCommandForCommand(rProperties));
        if (sRealCommand.isEmpty())
            return false;
        aURL = Tools::GetURL(sRealCommand);
        return !SfxOfficeDispatch::IsMasterUnoCommand(aURL) && Tools::GetDispatch(rxFrame, aURL).is();
    }
    catch (const Exception&)
    {
        return false;
    }
}

}

Reference<lang::XComponent> ControllerFactory::CreateImageController(
    const Reference<frame::XFrame>& rxFrame,
    const Reference<awt::XWindow>& rxParentWindow)
{
    rtl::Reference xController(new framework::ImageOrientationController(
        comphelper::getProcessComponentContext(), rxFrame, rxParentWindow,
        vcl::CommandInfoProvider::GetModuleIdentifier(rxFrame)));

    xController->update();
    return xController;
}

Reference<frame::XToolbarController> ControllerFactory::CreateToolBoxController(
    ToolBox* pToolBox,
    const ToolBoxItemId nItemId,
    const OUString& rsCommandName,
    const Reference<frame::XFrame>& rxFrame,
    const Reference<frame::XController>& rxController,
    const Reference<awt::XWindow>& rxParentWindow,
    const sal_Int32 nWidth, bool bSideBar)
{
    Reference<frame::XToolbarController> xController (
        CreateToolBarController(
            VCLUnoHelper::GetInterface(pToolBox),
            rsCommandName,
            rxFrame, rxController,
            nWidth, bSideBar));

    bool bFactoryHasController( xController.is() );

    // Create a controller for the new item.
    if ( !bFactoryHasController )
    {
        xController = ::framework::CreateToolBoxController(
                    rxFrame,
                    pToolBox,
                    nItemId,
                    rsCommandName);
    }
    if ( ! xController.is())
    {
        xController = new framework::GenericToolbarController(
                    ::comphelper::getProcessComponentContext(),
                    rxFrame,
                    pToolBox,
                    nItemId,
                    rsCommandName);
    }

    // Initialize the controller with eg a service factory.
    Reference<lang::XInitialization> xInitialization (xController, UNO_QUERY);
    if (!bFactoryHasController && xInitialization.is())
    {
        beans::PropertyValue aPropValue;
        std::vector<Any> aPropertyVector;

        aPropValue.Name = "Frame";
        aPropValue.Value <<= rxFrame;
        aPropertyVector.push_back(Any(aPropValue));

        aPropValue.Name = "ServiceManager";
        aPropValue.Value <<= ::comphelper::getProcessServiceFactory();
        aPropertyVector.push_back(Any(aPropValue));

        aPropValue.Name = "CommandURL";
        aPropValue.Value <<= rsCommandName;
        aPropertyVector.push_back(Any(aPropValue));

        Sequence<Any> aArgs (comphelper::containerToSequence(aPropertyVector));
        xInitialization->initialize(aArgs);
    }

    if (xController.is())
    {
        if (rxParentWindow.is())
        {
            Reference<awt::XWindow> xItemWindow (xController->createItemWindow(rxParentWindow));
            VclPtr<vcl::Window> pItemWindow = VCLUnoHelper::GetWindow(xItemWindow);
            if (pItemWindow != nullptr)
            {
                WindowType eType = pItemWindow->GetType();
                if (eType == WindowType::LISTBOX || eType == WindowType::MULTILISTBOX || eType == WindowType::COMBOBOX)
                    pItemWindow->SetAccessibleName(pToolBox->GetItemText(nItemId));
                if (nWidth > 0)
                    pItemWindow->SetSizePixel(Size(nWidth, pItemWindow->GetSizePixel().Height()));
                pToolBox->SetItemWindow(nItemId, pItemWindow);
            }
        }

        Reference<util::XUpdatable> xUpdatable (xController, UNO_QUERY);
        if (xUpdatable.is())
            xUpdatable->update();

        // Add tooltip.
        if (xController.is())
        {
            auto aProperties = vcl::CommandInfoProvider::GetCommandProperties(rsCommandName,
                vcl::CommandInfoProvider::GetModuleIdentifier(rxFrame));
            const OUString sTooltip (vcl::CommandInfoProvider::GetTooltipForCommand(
                    rsCommandName, aProperties, rxFrame));
            if (pToolBox->GetQuickHelpText(nItemId).isEmpty())
                pToolBox->SetQuickHelpText(nItemId, sTooltip);
            // update() gave the item the state of its command. A command without a dispatch (a
            // dropdown that only opens its popup) was reported disabled for that reason alone, and
            // a master command's dispatch never updates it, so enable those. Keep a disabled state
            // that a bound dispatch reported: nothing sends it again while it does not change,
            // e.g. on a second toolbox that shows the same slot.
            if (!pToolBox->IsItemEnabled(nItemId)
                && !HasStatefulDispatch(rxFrame, rsCommandName, aProperties))
                pToolBox->EnableItem(nItemId);
        }
    }

    return xController;
}

Reference<frame::XToolbarController> ControllerFactory::CreateToolBoxController(
    weld::Toolbar& rToolbar, weld::Builder& rBuilder,
    const OUString& rsCommandName,
    const Reference<frame::XFrame>& rxFrame,
    const Reference<frame::XController>& rxController,
    bool bSideBar)
{
    css::uno::Reference<css::awt::XWindow> xWidget(new weld::TransportAsXWindow(&rToolbar, &rBuilder));

    Reference<frame::XToolbarController> xController(
        CreateToolBarController(
            xWidget,
            rsCommandName,
            rxFrame, rxController,
            -1, bSideBar));

    if (!xController.is())
    {
        xController = new framework::GenericToolbarController(
                    ::comphelper::getProcessComponentContext(),
                    rxFrame,
                    rToolbar,
                    rsCommandName);
    }

    if (xController.is())
    {
        xController->createItemWindow(xWidget);

        Reference<util::XUpdatable> xUpdatable(xController, UNO_QUERY);
        if (xUpdatable.is())
            xUpdatable->update();
    }

    return xController;
}


Reference<frame::XToolbarController> ControllerFactory::CreateToolBarController(
    const Reference<awt::XWindow>& rxToolbar,
    const OUString& rsCommandName,
    const Reference<frame::XFrame>& rxFrame,
    const Reference<frame::XController>& rxController,
    const sal_Int32 nWidth, bool bSideBar)
{
    try
    {
        const Reference<XComponentContext>& xContext = comphelper::getProcessComponentContext();
        Reference<frame::XUIControllerFactory> xFactory = frame::theToolbarControllerFactory::get( xContext );
        OUString sModuleName (Tools::GetModuleName(rxController));

        if (xFactory.is() && xFactory->hasController(rsCommandName,  sModuleName))
        {
            beans::PropertyValue aPropValue;
            std::vector<Any> aPropertyVector;

            aPropValue.Name = "ModuleIdentifier";
            aPropValue.Value <<= sModuleName;
            aPropertyVector.push_back( Any( aPropValue ));

            aPropValue.Name = "Frame";
            aPropValue.Value <<= rxFrame;
            aPropertyVector.push_back( Any( aPropValue ));

            aPropValue.Name = "ServiceManager";
            aPropValue.Value <<= comphelper::getProcessServiceFactory();
            aPropertyVector.push_back( Any( aPropValue ));

            aPropValue.Name = "ParentWindow";
            aPropValue.Value <<= rxToolbar;
            aPropertyVector.push_back( Any( aPropValue ));

            aPropValue.Name = "IsSidebar";
            aPropValue.Value <<= bSideBar;
            aPropertyVector.push_back( Any( aPropValue ));

            if (nWidth > 0)
            {
                aPropValue.Name = "Width";
                aPropValue.Value <<= nWidth;
                aPropertyVector.push_back( Any( aPropValue ));
            }

            Sequence<Any> aArgs (comphelper::containerToSequence(aPropertyVector));
            return Reference<frame::XToolbarController>(
                xFactory->createInstanceWithArgumentsAndContext(
                    rsCommandName,
                    aArgs,
                    xContext),
                UNO_QUERY);
        }
    }
    catch (Exception&)
    {
        // Ignore exception.
    }
    return nullptr;
}

} // end of namespace sfx2::sidebar

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
