/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 */

#pragma once

#include <tools/color.hxx>
#include <vcl/bitmap/BitmapFilter.hxx>

class VCL_DLLPUBLIC BitmapDisabledImageFilter final : public BitmapFilter
{
public:
    /** Makes the grey, dimmed version of an image that a disabled control shows.

        @param rFaceColor the color the image is drawn on (StyleSettings::GetFaceColor()).
        On a light face the result is a light grey (luminance mapped to 160-224, as it always
        was); on a dark face it is a dark grey just above the face (luminance mapped to
        face luminance + 0-47), so a disabled image looks dimmed in dark themes too. */
    explicit BitmapDisabledImageFilter(const Color& rFaceColor = COL_LIGHTGRAY)
        : maFaceColor(rFaceColor)
    {
    }

    virtual Bitmap execute(Bitmap const& rBitmap) const override;

private:
    Color maFaceColor;
};

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
