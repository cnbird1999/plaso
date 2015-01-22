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
"""Contains a class for outputting in a TLN format.

Output module based on TLN as described by:
http://windowsir.blogspot.com/2010/02/timeline-analysisdo-we-need-standard.html

Fields:
  Time - 32 bit Unix epoch.
  Source - The plugin that produced the data.
  Host - The source host system.
  User - The user associated with the data.
  Description - Message string describing the data.
"""

import logging

from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import helper
from plaso.output import interface


class Tln(interface.FileLogOutputFormatter):
  """Five field TLN pipe delimited outputter."""

  DELIMITER = u'|'

  def Start(self):
    """Returns a header for the output."""
    # Build a hostname and username dict objects.
    self._hostnames = {}
    if self.store:
      self._hostnames = helper.BuildHostDict(self.store)
      self._preprocesses = {}
      for info in self.store.GetStorageInformation():
        if hasattr(info, 'store_range'):
          for store_number in range(
              info.store_range[0], info.store_range[1] + 1):
            self._preprocesses[store_number] = info
    self.filehandle.WriteLine(u'Time|Source|Host|User|Description\n')

  def WriteEvent(self, event_object):
    """Write a single event."""
    try:
      self.EventBody(event_object)
    except errors.NoFormatterFound:
      logging.error(u'Unable to output line, no formatter found.')
      logging.error(event_object.GetString())

  def EventBody(self, event_object):
    """Formats data as TLN and writes to the filehandle from OutputFormater.

    Args:
      event_object: The event object (EventObject).

    Raises:
      errors.NoFormatterFound: If no formatter for that event is found.
    """
    if not hasattr(event_object, 'timestamp'):
      return

    # TODO: move this to an output module interface.
    event_formatter = formatters_manager.FormattersManager.GetFormatterObject(
        event_object.data_type)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              event_object.data_type))

    msg, _ = event_formatter.GetMessages(event_object)
    source_short, _ = event_formatter.GetSources(event_object)

    date_use = timelib.Timestamp.CopyToPosix(event_object.timestamp)
    hostname = getattr(event_object, 'hostname', u'')
    username = getattr(event_object, 'username', u'')

    if self.store:
      if not hostname:
        hostname = self._hostnames.get(event_object.store_number, u'')

      pre_obj = self._preprocesses.get(event_object.store_number)
      if pre_obj:
        check_user = pre_obj.GetUsernameById(username)
        if check_user != '-':
          username = check_user

    out_write = u'{0!s}|{1:s}|{2:s}|{3:s}|{4!s}\n'.format(
        date_use,
        source_short.replace(self.DELIMITER, u' '),
        hostname.replace(self.DELIMITER, u' '),
        username.replace(self.DELIMITER, u' '),
        msg.replace(self.DELIMITER, u' '))
    self.filehandle.WriteLine(out_write)
