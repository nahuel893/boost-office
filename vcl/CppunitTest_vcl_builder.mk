# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

$(eval $(call gb_CppunitTest_CppunitTest,vcl_builder))

$(eval $(call gb_CppunitTest_add_exception_objects,vcl_builder, \
	vcl/qa/cppunit/builder/builder \
))

$(eval $(call gb_CppunitTest_use_libraries,vcl_builder, \
	comphelper \
	cppu \
	cppuhelper \
	sal \
	subsequenttest \
	test \
	tl \
	unotest \
	utl \
	vcl \
))

$(eval $(call gb_CppunitTest_use_externals,vcl_builder, \
	boost_headers \
	libxml2 \
))

$(eval $(call gb_CppunitTest_use_sdk_api,vcl_builder))

$(eval $(call gb_CppunitTest_use_ure,vcl_builder))
$(eval $(call gb_CppunitTest_use_vcl,vcl_builder))

$(eval $(call gb_CppunitTest_use_rdb,vcl_builder,services))

$(eval $(call gb_CppunitTest_use_configuration,vcl_builder))

# vim: set noet sw=4 ts=4:
