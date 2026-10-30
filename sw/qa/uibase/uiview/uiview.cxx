/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#include <swmodeltestbase.hxx>

#include <LibreOfficeKit/LibreOfficeKitEnums.h>
#include <comphelper/OAccessible.hxx>
#include <comphelper/processfactory.hxx>
#include <osl/file.hxx>
#include <comphelper/propertyvalue.hxx>
#include <comphelper/scopeguard.hxx>
#include <vcl/scheduler.hxx>
#include <sfx2/viewfrm.hxx>
#include <sfx2/bindings.hxx>
#include <sfx2/dispatch.hxx>
#include <sfx2/lokhelper.hxx>
#include <test/lokcallback.hxx>
#include <comphelper/string.hxx>
#include <svl/style.hxx>
#include <vcl/toolbox.hxx>

#include <com/sun/star/accessibility/AccessibleRole.hpp>
#include <com/sun/star/accessibility/XAccessibleContext.hpp>
#include <com/sun/star/container/XNamed.hpp>
#include <com/sun/star/frame/XLayoutManager.hpp>
#include <com/sun/star/frame/XDispatchHelper.hpp>
#include <com/sun/star/frame/XDispatchProvider.hpp>
#include <com/sun/star/frame/XComponentLoader.hpp>
#include <com/sun/star/frame/XStorable2.hpp>
#include <com/sun/star/lang/XMultiServiceFactory.hpp>
#include <com/sun/star/packages/zip/ZipFileAccess.hpp>
#include <com/sun/star/style/XStyleFamiliesSupplier.hpp>
#include <com/sun/star/view/XSelectionSupplier.hpp>
#include <com/sun/star/text/XParagraphCursor.hpp>

#include <cmdid.h>
#include <unotxdoc.hxx>
#include <docsh.hxx>
#include <wrtsh.hxx>
#include <swmodule.hxx>
#include <view.hxx>
#include <IDocumentRedlineAccess.hxx>

#include <algorithm>
#include <optional>
#include <unordered_set>

/// Covers sw/source/uibase/uiview/ fixes.
class SwUibaseUiviewTest : public SwModelTestBase
{
public:
    SwUibaseUiviewTest()
        : SwModelTestBase(u"/sw/qa/uibase/uiview/data/"_ustr)
    {
    }
};

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testUpdateAllObjectReplacements)
{
    // Make a temporary copy of the test document
    createTempCopy(u"updateall-objectreplacements.odt");

    /* BASIC code that exhibits the problem:

    desktop = CreateUnoService("com.sun.star.frame.Desktop")
    Dim props(0) as new com.sun.star.beans.PropertyValue
    props(0).Name = "Hidden"
    props(0).Value = true
    component = desktop.loadComponentFromURL("file://.../test.odt", "_default", 0, props)
    Wait 1000 ' workaround
    dispatcher = createUnoService("com.sun.star.frame.DispatchHelper")
    frame = component.CurrentController.Frame
    dispatcher.executeDispatch(frame, ".uno:UpdateAll", "", 0, Array())
    component.storeSelf(Array())
    component.dispose()
    */

    uno::Reference<lang::XMultiServiceFactory> xFactory(comphelper::getProcessServiceFactory());

    // Load the copy
    uno::Reference<uno::XInterface> xInterface
        = xFactory->createInstance(u"com.sun.star.frame.Desktop"_ustr);
    uno::Reference<frame::XComponentLoader> xComponentLoader(xInterface, uno::UNO_QUERY);
    uno::Sequence<beans::PropertyValue> aLoadArgs{ comphelper::makePropertyValue(u"Hidden"_ustr,
                                                                                 true) };
    mxComponent = xComponentLoader->loadComponentFromURL(maTempFile.GetURL(), u"_default"_ustr, 0,
                                                         aLoadArgs);

    // Perform the .uno:UpdateAll call and save
    xInterface = xFactory->createInstance(u"com.sun.star.frame.DispatchHelper"_ustr);
    uno::Reference<frame::XDispatchHelper> xDispatchHelper(xInterface, uno::UNO_QUERY);
    uno::Reference<frame::XModel> xModel(mxComponent, uno::UNO_QUERY);
    uno::Reference<frame::XDispatchProvider> xDispatchProvider(
        xModel->getCurrentController()->getFrame(), uno::UNO_QUERY);
    uno::Sequence<beans::PropertyValue> aNoArgs;
    xDispatchHelper->executeDispatch(xDispatchProvider, u".uno:UpdateAll"_ustr, OUString(), 0,
                                     aNoArgs);
    uno::Reference<frame::XStorable2> xStorable(mxComponent, uno::UNO_QUERY);
    xStorable->storeSelf(aNoArgs);

    // Check the contents of the updated copy and verify that ObjectReplacements are there
    uno::Reference<packages::zip::XZipFileAccess2> xNameAccess
        = packages::zip::ZipFileAccess::createWithURL(comphelper::getComponentContext(xFactory),
                                                      maTempFile.GetURL());

    CPPUNIT_ASSERT(xNameAccess->hasByName(u"ObjectReplacements/Components"_ustr));
    CPPUNIT_ASSERT(xNameAccess->hasByName(u"ObjectReplacements/Components_1"_ustr));
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testUpdateReplacementNosetting)
{
    // Load a copy of the document in hidden mode.
    OUString aSourceURL = createFileURL(u"update-replacement-nosetting.odt");
    CPPUNIT_ASSERT_EQUAL(osl::FileBase::E_None, osl::File::copy(aSourceURL, maTempFile.GetURL()));
    loadFromURL(maTempFile.GetURL(), { comphelper::makePropertyValue(u"Hidden"_ustr, true) });

    // Update "everything" (including object replacements) and save it.
    dispatchCommand(mxComponent, u".uno:UpdateAll"_ustr, {});
    uno::Reference<frame::XStorable2> xStorable(mxComponent, uno::UNO_QUERY);
    xStorable->storeSelf({});

    // Check the contents of the updated copy.
    uno::Reference<uno::XComponentContext> xContext = comphelper::getProcessComponentContext();
    uno::Reference<packages::zip::XZipFileAccess2> xNameAccess
        = packages::zip::ZipFileAccess::createWithURL(xContext, maTempFile.GetURL());

    // Without the accompanying fix in place, this test would have failed, because the embedded
    // object replacement image was not generated.
    CPPUNIT_ASSERT(xNameAccess->hasByName(u"ObjectReplacements/Components"_ustr));
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testKeepRatio)
{
    // Given a document with a custom KeepRatio:
    createSwDoc("keep-ratio.fodt");

    // Then make sure we read the custom value:
    SwWrtShell* pWrtShell = getSwDocShell()->GetWrtShell();
    const SwViewOption* pViewOption = pWrtShell->GetViewOptions();
    comphelper::ScopeGuard g([pWrtShell, pViewOption] {
        SwViewOption aViewOption(*pViewOption);
        aViewOption.SetKeepRatio(false);
        SwModule::get()->ApplyUsrPref(aViewOption, &pWrtShell->GetView());
    });
    // Without the accompanying fix in place, this test would have failed, because KeepRatio was not
    // mapped to settings.xml
    CPPUNIT_ASSERT(pViewOption->IsKeepRatio());

    // Then export as well:
    save(TestFilter::ODT);
    xmlDocUniquePtr pXmlDoc = parseExport(u"settings.xml"_ustr);
    assertXPathContent(pXmlDoc, "//config:config-item[@config:name='KeepRatio']", u"true");
}

