#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the output manager."""

import unittest

from plaso.output import interface
from plaso.output import manager


class TestOutput(interface.LogOutputFormatter):
  """Test output module."""

  NAME = 'test_output'
  DESCRIPTION = u'This is a test output module.'

  def EventBody(self, event_object):
    """Writes the main body of an event to the output filehandle.

    Args:
      event_object: An event object (instance of EventObject).
    """
    pass


class OutputManagerTest(unittest.TestCase):
  """Tests for the output manager."""

  def testRegistration(self):
    """Tests the RegisterOutput and DeregisterOutput functions."""
    # pylint: disable=protected-access
    number_of_parsers = len(manager.OutputManager._output_classes)

    manager.OutputManager.RegisterOutput(TestOutput)

    with self.assertRaises(KeyError):
      manager.OutputManager.RegisterOutput(TestOutput)

    self.assertEquals(
        len(manager.OutputManager._output_classes),
        number_of_parsers + 1)

    with self.assertRaises(KeyError):
      manager.OutputManager.RegisterOutput(TestOutput)

    manager.OutputManager.DeregisterOutput(TestOutput)
    self.assertEquals(
        len(manager.OutputManager._output_classes),
        number_of_parsers)

  def testGetOutputClass(self):
    """Tests the GetOutputClass function."""
    manager.OutputManager.RegisterOutput(TestOutput)

    output_class = manager.OutputManager.GetOutputClass('test_output')
    self.assertEquals(output_class, TestOutput)

    with self.assertRaises(ValueError):
      _ = manager.OutputManager.GetOutputClass(1)

    with self.assertRaises(KeyError):
      _ = manager.OutputManager.GetOutputClass('bogus')

    manager.OutputManager.DeregisterOutput(TestOutput)

  def testHasOutputClass(self):
    """Tests the HasOutputClass function."""
    manager.OutputManager.RegisterOutput(TestOutput)

    self.assertTrue(manager.OutputManager.HasOutputClass('test_output'))
    self.assertFalse(manager.OutputManager.HasOutputClass('bogus'))
    self.assertFalse(manager.OutputManager.HasOutputClass(1))

    manager.OutputManager.DeregisterOutput(TestOutput)

  def testGetOutputs(self):
    """Tests the GetOtputs function."""
    manager.OutputManager.RegisterOutput(TestOutput)

    names = []
    descriptions = []

    for name, description in manager.OutputManager.GetOutputs():
      names.append(name)
      descriptions.append(description)

    self.assertIn('test_output', names)
    self.assertIn(u'This is a test output module.', descriptions)

    manager.OutputManager.DeregisterOutput(TestOutput)


if __name__ == '__main__':
  unittest.main()
