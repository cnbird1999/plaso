#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains a parser for the Mac OS X application usage.

   The application usage is stored in SQLite database files named
   /var/db/application_usage.sqlite
"""

from plaso.events import time_events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class MacOSXApplicationUsageEvent(time_events.PosixTimeEvent):
  """Convenience class for a Mac OS X application usage event."""

  DATA_TYPE = 'macosx:application_usage'

  def __init__(
      self, posix_time, usage, application_name, application_version,
      bundle_id, number_of_times):
    """Initializes the event object.

    Args:
      posix_time: The POSIX time value.
      usage: The description of the usage of the time value.
      application_name: The name of the application.
      application_version: The version of the application.
      bundle_id: The bundle identifier of the application.
      number_of_times: TODO: number of times what?
    """
    super(MacOSXApplicationUsageEvent, self).__init__(posix_time, usage)

    self.application = application_name
    self.app_version = application_version
    self.bundle_id = bundle_id
    self.count = number_of_times


class ApplicationUsagePlugin(interface.SQLitePlugin):
  """Parse Application Usage history files.

  Application usage is a SQLite database that logs down entries
  triggered by NSWorkspaceWillLaunchApplicationNotification and
  NSWorkspaceDidTerminateApplicationNotification NSWorkspace notifications by
  crankd.

  See the code here:
  http://code.google.com/p/google-macops/source/browse/trunk/crankd/\
      ApplicationUsage.py

  Default installation: /var/db/application_usage.sqlite
  """

  NAME = 'appusage'
  DESCRIPTION = u'Parser for Mac OS X application usage SQLite database files.'

  # Define the needed queries.
  QUERIES = [(
      ('SELECT last_time, event, bundle_id, app_version, app_path, '
       'number_times FROM application_usage ORDER BY last_time'),
      'ParseApplicationUsageRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset(['application_usage'])

  def ParseApplicationUsageRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses an application usage row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    # TODO: replace usage by definition(s) in eventdata. Not sure which values
    # it will hold here.
    usage = u'Application {0:s}'.format(row['event'])

    event_object = MacOSXApplicationUsageEvent(
        row['last_time'], usage, row['app_path'], row['app_version'],
        row['bundle_id'], row['number_times'])
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(ApplicationUsagePlugin)