namespace
{
/// Interception implementation that disables .uno:Zoom on Image1, but not on Image2.
struct ImageInterceptor : public cppu::WeakImplHelper<frame::XDispatchProviderInterceptor>
{
    uno::Reference<view::XSelectionSupplier> m_xSelectionSupplier;
    uno::Reference<frame::XDispatchProvider> m_xMaster;
    uno::Reference<frame::XDispatchProvider> m_xSlave;
    int m_nEnabled = 0;
    int m_nDisabled = 0;

public:
    ImageInterceptor(const uno::Reference<lang::XComponent>& xComponent);

    // XDispatchProviderInterceptor
    uno::Reference<frame::XDispatchProvider> SAL_CALL getMasterDispatchProvider() override;
    uno::Reference<frame::XDispatchProvider> SAL_CALL getSlaveDispatchProvider() override;
    void SAL_CALL setMasterDispatchProvider(
        const uno::Reference<frame::XDispatchProvider>& xNewSupplier) override;
    void SAL_CALL
    setSlaveDispatchProvider(const uno::Reference<frame::XDispatchProvider>& xNewSupplier) override;

    // XDispatchProvider
    uno::Reference<frame::XDispatch> SAL_CALL queryDispatch(const util::URL& rURL,
                                                            const OUString& rTargetFrameName,
                                                            sal_Int32 SearchFlags) override;
    uno::Sequence<uno::Reference<frame::XDispatch>> SAL_CALL
    queryDispatches(const uno::Sequence<frame::DispatchDescriptor>& rRequests) override;
};
}

ImageInterceptor::ImageInterceptor(const uno::Reference<lang::XComponent>& xComponent)
{
    uno::Reference<frame::XModel2> xModel(xComponent, uno::UNO_QUERY);
    CPPUNIT_ASSERT(xModel.is());
    m_xSelectionSupplier.set(xModel->getCurrentController(), uno::UNO_QUERY);
    CPPUNIT_ASSERT(m_xSelectionSupplier.is());
}

uno::Reference<frame::XDispatchProvider> ImageInterceptor::getMasterDispatchProvider()
{
    return m_xMaster;
}

uno::Reference<frame::XDispatchProvider> ImageInterceptor::getSlaveDispatchProvider()
{
    return m_xSlave;
}

