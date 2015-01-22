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
"""Formatter for the UTMP binary files."""

from plaso.formatters import interface
from plaso.formatters import manager


class UtmpSessionFormatter(interface.ConditionalEventFormatter):
  """Formatter for UTMP session."""

  DATA_TYPE = 'linux:utmp:event'

  FORMAT_STRING_PIECES = [
      u'User: {user}',
      u'Computer Name: {computer_name}',
      u'Terminal: {terminal}',
      u'PID: {pid}',
      u'Terminal_ID: {terminal_id}',
      u'Status: {status}',
      u'IP Address: {ip_address}',
      u'Exit: {exit}']

  FORMAT_STRING_SHORT_PIECES = [u'User: {user}']

  SOURCE_LONG = 'UTMP session'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(UtmpSessionFormatter)
