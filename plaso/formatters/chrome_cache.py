# -*- coding: utf-8 -*-
"""The Google Chrome Cache files event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeCacheEntryEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Chrome Cache entry event."""

  DATA_TYPE = 'chrome:cache:entry'

  FORMAT_STRING_PIECES = [
      u'Original URL: {original_url}']

  SOURCE_LONG = 'Chrome Cache'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(ChromeCacheEntryEventFormatter)
