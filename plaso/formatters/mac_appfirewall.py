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
"""Formatter for the Mac appfirewall.log file."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacAppFirewallLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for Mac appfirewall.log file."""

  DATA_TYPE = 'mac:asl:appfirewall:line'

  FORMAT_STRING_PIECES = [
      u'Computer: {computer_name}',
      u'Agent: {agent}',
      u'Status: {status}',
      u'Process name: {process_name}',
      u'Log: {action}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Process name: {process_name}',
      u'Status: {status}']

  SOURCE_LONG = 'Mac AppFirewall Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(MacAppFirewallLogFormatter)
