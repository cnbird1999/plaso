#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""Formatter for Basic Security Module binary files."""

from plaso.formatters import interface
from plaso.formatters import manager


class BSMFormatter(interface.ConditionalEventFormatter):
  """Formatter for an BSM log entry."""

  DATA_TYPE = 'bsm:event'

  FORMAT_STRING_PIECES = [
      u'Type: {event_type}',
      u'Information: {extra_tokens}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Type: {event_type}']

  SOURCE_LONG = 'BSM entry'
  SOURCE_SHORT = 'LOG'


class MacBSMFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Mac OS X BSM log entry."""

  DATA_TYPE = 'mac:bsm:event'

  FORMAT_STRING_PIECES = [
      u'Type: {event_type}',
      u'Return: {return_value}',
      u'Information: {extra_tokens}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Type: {event_type}',
      u'Return: {return_value}']

  SOURCE_LONG = 'BSM entry'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    BSMFormatter, MacBSMFormatter])
