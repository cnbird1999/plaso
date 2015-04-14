#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Restore Point (rp.log) file event formatter."""

import unittest

from plaso.formatters import test_lib
from plaso.formatters import winrestore


class RestorePointInfoFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows Restore Point information event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winrestore.RestorePointInfoFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winrestore.RestorePointInfoFormatter()

    expected_attribute_names = [
        u'description',
        u'restore_point_event_type',
        u'restore_point_type']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
