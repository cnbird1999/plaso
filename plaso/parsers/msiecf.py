# -*- coding: utf-8 -*-
"""Parser for Microsoft Internet Explorer (MSIE) Cache Files (CF)."""

import logging

import pymsiecf

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


if pymsiecf.get_version() < '20130317':
  raise ImportWarning(u'MsiecfParser requires at least pymsiecf 20130317.')


class MsiecfUrlEvent(time_events.TimestampEvent):
  """Convenience class for an MSIECF URL event."""

  DATA_TYPE = 'msiecf:url'

  def __init__(
      self, timestamp, timestamp_description, msiecf_item, recovered=False):
    """Initializes the event.

    Args:
      timestamp: The timestamp value.
      timestamp_desc: The usage string describing the timestamp.
      msiecf_item: The MSIECF item (pymsiecf.url).
      recovered: Boolean value to indicate the item was recovered, False
                 by default.
    """
    super(MsiecfUrlEvent, self).__init__(timestamp, timestamp_description)

    self.recovered = recovered
    self.offset = msiecf_item.offset

    self.url = msiecf_item.location
    self.number_of_hits = msiecf_item.number_of_hits
    self.cache_directory_index = msiecf_item.cache_directory_index
    self.filename = msiecf_item.filename
    self.cached_file_size = msiecf_item.cached_file_size

    if msiecf_item.type and msiecf_item.data:
      if msiecf_item.type == u'cache':
        if msiecf_item.data[:4] == 'HTTP':
          self.http_headers = msiecf_item.data[:-1]
      # TODO: parse data of other URL item type like history which requires
      # OLE VT parsing.


class MsiecfParser(interface.BaseParser):
  """Parses MSIE Cache Files (MSIECF)."""

  NAME = 'msiecf'
  DESCRIPTION = u'Parser for MSIE Cache Files (MSIECF) also known as index.dat.'

  def _ParseUrl(self, parser_mediator, msiecf_item, recovered=False):
    """Extract data from a MSIE Cache Files (MSIECF) URL item.

       Every item is stored as an event object, one for each timestamp.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      msiecf_item: An item (pymsiecf.url).
      recovered: Boolean value to indicate the item was recovered, False
                 by default.
    """
    # The secondary timestamp can be stored in either UTC or local time
    # this is dependent on what the index.dat file is used for.
    # Either the file path of the location string can be used to distinguish
    # between the different type of files.
    primary_timestamp = timelib.Timestamp.FromFiletime(
        msiecf_item.get_primary_time_as_integer())
    primary_timestamp_desc = 'Primary Time'

    # Need to convert the FILETIME to the internal timestamp here to
    # do the from localtime conversion.
    secondary_timestamp = timelib.Timestamp.FromFiletime(
        msiecf_item.get_secondary_time_as_integer())
    secondary_timestamp_desc = 'Secondary Time'

    if msiecf_item.type:
      if msiecf_item.type == u'cache':
        primary_timestamp_desc = eventdata.EventTimestamp.ACCESS_TIME
        secondary_timestamp_desc = eventdata.EventTimestamp.MODIFICATION_TIME

      elif msiecf_item.type == u'cookie':
        primary_timestamp_desc = eventdata.EventTimestamp.ACCESS_TIME
        secondary_timestamp_desc = eventdata.EventTimestamp.MODIFICATION_TIME

      elif msiecf_item.type == u'history':
        primary_timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME
        secondary_timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME

      elif msiecf_item.type == u'history-daily':
        primary_timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME
        secondary_timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME
        # The secondary_timestamp is in localtime normalize it to be in UTC.
        secondary_timestamp = timelib.Timestamp.LocaltimeToUTC(
            secondary_timestamp, parser_mediator.timezone)

      elif msiecf_item.type == u'history-weekly':
        primary_timestamp_desc = eventdata.EventTimestamp.CREATION_TIME
        secondary_timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME
        # The secondary_timestamp is in localtime normalize it to be in UTC.
        secondary_timestamp = timelib.Timestamp.LocaltimeToUTC(
            secondary_timestamp, parser_mediator.timezone)

    event_object = MsiecfUrlEvent(
        primary_timestamp, primary_timestamp_desc, msiecf_item, recovered)
    parser_mediator.ProduceEvent(event_object)

    if secondary_timestamp > 0:
      event_object = MsiecfUrlEvent(
          secondary_timestamp, secondary_timestamp_desc, msiecf_item,
          recovered)
      parser_mediator.ProduceEvent(event_object)

    expiration_timestamp = msiecf_item.get_expiration_time_as_integer()
    if expiration_timestamp > 0:
      # The expiration time in MSIECF version 4.7 is stored as a FILETIME value
      # in version 5.2 it is stored as a FAT date time value.
      # Since the as_integer function returns the raw integer value we need to
      # apply the right conversion here.
      if self.version == u'4.7':
        event_object = MsiecfUrlEvent(
            timelib.Timestamp.FromFiletime(expiration_timestamp),
            eventdata.EventTimestamp.EXPIRATION_TIME, msiecf_item, recovered)
      else:
        event_object = MsiecfUrlEvent(
            timelib.Timestamp.FromFatDateTime(expiration_timestamp),
            eventdata.EventTimestamp.EXPIRATION_TIME, msiecf_item, recovered)

      parser_mediator.ProduceEvent(event_object)

    last_checked_timestamp = msiecf_item.get_last_checked_time_as_integer()
    if last_checked_timestamp > 0:
      event_object = MsiecfUrlEvent(
          timelib.Timestamp.FromFatDateTime(last_checked_timestamp),
          eventdata.EventTimestamp.LAST_CHECKED_TIME, msiecf_item, recovered)
      parser_mediator.ProduceEvent(event_object)

  def Parse(self, parser_mediator, **kwargs):
    """Extract data from a MSIE Cache File (MSIECF).

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    file_object = parser_mediator.GetFileObject()
    msiecf_file = pymsiecf.file()
    msiecf_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      msiecf_file.open_file_object(file_object)

      self.version = msiecf_file.format_version
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, parser_mediator.GetDisplayName(), exception))



    for item_index in range(0, msiecf_file.number_of_items):
      try:
        msiecf_item = msiecf_file.get_item(item_index)
        if isinstance(msiecf_item, pymsiecf.url):
          self._ParseUrl(parser_mediator, msiecf_item)

        # TODO: implement support for pymsiecf.leak, pymsiecf.redirected,
        # pymsiecf.item.
      except IOError as exception:
        logging.warning(
            u'[{0:s}] unable to parse item: {1:d} in file: {2:s}: {3:s}'.format(
                self.NAME, item_index, parser_mediator.GetDisplayName(),
                exception))

    for item_index in range(0, msiecf_file.number_of_recovered_items):
      try:
        msiecf_item = msiecf_file.get_recovered_item(item_index)
        if isinstance(msiecf_item, pymsiecf.url):
          self._ParseUrl(
              parser_mediator, msiecf_item, recovered=True)

        # TODO: implement support for pymsiecf.leak, pymsiecf.redirected,
        # pymsiecf.item.
      except IOError as exception:
        logging.info((
            u'[{0:s}] unable to parse recovered item: {1:d} in file: {2:s}: '
            u'{3:s}').format(
                self.NAME, item_index, parser_mediator.GetDisplayName(),
                exception))

    file_object.close()


manager.ParsersManager.RegisterParser(MsiecfParser)