void ImageInterceptor::setMasterDispatchProvider(
    const uno::Reference<frame::XDispatchProvider>& xNewSupplier)
{
    m_xMaster = xNewSupplier;
}

void ImageInterceptor::setSlaveDispatchProvider(
    const uno::Reference<frame::XDispatchProvider>& xNewSupplier)
{
    m_xSlave = xNewSupplier;
}

uno::Reference<frame::XDispatch> ImageInterceptor::queryDispatch(const util::URL& rURL,
                                                                 const OUString& rTargetFrameName,
                                                                 sal_Int32 nSearchFlags)
{
    // Disable the UNO command based on the currently selected image, i.e. this can't be cached when
    // a different image is selected. Originally this was .uno:SetBorderStyle, but let's pick a
    // command which is active when running cppunit tests:
    if (rURL.Complete == ".uno:Zoom")
    {
        uno::Reference<container::XNamed> xImage;
        m_xSelectionSupplier->getSelection() >>= xImage;
        if (xImage.is() && xImage->getName() == "Image1")
        {
            ++m_nDisabled;
            return {};
        }

        ++m_nEnabled;
    }

    return m_xSlave->queryDispatch(rURL, rTargetFrameName, nSearchFlags);
}

uno::Sequence<uno::Reference<frame::XDispatch>>
ImageInterceptor::queryDispatches(const uno::Sequence<frame::DispatchDescriptor>& /*rRequests*/)
{
    return {};
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testSwitchBetweenImages)
{
    // Given a document with 2 images, and an interceptor catching an UNO command that specific to
    // the current selection:
    createSwDoc();
    SwWrtShell* pWrtShell = getSwDocShell()->GetWrtShell();
    uno::Reference<lang::XMultiServiceFactory> xMSF(mxComponent, uno::UNO_QUERY);
    uno::Reference<text::XTextDocument> xTextDocument(mxComponent, uno::UNO_QUERY);
    uno::Reference<text::XText> xText = xTextDocument->getText();
    uno::Reference<text::XTextCursor> xCursor = xText->createTextCursor();
    for (int i = 0; i < 2; ++i)
    {
        uno::Reference<beans::XPropertySet> xTextGraphic(
            xMSF->createInstance(u"com.sun.star.text.TextGraphicObject"_ustr), uno::UNO_QUERY);
        xTextGraphic->setPropertyValue(u"AnchorType"_ustr,
                                       uno::Any(text::TextContentAnchorType_AS_CHARACTER));
        xTextGraphic->setPropertyValue(u"Size"_ustr, uno::Any(awt::Size(5000, 5000)));
        uno::Reference<text::XTextContent> xTextContent(xTextGraphic, uno::UNO_QUERY);
        xText->insertTextContent(xCursor, xTextContent, false);
    }
    pWrtShell->SttEndDoc(/*bStt=*/false);
    uno::Reference<frame::XModel> xModel(mxComponent, uno::UNO_QUERY);
    uno::Reference<frame::XDispatchProviderInterception> xRegistration(
        xModel->getCurrentController()->getFrame(), uno::UNO_QUERY);
    rtl::Reference pInterceptor(new ImageInterceptor(mxComponent));

    xRegistration->registerDispatchProviderInterceptor(pInterceptor);
    pInterceptor->m_nEnabled = 0;
    pInterceptor->m_nDisabled = 0;

    // When selecting the first image:
    selectShape(1);

    // Then make sure the UNO command is disabled:
    CPPUNIT_ASSERT_EQUAL(0, pInterceptor->m_nEnabled);
    CPPUNIT_ASSERT_GREATEREQUAL(1, pInterceptor->m_nDisabled);

    // Given a clean state:
    pInterceptor->m_nEnabled = 0;
    pInterceptor->m_nDisabled = 0;

    // When selecting the second image:
    selectShape(2);

    // Then make sure the UNO command is enabled:
    CPPUNIT_ASSERT_GREATEREQUAL(1, pInterceptor->m_nEnabled);
    CPPUNIT_ASSERT_EQUAL(0, pInterceptor->m_nDisabled);

    // Given a clean state:
    pInterceptor->m_nEnabled = 0;
    pInterceptor->m_nDisabled = 0;

    // When selecting the first image, again (this time not changing the selection type):
    selectShape(1);

    // Then make sure the UNO command is disabled:
    CPPUNIT_ASSERT_EQUAL(0, pInterceptor->m_nEnabled);
    // Without the accompanying fix in place, this test would have failed with:
    // - Expected greater or equal than: 1
    // - Actual  : 0
    // i.e. selecting the first image didn't result in a disabled UNO command.
    CPPUNIT_ASSERT_GREATEREQUAL(1, pInterceptor->m_nDisabled);
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testPrintPreview)
{
    // Given a normal Writer view, in half-destroyed state, similar to what
    // SfxViewFrame::SwitchToViewShell_Impl() does in practice:
    createSwDoc();
    SwDocShell* pDocShell = getSwDocShell();
    SwView* pView = pDocShell->GetView();
    FmFormShell* pFormShell = pView->GetFormShell();
    pView->SetFormShell(reinterpret_cast<FmFormShell*>(-1));
    pView->SetDying();

    // When selecting a shell, similar to what happens the doc size changes:
    // Then make sure we don't crash:
    pView->SelectShell();

    // Restore the state and shut down.
    pView->SetFormShell(pFormShell);
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, TestTdf152839_Formtext)
{
    createSwDoc("tdf152839_formtext.rtf");

    xmlDocUniquePtr pXmlDoc = parseLayoutDump();
    sal_Int32 nHeight
        = getXPath(pXmlDoc, "/root/page[1]/body/tab[1]/row[2]/cell[1]/txt/infos/bounds", "height")
              .toInt32();
    CPPUNIT_ASSERT_EQUAL(sal_Int32(723), nHeight);
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testEditInReadonly)
{
    createSwDoc("editinsection.odt");

    SwDocShell* pDocShell = getSwDocShell();
    SwView* pView = pDocShell->GetView();

    pView->GetViewFrame().GetDispatcher()->Execute(SID_EDITDOC, SfxCallMode::SYNCHRON);

    uno::Reference<frame::XModel> xModel(mxComponent, uno::UNO_QUERY);
    uno::Reference<text::XTextDocument> xTextDocument(mxComponent, uno::UNO_QUERY);
    uno::Reference<text::XParagraphCursor> xParaCursor(xTextDocument->getText()->createTextCursor(),
                                                       uno::UNO_QUERY);

    uno::Reference<view::XSelectionSupplier> xSelSupplier(xModel->getCurrentController(),
                                                          uno::UNO_QUERY_THROW);

    xSelSupplier->select(css::uno::Any(xParaCursor));
    std::unique_ptr<SfxPoolItem> pItem;
    SfxItemState eState = pView->GetViewFrame().GetBindings().QueryState(FN_INSERT_TABLE, pItem);
    //status disabled in read only content
    CPPUNIT_ASSERT_EQUAL(SfxItemState::DISABLED, eState);

    //move cursor to section
    xParaCursor->gotoNextParagraph(false);
    xSelSupplier->select(css::uno::Any(xParaCursor));
    eState = pView->GetViewFrame().GetBindings().QueryState(FN_INSERT_TABLE, pItem);
    //status default in editable section
    CPPUNIT_ASSERT_EQUAL(SfxItemState::DEFAULT, eState);
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testShowTextobjectbarInReadonly)
{
    createSwDoc("tdf146549.odt");

    SwDocShell* pDocShell = getSwDocShell();
    SwView* pView = pDocShell->GetView();

    pView->GetViewFrame().GetDispatcher()->Execute(SID_EDITDOC, SfxCallMode::SYNCHRON);

    uno::Reference<frame::XModel> xModel(mxComponent, uno::UNO_QUERY);
    uno::Reference<text::XTextDocument> xTextDocument(mxComponent, uno::UNO_QUERY);
    uno::Reference<text::XParagraphCursor> xParaCursor(xTextDocument->getText()->createTextCursor(),
                                                       uno::UNO_QUERY);

    uno::Reference<view::XSelectionSupplier> xSelSupplier(xModel->getCurrentController(),
                                                          uno::UNO_QUERY_THROW);

    SwWrtShell* pWrtShell = getSwDocShell()->GetWrtShell();
    CPPUNIT_ASSERT(pWrtShell);

    SfxViewFrame& rViewFrame = pWrtShell->GetView().GetViewFrame();
    uno::Reference<com::sun::star::frame::XLayoutManager> xLayoutManager;
    uno::Reference<beans::XPropertySet> xPropSet(rViewFrame.GetFrame().GetFrameInterface(),
                                                 uno::UNO_QUERY);
    xLayoutManager.set(xPropSet->getPropertyValue(u"LayoutManager"_ustr), uno::UNO_QUERY);

    // move the cursor to the non-editable section
    xSelSupplier->select(css::uno::Any(xParaCursor));

    bool bShow;
    bShow = xLayoutManager->isElementVisible(u"private:resource/toolbar/drawtextobjectbar"_ustr);
    CPPUNIT_ASSERT_EQUAL(false, bShow); // the formatting toolbar should be hidden

    // move the cursor to the editable section
    xParaCursor->gotoNextParagraph(false);
    xSelSupplier->select(css::uno::Any(xParaCursor));

    bShow = xLayoutManager->isElementVisible(u"private:resource/toolbar/drawtextobjectbar"_ustr);
    CPPUNIT_ASSERT_EQUAL(true, bShow); // the formatting toolbar should be shown

    // move the cursor to the non-editable section
    xParaCursor->gotoPreviousParagraph(false);
    xSelSupplier->select(css::uno::Any(xParaCursor));

    bShow = xLayoutManager->isElementVisible(u"private:resource/toolbar/drawtextobjectbar"_ustr);
    CPPUNIT_ASSERT_EQUAL(false, bShow); // the formatting toolbar should be hidden
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testReinstateTrackedChangeState)
{
    // Given a document with a deletion:
    createSwDoc();
    SwWrtShell* pWrtShell = getSwDocShell()->GetWrtShell();
    pWrtShell->Insert("abcd");
    RedlineFlags nMode = pWrtShell->GetRedlineFlags();
    pWrtShell->SetRedlineFlags(nMode | RedlineFlags::On);
    pWrtShell->Left(SwCursorSkipMode::Chars, /*bSelect=*/false, 1, /*bBasicCall=*/false);
    pWrtShell->Left(SwCursorSkipMode::Chars, /*bSelect=*/true, 2, /*bBasicCall=*/false);
    pWrtShell->DelRight();

    // When the cursor is inside a redline:
    pWrtShell->SttPara(/*bSelect=*/false);
    pWrtShell->Right(SwCursorSkipMode::Chars, /*bSelect=*/false, 2, /*bBasicCall=*/false);

    // Then make sure that reinstate is enabled:
    SwView* pView = getSwDocShell()->GetView();
    std::unique_ptr<SfxPoolItem> pItem;
    SfxItemState eState
        = pView->GetViewFrame().GetBindings().QueryState(FN_REDLINE_REINSTATE_DIRECT, pItem);
    CPPUNIT_ASSERT_EQUAL(SfxItemState::DEFAULT, eState);

    // When the cursor is outside a redline:
    pWrtShell->SttPara(/*bSelect=*/false);

    // Then make sure that reinstate is disabled:
    eState = pView->GetViewFrame().GetBindings().QueryState(FN_REDLINE_REINSTATE_DIRECT, pItem);
    // Without the accompanying fix in place, this test would have failed with:
    // - Expected: 1 (DISABLED)
    // - Actual  : 32 (DEFAULT)
    // i.e. reinstate was always enabled.
    CPPUNIT_ASSERT_EQUAL(SfxItemState::DISABLED, eState);
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testRedlineRenderModeCommand)
{
    // Given a document with default view options:
    createSwDoc();
    SwWrtShell* pWrtShell = getSwDocShell()->GetWrtShell();
    SwRedlineRenderMode eActual = pWrtShell->GetViewOptions()->GetRedlineRenderMode();
    CPPUNIT_ASSERT_EQUAL(SwRedlineRenderMode::Standard, eActual);

    // When toggling redline render mode to omit deletes:
    dispatchCommand(mxComponent, u".uno:RedlineRenderMode"_ustr, {});

    // Then make sure the view option is updated:
    eActual = pWrtShell->GetViewOptions()->GetRedlineRenderMode();
    // Without the accompanying fix in place, this test would have failed with:
    // - Expected: 2 (OmitDeletes)
    // - Actual  : 0 (Standard)
    // i.e. the view option wasn't set.
    CPPUNIT_ASSERT_EQUAL(SwRedlineRenderMode::OmitDeletes, eActual);

    // And when toggling off:
    dispatchCommand(mxComponent, u".uno:RedlineRenderMode"_ustr, {});

    // Then make sure the view option is back to its default:
    eActual = pWrtShell->GetViewOptions()->GetRedlineRenderMode();
    CPPUNIT_ASSERT_EQUAL(SwRedlineRenderMode::Standard, eActual);
}

