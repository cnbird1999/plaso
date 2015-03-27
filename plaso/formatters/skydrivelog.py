# -*- coding: utf-8 -*-
"""The SkyDrive log event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class SkyDriveLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SkyDrive log file event."""

  DATA_TYPE = 'skydrive:log:line'

  FORMAT_STRING_PIECES = [
      u'[{source_code}]',
      u'({log_level})',
      u'{text}']

  FORMAT_STRING_SHORT_PIECES = [u'{text}']

  SOURCE_LONG = 'SkyDrive Log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(SkyDriveLogFormatter)
