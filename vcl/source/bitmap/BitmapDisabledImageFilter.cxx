/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 */

#include <vcl/BitmapWriteAccess.hxx>
#include <bitmap/BitmapDisabledImageFilter.hxx>

#include <algorithm>

Bitmap BitmapDisabledImageFilter::execute(Bitmap const& rBitmap) const
{
    const Size aSize(rBitmap.GetSizePixel());

    // A disabled image is a grey version of the image, close to the color it is drawn on.
    // On a light face: luminance 0-255 remapped to 160-224, a light grey.
    // On a dark face that light grey would stand out more than the enabled image does, so the
    // luminance is remapped to a band just above the face instead: face to face + 47. The band
    // is narrower than the light one because contrast grows faster at the dark end; this keeps
    // a disabled icon at about the same contrast against a dark face as against a light one.
    const bool bDarkFace = maFaceColor.IsDark();
    const int nFaceLum = maFaceColor.GetLuminance();
    auto toDisabledLum = [bDarkFace, nFaceLum](sal_uInt8 nLum) -> sal_uInt8 {
        if (bDarkFace)
            return std::min(255, nFaceLum + nLum * 3 / 16);
        return nLum / 4 + 160;
    };

    auto ePixelFormat = rBitmap.getPixelFormat();
    const BitmapPalette* pPal
        = vcl::isPalettePixelFormat(ePixelFormat) ? &Bitmap::GetGreyPalette(256) : nullptr;
    Bitmap aGrey(aSize, ePixelFormat, pPal);
    BitmapScopedWriteAccess pGrey(aGrey);

    BitmapScopedReadAccess pRead(rBitmap);
    if (pRead && pGrey)
    {
        for (sal_Int32 nY = 0; nY < sal_Int32(aSize.Height()); ++nY)
        {
            Scanline pGreyScan = pGrey->GetScanline(nY);
            Scanline pReadScan = pRead->GetScanline(nY);

            for (sal_Int32 nX = 0; nX < sal_Int32(aSize.Width()); ++nX)
            {
                const BitmapColor aColor = pRead->GetPixelFromData(pReadScan, nX);
                sal_uInt8 nLum(toDisabledLum(aColor.GetLuminance()));
                BitmapColor aGreyValue(ColorAlpha, nLum, nLum, nLum, aColor.GetAlpha());
                pGrey->SetPixelOnData(pGreyScan, nX, aGreyValue);
            }
        }
    }

    return aGrey;
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