namespace
{
/// LOK view callback for test purposes.
struct ViewCallback
{
    std::set<SwRedlineRenderMode> m_aInvalidationModes;

    static void callback(int nType, const char* pPayload, void* pData);
    void callbackImpl(int nType, const char* pPayload);
};

void ViewCallback::callback(int nType, const char* pPayload, void* pData)
{
    static_cast<ViewCallback*>(pData)->callbackImpl(nType, pPayload);
}

void ViewCallback::callbackImpl(int nType, const char* pPayload)
{
    switch (nType)
    {
        case LOK_CALLBACK_INVALIDATE_TILES:
        {
            OUString aPayload = OUString::fromUtf8(pPayload);
            if (aPayload.startsWith("EMPTY"))
            {
                break;
            }
            uno::Sequence<OUString> aSeq = comphelper::string::convertCommaSeparated(aPayload);
            // x y w h part mode
            CPPUNIT_ASSERT_EQUAL(static_cast<sal_Int32>(6), aSeq.getLength());
            m_aInvalidationModes.insert(static_cast<SwRedlineRenderMode>(aSeq[5].toInt32()));
        }
        break;
    }
}
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testRedlineRenderModeInvalidate)
{
    // Set up LOK:
    comphelper::LibreOfficeKit::setActive(true);
    comphelper::LibreOfficeKit::setPartInInvalidation(true);

    // Given a document where redline render mode is set to "omit deletes":
    createSwDoc();
    getSwTextDoc()->initializeForTiledRendering({});
    SwDocShell* pDocShell = getSwDocShell();
    SwWrtShell* pWrtShell = pDocShell->GetWrtShell();
    ViewCallback aCallback;
    TestLokCallbackWrapper aCallbackWrapper(&ViewCallback::callback, &aCallback);
    pWrtShell->GetSfxViewShell()->setLibreOfficeKitViewCallback(&aCallbackWrapper);
    aCallbackWrapper.setLOKViewId(SfxLokHelper::getView(*pWrtShell->GetSfxViewShell()));
    SwViewOption aOpt(*pWrtShell->GetViewOptions());
    aOpt.SetRedlineRenderMode(SwRedlineRenderMode::OmitDeletes);
    pWrtShell->ApplyViewOptions(aOpt);
    Scheduler::ProcessEventsToIdle();
    aCallback.m_aInvalidationModes.clear();

    // When typing a key:
    pWrtShell->Insert(u"x"_ustr);
    pWrtShell->GetSfxViewShell()->flushPendingLOKInvalidateTiles();

    // Then make sure that both the "omit inserts" and the "omit deletes" modes are invalidated:
    // Without the accompanying fix in place, this test would have failed, only the "omit deletes"
    // mode was invalidated.
    CPPUNIT_ASSERT(aCallback.m_aInvalidationModes.contains(SwRedlineRenderMode::OmitInserts));
    CPPUNIT_ASSERT(aCallback.m_aInvalidationModes.contains(SwRedlineRenderMode::OmitDeletes));

    // Tear down LOK:
    pWrtShell->GetSfxViewShell()->setLibreOfficeKitViewCallback(nullptr);
    comphelper::LibreOfficeKit::setPartInInvalidation(false);
}

