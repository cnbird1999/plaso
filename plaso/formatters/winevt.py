# -*- coding: utf-8 -*-
"""Formatter for Windows EventLog (EVT) files."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinEvtFormatter(interface.ConditionalEventFormatter):
  """Define the formatting for Windows EventLog (EVT) record."""

  DATA_TYPE = 'windows:evt:record'

  # TODO: add string representation of facility.
  FORMAT_STRING_PIECES = [
      u'[{event_identifier} /',
      u'0x{event_identifier:04x}]',
      u'Severity: {severity_string}',
      u'Record Number: {record_number}',
      u'Event Type: {event_type_string}',
      u'Event Category: {event_category}',
      u'Source Name: {source_name}',
      u'Computer Name: {computer_name}',
      u'Strings: {strings}']

  FORMAT_STRING_SHORT_PIECES = [
      u'[{event_identifier} /',
      u'0x{event_identifier:04x}]',
      u'Strings: {strings}']

  SOURCE_LONG = 'WinEVT'
  SOURCE_SHORT = 'EVT'

  # Mapping of the numeric event types to a descriptive string.
  _EVENT_TYPES = [
      u'Error event',
      u'Warning event',
      u'Information event',
      u'Success Audit event',
      u'Failure Audit event']

  _SEVERITY = [
      u'Success',
      u'Informational',
      u'Warning',
      u'Error']

  def GetEventTypeString(self, event_type):
    """Retrieves a string representation of the event type.

    Args:
      event_type: The numeric event type.

    Returns:
      An Unicode string containing a description of the event type.
    """
    if event_type >= 0 and event_type < len(self._EVENT_TYPES):
      return self._EVENT_TYPES[event_type]
    return u'Unknown {0:d}'.format(event_type)

  def GetSeverityString(self, severity):
    """Retrieves a string representation of the severity.

    Args:
      severity: The numeric severity.

    Returns:
      An Unicode string containing a description of the event type.
    """
    if severity >= 0 and severity < len(self._SEVERITY):
      return self._SEVERITY[severity]
    return u'Unknown {0:d}'.format(severity)

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

    # Update event object with the event type string.
    event_object.event_type_string = self.GetEventTypeString(
        event_object.event_type)

    # TODO: add string representation of facility.

    # Update event object with the severity string.
    event_object.severity_string = self.GetSeverityString(event_object.severity)

    return super(WinEvtFormatter, self).GetMessages(event_object)


manager.FormattersManager.RegisterFormatter(WinEvtFormatter)
