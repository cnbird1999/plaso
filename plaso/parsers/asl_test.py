#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Apple System Log file parser."""

import unittest

from plaso.formatters import asl as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import asl
from plaso.parsers import test_lib


class AslParserTest(test_lib.ParserTestCase):
  """Tests for Apple System Log file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = asl.AslParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['applesystemlog.asl'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)

    event_object = event_objects[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-11-25 09:45:35.705481')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.record_position, 442)
    self.assertEqual(event_object.message_id, 101406)
    self.assertEqual(event_object.computer_name, u'DarkTemplar-2.local')
    self.assertEqual(event_object.sender, u'locationd')
    self.assertEqual(event_object.facility, u'com.apple.locationd')
    self.assertEqual(event_object.pid, 69)
    self.assertEqual(event_object.user_sid, u'205')
    self.assertEqual(event_object.group_id, 205)
    self.assertEqual(event_object.read_uid, 205)
    self.assertEqual(event_object.read_gid, 'ALL')
    self.assertEqual(event_object.level, u'WARNING (4)')

    expected_message = (
        u'Incorrect NSStringEncoding value 0x8000100 detected. '
        u'Assuming NSASCIIStringEncoding. Will stop this compatiblity '
        u'mapping behavior in the near future.')

    self.assertEqual(event_object.message, expected_message)

    expected_extra = (
        u'[CFLog Local Time: 2013-11-25 09:45:35.701]'
        u'[CFLog Thread: 1007]'
        u'[Sender_Mach_UUID: 50E1F76A-60FF-368C-B74E-EB48F6D98C51]')

    self.assertEqual(event_object.extra_information, expected_extra)

    expected_msg = (
        u'MessageID: 101406 '
        u'Level: WARNING (4) '
        u'User ID: 205 '
        u'Group ID: 205 '
        u'Read User: 205 '
        u'Read Group: ALL '
        u'Host: DarkTemplar-2.local '
        u'Sender: locationd '
        u'Facility: com.apple.locationd '
        u'Message: {0:s} {1:s}').format(expected_message, expected_extra)

    expected_msg_short = (
        u'Sender: locationd '
        u'Facility: com.apple.locationd')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
