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
"""Formatter for Chrome Cache files based-events."""

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeCacheEntryEventFormatter(interface.ConditionalEventFormatter):
  """Class contains the Chrome Cache Entry event formatter."""

  DATA_TYPE = 'chrome:cache:entry'

  FORMAT_STRING_PIECES = [
      u'Original URL: {original_url}']

  SOURCE_LONG = 'Chrome Cache'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(ChromeCacheEntryEventFormatter)
