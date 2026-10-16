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
#include <array>
#include <cmath>

namespace
{
// An sRGB channel (0-255) in linear light (0-1), as for the WCAG 2.1 relative luminance.
double toLinear(sal_uInt8 nValue)
{
    const double f = nValue / 255.0;
    return f <= 0.04045 ? f / 12.92 : std::pow((f + 0.055) / 1.055, 2.4);
}

sal_uInt8 toSRGB(double fLinear)
{
    const double f
        = fLinear <= 0.0031308 ? 12.92 * fLinear : 1.055 * std::pow(fLinear, 1 / 2.4) - 0.055;
    return std::clamp<long>(std::lround(f * 255), 0, 255);
}
}

Bitmap BitmapDisabledImageFilter::execute(Bitmap const& rBitmap) const
{
    const Size aSize(rBitmap.GetSizePixel());

    // A disabled image is a grey version of the image, close to the color it is drawn on.
    // On a light face: luminance 0-255 remapped to 160-224, a light grey.
    // On a dark face that light grey would stand out more than the enabled image does. There a
    // pixel of luminance L becomes the grey whose WCAG contrast against the face is 1 + L / 255:
    // as light as the face for black, 2:1 for white. The band is set in contrast, not in sRGB
    // levels, so it dims alike on every dark face down to black (a fixed sRGB band nearly
    // vanishes there), and a disabled icon keeps about the contrast it has on a light face.
    std::array<sal_uInt8, 256> aDisabledLum;
    if (maFaceColor.IsDark())
    {
        const double fFace = 0.2126 * toLinear(maFaceColor.GetRed())
                             + 0.7152 * toLinear(maFaceColor.GetGreen())
                             + 0.0722 * toLinear(maFaceColor.GetBlue()) + 0.05;
        for (int nLum = 0; nLum < 256; ++nLum)
            aDisabledLum[nLum] = toSRGB((1.0 + nLum / 255.0) * fFace - 0.05);
    }
    else
    {
        for (int nLum = 0; nLum < 256; ++nLum)
            aDisabledLum[nLum] = nLum / 4 + 160;
    }

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
                sal_uInt8 nLum(aDisabledLum[aColor.GetLuminance()]);
                BitmapColor aGreyValue(ColorAlpha, nLum, nLum, nLum, aColor.GetAlpha());
                pGrey->SetPixelOnData(pGreyScan, nX, aGreyValue);
            }
        }
    }

    return aGrey;
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
