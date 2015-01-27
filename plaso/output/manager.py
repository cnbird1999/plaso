#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 The Plaso Project Authors.
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
"""This file contains the output manager class."""


class OutputManager(object):
  """Class that implements the output manager."""

  _output_classes = {}

  @classmethod
  def DeregisterOutput(cls, output_class):
    """Deregisters an output class.

    The output classes are identified based on their NAME attribute.

    Args:
      output_class: the class object of the output.

    Raises:
      KeyError: if output class is not set for the corresponding data type.
    """
    output_class_name = output_class.NAME.lower()
    if output_class_name not in cls._output_classes:
      raise KeyError(
          u'Output class not set for name: {0:s}.'.format(
              output_class.NAME))

    del cls._output_classes[output_class_name]

  @classmethod
  def GetOutputClass(cls, name):
    """Retrieves the output object for a specific name.

    Args:
      name: The name of the output.

    Returns:
      The corresponding output (instance of LogOutputFormatter).

    Raises:
      KeyError: if there is no output object found with the
                supplied name or if the name is not a string.
    """
    if not isinstance(name, basestring):
      raise KeyError(u'Name attribute is not a string.')

    name = name.lower()
    if name not in cls._output_classes:
      raise KeyError(u'Name: [{0:s}] not registered as an output.'.format(name))

    return cls._output_classes[name]

  @classmethod
  def GetOutputs(cls):
    """Generate a list of all available output formatter classes."""
    for output_class in cls._output_classes.itervalues():
      yield output_class.NAME, output_class.DESCRIPTION

  @classmethod
  def RegisterOutput(cls, output_class):
    """Registers an output class.

    The output classes are identified based on their NAME attribute.

    Args:
      output_class: the class object of the output (instance of
                    LogOutputFormatter).

    Raises:
      KeyError: if output class is already set for the corresponding
                name attribute.
    """
    output_name = output_class.NAME.lower()
    if output_name in cls._output_classes:
      raise KeyError((
          u'Output class already set for name: {0:s}.').format(
              output_class.NAME))

    cls._output_classes[output_name] = output_class

  @classmethod
  def RegisterOutputs(cls, output_classes):
    """Registers output classes.

    The output classes are identified based on their NAME attribute.

    Args:
      output_classes: a list of class objects of the outputs (instance of
                       LogOutputFormatter).

    Raises:
      KeyError: if output class is already set for the corresponding name.
    """
    for output_class in output_classes:
      cls.RegisterOutput(output_class)
