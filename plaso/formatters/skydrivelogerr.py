# -*- coding: utf-8 -*-
"""The SkyDrive error log event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class SkyDriveLogErrorFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SkyDrive error log file event."""

  DATA_TYPE = 'skydrive:error:line'

  FORMAT_STRING_PIECES = [
      u'[{module}',
      u'{source_code}]',
      u'{text}',
      u'({detail})']

  FORMAT_STRING_SHORT_PIECES = [u'{text}']

  SOURCE_LONG = 'SkyDrive Error Log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(SkyDriveLogErrorFormatter)
