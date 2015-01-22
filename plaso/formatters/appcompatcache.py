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
"""Formatter for the AppCompatCache entries inside the Windows Registry."""

from plaso.formatters import interface
from plaso.formatters import manager


class AppCompatCacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for an AppCompatCache Windows Registry entry."""

  DATA_TYPE = 'windows:registry:appcompatcache'

  FORMAT_STRING_PIECES = [
      u'[{keyname}]',
      u'Cached entry: {entry_index}',
      u'Path: {path}']

  FORMAT_STRING_SHORT_PIECES = [u'Path: {path}']

  SOURCE_LONG = 'AppCompatCache Registry Entry'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(AppCompatCacheFormatter)
