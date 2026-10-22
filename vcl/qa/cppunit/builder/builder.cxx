/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#include <test/unoapi_test.hxx>

#include <com/sun/star/frame/XFrame.hpp>
#include <com/sun/star/frame/XModel.hpp>

#include <vcl/builder.hxx>
#include <vcl/commandinfoprovider.hxx>
#include <vcl/toolbox.hxx>
#include <vcl/wrkwin.hxx>

using namespace css;

namespace
{
/// Tests for VclBuilder.
class BuilderTest : public UnoApiTest
{
public:
    BuilderTest()
        : UnoApiTest(u"/vcl/qa/cppunit/builder/data/"_ustr)
    {
    }
};

CPPUNIT_TEST_FIXTURE(BuilderTest, testToolButtonLabelWithCommand)
{
    // A builder that has a frame inserts a tool button with a command by that command, the way the
    // notebookbar does.
    loadFromURL(u"private:factory/swriter"_ustr);
    uno::Reference<frame::XModel> xModel(mxComponent, uno::UNO_QUERY_THROW);
    uno::Reference<frame::XFrame> xFrame(xModel->getCurrentController()->getFrame());
    const OUString aModule(vcl::CommandInfoProvider::GetModuleIdentifier(xFrame));

    ScopedVclPtrInstance<WorkWindow> pParent(nullptr, WB_STDWORK);
    VclBuilder aBuilder(pParent.get(), createFileURL(u""), u"toolbox.ui"_ustr, OUString(), xFrame);
    ToolBox* pToolBox = aBuilder.get<ToolBox>(u"toolbar");
    CPPUNIT_ASSERT(pToolBox);

    // A button with a command and a label shows the label.
    const OUString aLabelled(u".uno:TitlePageDialog"_ustr);
    const auto aLabelledProperties
        = vcl::CommandInfoProvider::GetCommandProperties(aLabelled, aModule);
    const ToolBoxItemId nLabelled = pToolBox->GetItemId(aLabelled);
    // Without the fix in place, this test would have failed with
    // - Expected: Cover Page
    // - Actual  : Title Page
    // i.e. the .ui label was ignored and the item showed the command's label.
    CPPUNIT_ASSERT_EQUAL(u"Cover Page"_ustr, pToolBox->GetItemText(nLabelled));
    // Its tooltip still comes from the command.
    CPPUNIT_ASSERT_EQUAL(
        vcl::CommandInfoProvider::GetTooltipForCommand(aLabelled, aLabelledProperties, xFrame),
        pToolBox->GetQuickHelpText(nLabelled));

    // A button with a command and no label shows the command's label.
    const OUString aUnlabelled(u".uno:InsertPagebreak"_ustr);
    const OUString aCommandLabel(vcl::CommandInfoProvider::GetLabelForCommand(
        vcl::CommandInfoProvider::GetCommandProperties(aUnlabelled, aModule)));
    CPPUNIT_ASSERT(!aCommandLabel.isEmpty());
    CPPUNIT_ASSERT_EQUAL(aCommandLabel, pToolBox->GetItemText(pToolBox->GetItemId(aUnlabelled)));

    // The label's mnemonic markup becomes VCL's "~", which a toolbox item drops: no "_" shows.
    CPPUNIT_ASSERT_EQUAL(u"Bookmark"_ustr,
                         pToolBox->GetItemText(pToolBox->GetItemId(u".uno:InsertBookmark"_ustr)));

    aBuilder.disposeBuilder();
}
}

CPPUNIT_PLUGIN_IMPLEMENT();

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
