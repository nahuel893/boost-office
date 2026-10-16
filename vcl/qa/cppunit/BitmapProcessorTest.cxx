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

#include <algorithm>
#include <cmath>
#include <sstream>
#include <string>
#include <vector>

#include <bitmap/BitmapDisabledImageFilter.hxx>
#include <vcl/BitmapWriteAccess.hxx>

namespace
{
class BitmapProcessorTest : public CppUnit::TestFixture
{
    void testDisabledImage();
    void testDisabledImageOnDarkFace();
    void testDisabledImageOnBlackFace();
    void testDisabledImageOnVeryDarkFace();
    void testDisabledImageOnLightFace();
    void testDisabledImageOnDarkFaceKeepsAlpha();
    void testDisabledImageFollowsTheFaceColor();

    CPPUNIT_TEST_SUITE(BitmapProcessorTest);
    CPPUNIT_TEST(testDisabledImage);
    CPPUNIT_TEST(testDisabledImageOnDarkFace);
    CPPUNIT_TEST(testDisabledImageOnBlackFace);
    CPPUNIT_TEST(testDisabledImageOnVeryDarkFace);
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

// WCAG 2.1 contrast ratio of two colors.
double lcl_contrast(const Color& rA, const Color& rB)
{
    auto toLinear = [](sal_uInt8 nValue) {
        const double f = nValue / 255.0;
        return f <= 0.04045 ? f / 12.92 : std::pow((f + 0.055) / 1.055, 2.4);
    };
    auto relativeLuminance = [&toLinear](const Color& rColor) {
        return 0.2126 * toLinear(rColor.GetRed()) + 0.7152 * toLinear(rColor.GetGreen())
               + 0.0722 * toLinear(rColor.GetBlue());
    };
    const double fA = relativeLuminance(rA) + 0.05;
    const double fB = relativeLuminance(rB) + 0.05;
    return std::max(fA, fB) / std::min(fA, fB);
}

// On a dark face, a disabled pixel of luminance L is a grey at contrast 1 + L / 255 against the
// face (the face itself for black, 2:1 for white), whatever the dark face is, down to black.
void lcl_checkDarkFace(const Color& rFace)
{
    Bitmap aDisabled(BitmapDisabledImageFilter(rFace).execute(lcl_makeRow(aTestColors)));
    BitmapScopedReadAccess pReadAccess(aDisabled);
    for (size_t i = 0; i < aTestColors.size(); ++i)
    {
        const Color aColor(pReadAccess->GetPixel(0, i));
        std::ostringstream aMessage;
        aMessage << "face " << rFace << ", pixel " << aTestColors[i] << " -> " << aColor;
        CPPUNIT_ASSERT_EQUAL_MESSAGE(aMessage.str(), int(aColor.GetRed()), int(aColor.GetGreen()));
        CPPUNIT_ASSERT_EQUAL_MESSAGE(aMessage.str(), int(aColor.GetRed()), int(aColor.GetBlue()));
        CPPUNIT_ASSERT_DOUBLES_EQUAL_MESSAGE(aMessage.str(),
                                             1.0 + aTestColors[i].GetLuminance() / 255.0,
                                             lcl_contrast(aColor, rFace), 0.02);
    }
}

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
    lcl_checkDarkFace(Color(0x2B, 0x2B, 0x2B));
    lcl_checkDarkFace(Color(0x45, 0x45, 0x45));
    Bitmap aDisabled(
        BitmapDisabledImageFilter(Color(0x2B, 0x2B, 0x2B)).execute(lcl_makeRow(aTestColors)));
    BitmapScopedReadAccess pReadAccess(aDisabled);
    CPPUNIT_ASSERT_EQUAL(Color(0x2B, 0x2B, 0x2B), Color(pReadAccess->GetPixel(0, 0))); // black
    CPPUNIT_ASSERT_EQUAL(Color(88, 88, 88), Color(pReadAccess->GetPixel(0, 1))); // white, 2:1
}

void BitmapProcessorTest::testDisabledImageOnBlackFace()
{
    // A black face (e.g. high contrast black): the band must not shrink to near invisible.
    lcl_checkDarkFace(COL_BLACK);
}

void BitmapProcessorTest::testDisabledImageOnVeryDarkFace()
{
    // #1A1A1A: the first, fixed sRGB band was already dimmer here than on #2B2B2B.
    lcl_checkDarkFace(Color(0x1A, 0x1A, 0x1A));
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
    const Color aColor(pReadAccess->GetPixel(0, 0));
    CPPUNIT_ASSERT_EQUAL(sal_uInt8(0xAA), aColor.GetAlpha());
    // 88 (2:1 against the face), give or take the rounding of the premultiplied alpha storage
    CPPUNIT_ASSERT_DOUBLES_EQUAL(88.0, double(aColor.GetRed()), 1.0);
    CPPUNIT_ASSERT_EQUAL(aColor.GetRed(), aColor.GetGreen());
    CPPUNIT_ASSERT_EQUAL(aColor.GetRed(), aColor.GetBlue());
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
    const Color aDark(88, 88, 88); // contrast 2:1 against #2B2B2B
    CPPUNIT_ASSERT_EQUAL(aLight, drawDisabledOn(Color(0xE4, 0xF2, 0xE8)));
    CPPUNIT_ASSERT_EQUAL(aDark, drawDisabledOn(Color(0x2B, 0x2B, 0x2B)));
    CPPUNIT_ASSERT_EQUAL(aLight, drawDisabledOn(Color(0xE4, 0xF2, 0xE8)));
}

} // namespace

CPPUNIT_TEST_SUITE_REGISTRATION(BitmapProcessorTest);

CPPUNIT_PLUGIN_IMPLEMENT();

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
