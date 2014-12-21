#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains a formatter for the Safari Binary cookie."""

from plaso.formatters import interface


class SafaryCookieFormatter(interface.ConditionalEventFormatter):
  """The event formatter for cookie data in Safari Binary Cookie file."""

  DATA_TYPE = 'safari:cookie:entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'<{path}>',
      u'({cookie_name})',
      u'Flags: {flags}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{url}',
      u'({cookie_name})']

  SOURCE_LONG = 'Safari Cookies'
  SOURCE_SHORT = 'WEBHIST'