namespace
{
/// Finds the combo box of the "Apply Style" (.uno:StyleApply) toolbar item below pWindow.
vcl::Window* findApplyStyleBox(vcl::Window* pWindow)
{
    if (auto pToolBox = dynamic_cast<ToolBox*>(pWindow))
    {
        for (ToolBox::ImplToolItems::size_type i = 0; i < pToolBox->GetItemCount(); ++i)
        {
            const ToolBoxItemId nId = pToolBox->GetItemId(i);
            if (pToolBox->GetItemCommand(nId) != ".uno:StyleApply")
                continue;
            // The item window is an InterimItemWindow that holds the combo box.
            std::vector<vcl::Window*> aWindows{ pToolBox->GetItemWindow(nId) };
            while (!aWindows.empty())
            {
                vcl::Window* pChild = aWindows.back();
                aWindows.pop_back();
                if (!pChild)
                    continue;
                if (pChild->GetType() == WindowType::COMBOBOX)
                    return pChild;
                for (sal_uInt16 j = 0; j < pChild->GetChildCount(); ++j)
                    aWindows.push_back(pChild->GetChild(j));
            }
        }
    }
    for (sal_uInt16 i = 0; i < pWindow->GetChildCount(); ++i)
        if (vcl::Window* pFound = findApplyStyleBox(pWindow->GetChild(i)))
            return pFound;
    return nullptr;
}

/// Sends the pending status updates to the toolbar controllers now: they are sent from a timer,
/// and Scheduler::ProcessEventsToIdle() does not wait for timers.
void updateStatus(SwWrtShell& rWrtShell)
{
    Scheduler::ProcessEventsToIdle();
    rWrtShell.GetView().GetViewFrame().GetBindings().Update();
    Scheduler::ProcessEventsToIdle();
}

vcl::Window* getApplyStyleBox(SwWrtShell& rWrtShell)
{
    updateStatus(rWrtShell);
    vcl::Window* pBox
        = findApplyStyleBox(rWrtShell.GetView().GetViewFrame().GetWindow().GetSystemWindow());
    CPPUNIT_ASSERT_MESSAGE("no Apply Style box in the formatting toolbar", pBox);
    return pBox;
}

/// The entries of the box, one per line, as its accessible list exposes them.
OUString getEntries(vcl::Window& rBox)
{
    OUStringBuffer aEntries;
    uno::Reference<accessibility::XAccessibleContext> xBox
        = rBox.GetAccessible()->getAccessibleContext();
    for (sal_Int64 i = 0; i < xBox->getAccessibleChildCount(); ++i)
    {
        uno::Reference<accessibility::XAccessibleContext> xList
            = xBox->getAccessibleChild(i)->getAccessibleContext();
        if (xList->getAccessibleRole() != accessibility::AccessibleRole::LIST)
            continue;
        for (sal_Int64 j = 0; j < xList->getAccessibleChildCount(); ++j)
            aEntries.append(
                xList->getAccessibleChild(j)->getAccessibleContext()->getAccessibleName() + "\n");
    }
    return aEntries.makeStringAndClear();
}

sal_Int32 getEntryCount(vcl::Window& rBox)
{
    const OUString aEntries = getEntries(rBox);
    return std::count(aEntries.getStr(), aEntries.getStr() + aEntries.getLength(), u'\n');
}

/// The list of SvxStyleToolBoxControl::FillStyleBox() for paragraph styles: "Clear formatting",
/// the default styles, then the used, favourite and user-defined styles not listed yet, then
/// "More Styles...".
OUString getExpectedParaStyleList(SwDocShell& rDocShell)
{
    OUStringBuffer aEntries(u"Clear formatting\n"_ustr);
    std::unordered_set<OUString> aListed;
    for (const OUString& rDefault :
         { u"Default Paragraph Style"_ustr, u"Body Text"_ustr, u"Title"_ustr, u"Subtitle"_ustr,
           u"Heading 1"_ustr, u"Heading 2"_ustr, u"Heading 3"_ustr, u"Heading 4"_ustr,
           u"Block Quotation"_ustr, u"Preformatted Text"_ustr })
    {
        aEntries.append(rDefault + "\n");
        aListed.insert(rDefault);
    }
    SfxStyleSheetBasePool* pPool = rDocShell.GetStyleSheetPool();
    for (SfxStyleSearchBits eBits : { SfxStyleSearchBits::Used, SfxStyleSearchBits::Favourite,
                                      SfxStyleSearchBits::UserDefined })
    {
        auto xIter = pPool->CreateIterator(SfxStyleFamily::Para, eBits);
        for (SfxStyleSheetBase* pStyle = xIter->First(); pStyle; pStyle = xIter->Next())
            if (aListed.insert(pStyle->GetName()).second)
                aEntries.append(pStyle->GetName() + "\n");
    }
    aEntries.append("More Styles...\n");
    return aEntries.makeStringAndClear();
}

uno::Sequence<beans::PropertyValue> paraStyleArgs(const OUString& rName)
{
    return { comphelper::makePropertyValue(u"Param"_ustr, rName),
             comphelper::makePropertyValue(u"Family"_ustr,
                                           static_cast<sal_Int16>(SfxStyleFamily::Para)) };
}
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testApplyStyleBoxNotFilledWhenNotEngaged)
{
    createSwDoc();
    SwWrtShell* pWrtShell = getSwDocShell()->GetWrtShell();
    pWrtShell->Insert(u"one"_ustr);
    pWrtShell->SplitNode();
    pWrtShell->Insert(u"two"_ustr);
    pWrtShell->SplitNode();
    pWrtShell->Insert(u"three"_ustr);
    pWrtShell->SttEndDoc(/*bStt=*/true);
    dispatchCommand(
        mxComponent,
        u".uno:StyleApply?Style:string=Heading%201&FamilyName:string=ParagraphStyles"_ustr, {});
    pWrtShell->Down(/*bSelect=*/false);
    dispatchCommand(
        mxComponent,
        u".uno:StyleApply?Style:string=Heading%202&FamilyName:string=ParagraphStyles"_ustr, {});
    pWrtShell->SttEndDoc(/*bStt=*/true);

    vcl::Window* pBox = getApplyStyleBox(*pWrtShell);
    CPPUNIT_ASSERT(!pBox->HasChildPathFocus());

    // Moving between paragraphs with different styles updates the box. While the box is neither
    // focused nor open, it shows the current style but does not hold the whole list: refilling it
    // on every cursor move is slow with many styles.
    // Without the fix in place, this test would have failed with
    // - Expected less or equal than: 1
    // - Actual  : 13
    for (const OUString& rStyle :
         { u"Heading 1"_ustr, u"Heading 2"_ustr, u"Default Paragraph Style"_ustr })
    {
        updateStatus(*pWrtShell);
        CPPUNIT_ASSERT_EQUAL(rStyle, pBox->GetText());
        CPPUNIT_ASSERT_LESSEQUAL(sal_Int32(1), getEntryCount(*pBox));
        pWrtShell->Down(/*bSelect=*/false);
    }

    // Focusing the box fills the list; once the user is back in the document, the next update
    // drops it again.
    pBox->GrabFocus();
    updateStatus(*pWrtShell);
    CPPUNIT_ASSERT_EQUAL(getExpectedParaStyleList(*getSwDocShell()), getEntries(*pBox));
    pWrtShell->GetView().GetWindow()->GrabFocus();
    pWrtShell->SttEndDoc(/*bStt=*/true);
    updateStatus(*pWrtShell);
    CPPUNIT_ASSERT(!pBox->HasChildPathFocus());
    CPPUNIT_ASSERT_EQUAL(u"Heading 1"_ustr, pBox->GetText());
    CPPUNIT_ASSERT_LESSEQUAL(sal_Int32(1), getEntryCount(*pBox));
}

