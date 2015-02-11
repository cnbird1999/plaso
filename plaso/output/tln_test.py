#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the TLN output class."""

import StringIO
import unittest

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import event
from plaso.output import tln


class TlnTestEvent(event.EventObject):
  """Simplified EventObject for testing."""
  DATA_TYPE = 'test:l2ttln'

  def __init__(self):
    """Initialize event with data."""
    super(TlnTestEvent, self).__init__()
    self.timestamp = 1340821021000000
    self.hostname = u'ubuntu'
    self.display_name = u'OS: log/syslog.1'
    self.inode = 12345678
    self.text = (
        u'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
        u'closed for user root)')
    self.username = u'root'


class L2TTlnTestEventFormatter(formatters_interface.EventFormatter):
  """Formatter for the test event."""
  DATA_TYPE = 'test:l2ttln'
  FORMAT_STRING = u'{text}'
  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


formatters_manager.FormattersManager.RegisterFormatter(L2TTlnTestEventFormatter)


class TlnTest(unittest.TestCase):
  """Tests for the TLN outputter."""

  def setUp(self):
    """Sets up the objects needed for this test."""
    self.output = StringIO.StringIO()
    self.formatter = tln.TlnOutputFormatter(None, self.output)
    self.event_object = TlnTestEvent()

  def testStart(self):
    """Test ensures header line is outputted as expected."""
    correct_line = u'Time|Source|Host|User|Description\n'

    self.formatter.Start()
    self.assertEquals(self.output.getvalue(), correct_line)

  def testEventBody(self):
    """Test ensures that returned lines returned are formatted as TLN."""

    self.formatter.EventBody(self.event_object)
    correct = (u'1340821021|LOG|ubuntu|root|Reporter <CRON> PID:  8442  '
               u'(pam_unix(cron:session): session closed for user root)\n')
    self.assertEquals(self.output.getvalue(), correct)

  def testEventBodyNoStrayPipes(self):
    """Test ensures that the only pipes are the four field delimiters."""

    self.formatter.EventBody(self.event_object)
    self.assertEquals(self.output.getvalue().count(u'|'), 4)


if __name__ == '__main__':
  unittest.main()
