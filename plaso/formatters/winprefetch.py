# -*- coding: utf-8 -*-
"""Formatter for the Windows Prefetch events."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinPrefetchExecutionFormatter(interface.ConditionalEventFormatter):
  """Class that formats Windows Prefetch execution events."""

  DATA_TYPE = 'windows:prefetch:execution'

  FORMAT_STRING_PIECES = [
      u'Prefetch',
      u'[{executable}] was executed -',
      u'run count {run_count}',
      u'path: {path}',
      u'hash: 0x{prefetch_hash:08X}',
      u'{volumes_string}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{executable} was run',
      u'{run_count} time(s)']

  SOURCE_LONG = 'WinPrefetch'
  SOURCE_SHORT = 'LOG'

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from an event object.

    Args:
      event_object: The event object (instance of EventObject) containing
                    the event specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.

    Raises:
      WrongFormatter: when the data type of the formatter does not match
                      that of the event object.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(
          u'Invalid event object - unsupported data type: {0:s}'.format(
              event_object.data_type))

    volumes_strings = []
    for volume_index in range(0, event_object.number_of_volumes):
      volumes_strings.append((
          u'volume: {0:d} [serial number: 0x{1:08X}, device path: '
          u'{2:s}]').format(
              volume_index + 1,
              event_object.volume_serial_numbers[volume_index],
              event_object.volume_device_paths[volume_index]))

    if volumes_strings:
      event_object.volumes_string = u', '.join(volumes_strings)

    return super(WinPrefetchExecutionFormatter, self).GetMessages(event_object)


manager.FormattersManager.RegisterFormatter(WinPrefetchExecutionFormatter)
