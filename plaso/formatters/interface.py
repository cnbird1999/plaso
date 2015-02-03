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
"""This file contains the event formatters interface classes."""

import logging
import re

from plaso.lib import errors


class EventFormatter(object):
  """Base class to format event type specific data using a format string.

     Define the (long) format string and the short format string by defining
     FORMAT_STRING and FORMAT_STRING_SHORT. The syntax of the format strings
     is similar to that of format() where the place holder for a certain
     event object attribute is defined as {attribute_name}.
  """

  # The data type is a unique identifier for the event data. The current
  # approach is to define it as human readable string in the format
  # root:branch: ... :leaf, e.g. a page visited entry inside a Chrome History
  # database is defined as: chrome:history:page_visited.
  DATA_TYPE = u'internal'

  # The format string.
  FORMAT_STRING = u''
  FORMAT_STRING_SHORT = u''

  # The source short and long strings.
  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u''

  def __init__(self):
    """Set up the formatter and determine if this is the right formatter."""
    super(EventFormatter, self).__init__()

    # TODO: currently the output code directly accesses the format string
    # attribute. Remove this.
    self.format_string = None

    # Forcing the format string to be Unicode to make sure we don't
    # try to format it as an ASCII string.
    self.source_string = unicode(self.SOURCE_LONG)
    self.source_string_short = unicode(self.SOURCE_SHORT)

  def _FormatMessage(self, format_string, event_values):
    """Determines the formatted message string.

    Args:
      format_string: a Unicode string containing the message format string.
      event_values: a dictionary object containing the event (object) values.

    Returns:
      The formatted message string.
    """
    # TODO: this does not work in Python 3.
    if not isinstance(format_string, unicode):
      logging.warning(u'Format string: {0:s} is non-Unicode.'.format(
          format_string))

      # Plaso code files should be in UTF-8 any thus binary strings are
      # assumed UTF-8. If this is not the case this should be fixed.
      format_string = format_string.decode(u'utf-8', errors=u'ignore')

    try:
      message_string = format_string.format(**event_values)

    except KeyError as exception:
      logging.warning(
          u'Unable to format string: {0:s} with error: {1:s}'.format(
              format_string, exception))

      attribute_values = []
      for attribute, value in event_values.iteritems():
        attribute_values.append(u'{0:s}: {1!s}'.format(attribute, value))

      message_string = u' '.join(attribute_values)

    # Strip carriage return and linefeed form the message strings.
    # Using replace function here because it is faster than re.sub() or
    # string.strip().
    return message_string.replace('\r', u'').replace('\n', u'')

  def _FormatMessages(self, format_string, short_format_string, event_values):
    """Determines the formatted message strings.

    Args:
      format_string: a Unicode string containing the message format string.
      short_format_string: a Unicode string containing the short message
                           format string.
      event_values: a dictionary object containing the event (object) values.

    Returns:
      A tuple containing the formatted message string and short message string.
    """
    message_string = self._FormatMessage(format_string, event_values)

    if short_format_string:
      short_message_string = self._FormatMessage(
          short_format_string, event_values)
    else:
      short_message_string = message_string

    # Truncate the short message string if necessary.
    if len(short_message_string) > 80:
      short_message_string = u'{0:s}...'.format(short_message_string[0:77])

    # TODO: currently the output code directly accesses the format string
    # attribute. Remove this.
    self.format_string = format_string

    return message_string, short_message_string

  def GetMessages(self, event_object):
    """Return a list of messages extracted from an event object.

    The l2t_csv and other formats are dependent on a message field,
    referred to as description_long and description_short in l2t_csv.

    Plaso does not store this field explicitly, it only contains a format
    string and the appropriate attributes.

    This method takes the format string and converts that back into a
    formatted string that can be used for display.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.GetValues()

    return self._FormatMessages(
        self.FORMAT_STRING, self.FORMAT_STRING_SHORT, event_values)

  def GetSources(self, event_object):
    """Return a list containing source short and long."""
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    return self.source_string_short, self.source_string


class ConditionalEventFormatter(EventFormatter):
  """Base class to conditionally format event data using format string pieces.

     Define the (long) format string and the short format string by defining
     FORMAT_STRING_PIECES and FORMAT_STRING_SHORT_PIECES. The syntax of the
     format strings pieces is similar to of the event formatter
     (EventFormatter). Every format string piece should contain a single
     attribute name or none.

     FORMAT_STRING_SEPARATOR is used to control the string which the separate
     string pieces should be joined. It contains a space by default.
  """
  # The format string pieces.
  FORMAT_STRING_PIECES = [u'']
  FORMAT_STRING_SHORT_PIECES = [u'']

  # The separator used to join the string pieces.
  FORMAT_STRING_SEPARATOR = u' '

  def __init__(self):
    """Initializes the conditional formatter.

       A map is build of the string pieces and their corresponding attribute
       name to optimize conditional string formatting.

    Raises:
      RuntimeError: when an invalid format string piece is encountered.
    """
    super(ConditionalEventFormatter, self).__init__()

    # The format string can be defined as:
    # {name}, {name:format}, {name!conversion}, {name!conversion:format}
    regexp = re.compile('{[a-z][a-zA-Z0-9_]*[!]?[^:}]*[:]?[^}]*}')
    regexp_name = re.compile('[a-z][a-zA-Z0-9_]*')

    # The format string pieces map is a list containing the attribute name
    # per format string piece. E.g. ["Description: {description}"] would be
    # mapped to: [0] = "description". If the string piece does not contain
    # an attribute name it is treated as text that does not needs formatting.
    self._format_string_pieces_map = []
    for format_string_piece in self.FORMAT_STRING_PIECES:
      result = regexp.findall(format_string_piece)
      if not result:
        # The text format string piece is stored as an empty map entry to
        # keep the index in the map equal to the format string pieces.
        self._format_string_pieces_map.append('')
      elif len(result) == 1:
        # Extract the attribute name.
        attribute_name = regexp_name.findall(result[0])[0]
        self._format_string_pieces_map.append(attribute_name)
      else:
        raise RuntimeError((
            u'Invalid format string piece: [{0:s}] contains more than 1 '
            u'attribute name.').format(format_string_piece))

    self._format_string_short_pieces_map = []
    for format_string_piece in self.FORMAT_STRING_SHORT_PIECES:
      result = regexp.findall(format_string_piece)
      if not result:
        # The text format string piece is stored as an empty map entry to
        # keep the index in the map equal to the format string pieces.
        self._format_string_short_pieces_map.append('')
      elif len(result) == 1:
        # Extract the attribute name.
        attribute_name = regexp_name.findall(result[0])[0]
        self._format_string_short_pieces_map.append(attribute_name)
      else:
        raise RuntimeError((
            u'Invalid short format string piece: [{0:s}] contains more '
            u'than 1 attribute name.').format(format_string_piece))

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from an event object.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    # Using getattr here to make sure the attribute is not set to None.
    # if A.b = None, hasattr(A, b) is True but getattr(A, b, None) is False.
    string_pieces = []
    for map_index, attribute_name in enumerate(self._format_string_pieces_map):
      if not attribute_name or hasattr(event_object, attribute_name):
        if attribute_name:
          attribute = getattr(event_object, attribute_name, None)
          # If an attribute is an int, yet has zero value we want to include
          # that in the format string, since that is still potentially valid
          # information. Otherwise we would like to skip it.
          if type(attribute) not in (bool, int, long, float) and not attribute:
            continue
        string_pieces.append(self.FORMAT_STRING_PIECES[map_index])
    format_string = unicode(
        self.FORMAT_STRING_SEPARATOR.join(string_pieces))

    string_pieces = []
    for map_index, attribute_name in enumerate(
        self._format_string_short_pieces_map):
      if not attribute_name or getattr(event_object, attribute_name, None):
        string_pieces.append(self.FORMAT_STRING_SHORT_PIECES[map_index])
    short_format_string = unicode(
        self.FORMAT_STRING_SEPARATOR.join(string_pieces))

    event_values = event_object.GetValues()
    return self._FormatMessages(
        format_string, short_format_string, event_values)