CPPUNIT_TEST_FIXTURE(SwUibaseUiviewTest, testApplyStyleBoxListWhileEngaged)
{
    createSwDoc();
    SwDocShell* pDocShell = getSwDocShell();
    SwWrtShell* pWrtShell = pDocShell->GetWrtShell();
    vcl::Window* pBox = getApplyStyleBox(*pWrtShell);

    // Engage the box: while it has the focus, it lists every style as it always did.
    pBox->GrabFocus();
    Scheduler::ProcessEventsToIdle();
    CPPUNIT_ASSERT(pBox->HasChildPathFocus());

    // The list equals the one built from the style pool, and rName is listed or not.
    auto checkList = [&](const char* pStep, const OUString& rName, std::optional<bool> oListed)
    {
        updateStatus(*pWrtShell);
        CPPUNIT_ASSERT_MESSAGE(pStep, pBox->HasChildPathFocus());
        const OUString aEntries = getEntries(*pBox);
        CPPUNIT_ASSERT_EQUAL_MESSAGE(pStep, getExpectedParaStyleList(*pDocShell), aEntries);
        if (oListed)
            CPPUNIT_ASSERT_EQUAL_MESSAGE(pStep, *oListed,
                                         aEntries.indexOf(OUString("\n" + rName + "\n")) != -1);
    };
    checkList("initial", u"Heading 5"_ustr, false);

    dispatchCommand(mxComponent, u".uno:StyleNewByExample"_ustr,
                    paraStyleArgs(u"Boost Paragraph"_ustr));
    checkList("create", u"Boost Paragraph"_ustr, true);
    dispatchCommand(mxComponent, u".uno:Undo"_ustr, {});
    // Undo may take back only the use of the new style, not the style itself.
    checkList("undo create", u"Boost Paragraph"_ustr, {});
    dispatchCommand(mxComponent, u".uno:Redo"_ustr, {});
    checkList("redo create", u"Boost Paragraph"_ustr, true);

    uno::Reference<style::XStyleFamiliesSupplier> xSupplier(mxComponent, uno::UNO_QUERY_THROW);
    uno::Reference<container::XNameAccess> xParaStyles(
        xSupplier->getStyleFamilies()->getByName(u"ParagraphStyles"_ustr), uno::UNO_QUERY_THROW);
    uno::Reference<container::XNamed> xStyle(xParaStyles->getByName(u"Boost Paragraph"_ustr),
                                             uno::UNO_QUERY_THROW);
    xStyle->setName(u"Boost Renamed"_ustr);
    checkList("rename", u"Boost Renamed"_ustr, true);
    checkList("rename", u"Boost Paragraph"_ustr, false);
    dispatchCommand(mxComponent, u".uno:Undo"_ustr, {});
    checkList("undo rename", u"Boost Paragraph"_ustr, {});
    dispatchCommand(mxComponent, u".uno:Redo"_ustr, {});
    checkList("redo rename", u"Boost Renamed"_ustr, {});

    // The box lists hidden styles too (SfxStyleSheetIterator does not filter them).
    SfxStyleSheetBasePool* pPool = pDocShell->GetStyleSheetPool();
    dispatchCommand(mxComponent, u".uno:HideStyle"_ustr, paraStyleArgs(u"Boost Renamed"_ustr));
    CPPUNIT_ASSERT(pPool->Find(u"Boost Renamed"_ustr, SfxStyleFamily::Para)->IsHidden());
    checkList("hide", u"Boost Renamed"_ustr, {});
    dispatchCommand(mxComponent, u".uno:Undo"_ustr, {});
    checkList("undo hide", u"Boost Renamed"_ustr, {});
    dispatchCommand(mxComponent, u".uno:Redo"_ustr, {});
    checkList("redo hide", u"Boost Renamed"_ustr, {});

    dispatchCommand(mxComponent, u".uno:DeleteStyle"_ustr, paraStyleArgs(u"Boost Renamed"_ustr));
    CPPUNIT_ASSERT(!xParaStyles->hasByName(u"Boost Renamed"_ustr));
    checkList("delete", u"Boost Renamed"_ustr, false);
    dispatchCommand(mxComponent, u".uno:Undo"_ustr, {});
    CPPUNIT_ASSERT(xParaStyles->hasByName(u"Boost Renamed"_ustr));
    checkList("undo delete", u"Boost Renamed"_ustr, true);
    dispatchCommand(mxComponent, u".uno:Redo"_ustr, {});
    checkList("redo delete", u"Boost Renamed"_ustr, false);

    // "Heading 5" is not a default style: it is listed only while a paragraph uses it.
    dispatchCommand(
        mxComponent,
        u".uno:StyleApply?Style:string=Heading%205&FamilyName:string=ParagraphStyles"_ustr, {});
    checkList("apply", u"Heading 5"_ustr, true);
    dispatchCommand(mxComponent,
                    u".uno:StyleApply?Style:string=Standard&FamilyName:string=ParagraphStyles"_ustr,
                    {});
    checkList("remove", u"Heading 5"_ustr, false);
    dispatchCommand(mxComponent, u".uno:Undo"_ustr, {});
    checkList("undo remove", u"Heading 5"_ustr, true);
    dispatchCommand(mxComponent, u".uno:Redo"_ustr, {});
    checkList("redo remove", u"Heading 5"_ustr, false);
}

CPPUNIT_PLUGIN_IMPLEMENT();

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
