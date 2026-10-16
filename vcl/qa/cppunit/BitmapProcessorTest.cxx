/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#include <cppunit/TestAssert.h>
#include <cppunit/TestFixture.h>
#include <cppunit/extensions/HelperMacros.h>
#include <cppunit/plugin/TestPlugIn.h>

#include <vcl/bitmap.hxx>
#include <vcl/alpha.hxx>
#include <vcl/image.hxx>
#include <vcl/rendercontext/DrawImageFlags.hxx>
#include <vcl/settings.hxx>
#include <vcl/virdev.hxx>

#include <bitmap/BitmapDisabledImageFilter.hxx>
#include <vcl/BitmapWriteAccess.hxx>

namespace
{
class BitmapProcessorTest : public CppUnit::TestFixture
{
    void testDisabledImage();
    void testDisabledImageOnDarkFace();
    void testDisabledImageOnLightFace();
    void testDisabledImageOnDarkFaceKeepsAlpha();
    void testDisabledImageFollowsTheFaceColor();

    CPPUNIT_TEST_SUITE(BitmapProcessorTest);
    CPPUNIT_TEST(testDisabledImage);
    CPPUNIT_TEST(testDisabledImageOnDarkFace);
    CPPUNIT_TEST(testDisabledImageOnLightFace);
    CPPUNIT_TEST(testDisabledImageOnDarkFaceKeepsAlpha);
    CPPUNIT_TEST(testDisabledImageFollowsTheFaceColor);
    CPPUNIT_TEST_SUITE_END();
};

// One pixel per test color, in a row.
Bitmap lcl_makeRow(const std::vector<Color>& rColors)
{
    Bitmap aBitmap(Size(rColors.size(), 1), vcl::PixelFormat::N24_BPP);
    BitmapScopedWriteAccess pWriteAccess(aBitmap);
    for (size_t i = 0; i < rColors.size(); ++i)
        pWriteAccess->SetPixel(0, i, BitmapColor(rColors[i]));
    return aBitmap;
}

const std::vector<Color> aTestColors{ COL_BLACK,
                                      COL_WHITE,
                                      Color(0xD6, 0xD6, 0xD6), // a dark-theme icon outline
                                      Color(0x42, 0x42, 0x42), // a light-theme icon outline
                                      Color(0x00, 0x00, 0xFF),
                                      Color(0xE0, 0x40, 0x20) };

void BitmapProcessorTest::testDisabledImage()
{
    {
        Bitmap aBitmap(Size(3, 3), vcl::PixelFormat::N24_BPP);
        {
            BitmapScopedWriteAccess pWriteAccess(aBitmap);
            pWriteAccess->Erase(Color(ColorTransparency, 0x00, 0x00, 0xFF, 0x00));
        }
        BitmapDisabledImageFilter aDisabledImageFilter;
        Bitmap aDisabledBitmap(aDisabledImageFilter.execute(aBitmap));
        {
            BitmapScopedReadAccess pReadAccess(aDisabledBitmap);
            Color aColor(pReadAccess->GetPixel(0, 0));
            CPPUNIT_ASSERT_EQUAL(Color(0x00C5C5C5), aColor);
        }
    }

    {
        Bitmap aBitmap(Size(3, 3), vcl::PixelFormat::N24_BPP);
        {
            BitmapScopedWriteAccess pWriteAccess(aBitmap);
            pWriteAccess->Erase(Color(ColorTransparency, 0x00, 0x00, 0xFF, 0x00));
        }
        AlphaMask aMask(Size(3, 3));
        {
            BitmapScopedWriteAccess pWriteAccess(aMask);
            pWriteAccess->Erase(Color(ColorTransparency, 0x00, 0xAA, 0xAA, 0xAA));
        }

        Bitmap aBitmap2(aBitmap, aMask);
        BitmapDisabledImageFilter aDisabledImageFilter;
        Bitmap aDisabledBitmap(aDisabledImageFilter.execute(aBitmap2));
        {
            BitmapScopedReadAccess pReadAccess(aDisabledBitmap);
            Color aColor(pReadAccess->GetPixel(0, 0));
            CPPUNIT_ASSERT_EQUAL(Color(ColorAlpha, 0xAA, 0xC5, 0xC5, 0xC5), aColor);
        }
    }
}

void BitmapProcessorTest::testDisabledImageOnDarkFace()
{
    // A dark face (the dark ribbon background): a disabled pixel must stay in a band just above
    // the face, not turn light grey (luminance / 4 + 160) and stand out more than enabled icons.
    const Color aFace(0x2B, 0x2B, 0x2B);
    const sal_uInt8 nFace = aFace.GetLuminance();
    Bitmap aDisabled(BitmapDisabledImageFilter(aFace).execute(lcl_makeRow(aTestColors)));
    BitmapScopedReadAccess pReadAccess(aDisabled);
    for (size_t i = 0; i < aTestColors.size(); ++i)
    {
        const Color aColor(pReadAccess->GetPixel(0, i));
        const sal_uInt8 nExpected = nFace + aTestColors[i].GetLuminance() * 3 / 16;
        CPPUNIT_ASSERT_EQUAL(Color(nExpected, nExpected, nExpected), aColor);
        CPPUNIT_ASSERT_GREATEREQUAL(int(nFace), int(aColor.GetLuminance()));
        CPPUNIT_ASSERT_LESSEQUAL(int(nFace) + 48, int(aColor.GetLuminance()));
    }
    // white: 43 + 255 * 3 / 16
    CPPUNIT_ASSERT_EQUAL(Color(90, 90, 90), Color(pReadAccess->GetPixel(0, 1)));
}

void BitmapProcessorTest::testDisabledImageOnLightFace()
{
    // A light face keeps today's light grey, byte for byte.
    const Bitmap aRow(lcl_makeRow(aTestColors));
    const Bitmap aDefault(BitmapDisabledImageFilter().execute(aRow));
    for (const Color& rFace : { COL_LIGHTGRAY, Color(0xE4, 0xF2, 0xE8), COL_WHITE })
    {
        Bitmap aDisabled(BitmapDisabledImageFilter(rFace).execute(aRow));
        CPPUNIT_ASSERT_EQUAL(aDefault.GetChecksum(), aDisabled.GetChecksum());
        BitmapScopedReadAccess pReadAccess(aDisabled);
        for (size_t i = 0; i < aTestColors.size(); ++i)
        {
            const sal_uInt8 nExpected = aTestColors[i].GetLuminance() / 4 + 160;
            CPPUNIT_ASSERT_EQUAL(Color(nExpected, nExpected, nExpected),
                                 Color(pReadAccess->GetPixel(0, i)));
        }
    }
}

void BitmapProcessorTest::testDisabledImageOnDarkFaceKeepsAlpha()
{
    Bitmap aBitmap(Size(3, 3), vcl::PixelFormat::N24_BPP);
    {
        BitmapScopedWriteAccess pWriteAccess(aBitmap);
        pWriteAccess->Erase(COL_WHITE);
    }
    AlphaMask aMask(Size(3, 3));
    {
        BitmapScopedWriteAccess pWriteAccess(aMask);
        pWriteAccess->Erase(Color(ColorTransparency, 0x00, 0xAA, 0xAA, 0xAA));
    }
    Bitmap aDisabled(
        BitmapDisabledImageFilter(Color(0x2B, 0x2B, 0x2B)).execute(Bitmap(aBitmap, aMask)));
    BitmapScopedReadAccess pReadAccess(aDisabled);
    CPPUNIT_ASSERT_EQUAL(Color(ColorAlpha, 0xAA, 90, 90, 90), Color(pReadAccess->GetPixel(0, 0)));
}

void BitmapProcessorTest::testDisabledImageFollowsTheFaceColor()
{
    // The disabled bitmap is cached in the image: after a theme switch (another face color) it
    // must be made again, for dark and back for light.
    Bitmap aBitmap(Size(4, 4), vcl::PixelFormat::N24_BPP);
    {
        BitmapScopedWriteAccess pWriteAccess(aBitmap);
        pWriteAccess->Erase(COL_WHITE);
    }
    const Image aImage(aBitmap);
    ScopedVclPtrInstance<VirtualDevice> pDev;
    pDev->SetOutputSizePixel(Size(4, 4));
    auto drawDisabledOn = [&](const Color& rFace) {
        AllSettings aSettings(pDev->GetSettings());
        StyleSettings aStyle(aSettings.GetStyleSettings());
        aStyle.SetFaceColor(rFace);
        aSettings.SetStyleSettings(aStyle);
        pDev->SetSettings(aSettings);
        pDev->DrawImage(Point(), aImage, DrawImageFlags::Disable);
        return pDev->GetPixel(Point(1, 1));
    };
    const Color aLight(223, 223, 223); // 255 / 4 + 160
    const Color aDark(90, 90, 90); // 43 + 255 * 3 / 16
    CPPUNIT_ASSERT_EQUAL(aLight, drawDisabledOn(Color(0xE4, 0xF2, 0xE8)));
    CPPUNIT_ASSERT_EQUAL(aDark, drawDisabledOn(Color(0x2B, 0x2B, 0x2B)));
    CPPUNIT_ASSERT_EQUAL(aLight, drawDisabledOn(Color(0xE4, 0xF2, 0xE8)));
}

} // namespace

CPPUNIT_TEST_SUITE_REGISTRATION(BitmapProcessorTest);

CPPUNIT_PLUGIN_IMPLEMENT();

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
