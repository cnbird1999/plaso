# -*- coding: utf-8 -*-
"""The common front-end functionality."""

import abc
import locale
import logging
import sys


class FrontendInputReader(object):
  """Class that implements the input reader interface for the engine."""

  @abc.abstractmethod
  def Read(self):
    """Reads a string from the input.

    Returns:
      A string containing the input.
    """


class FrontendOutputWriter(object):
  """Class that implements the output writer interface for the engine."""

  @abc.abstractmethod
  def Write(self, string):
    """Writes a string to the output.

    Args:
      string: A string containing the output.
    """


class StdinFrontendInputReader(object):
  """Class that implements a stdin input reader."""

  def Read(self):
    """Reads a string from the input.

    Returns:
      A string containing the input.
    """
    return sys.stdin.readline()


class StdoutFrontendOutputWriter(object):
  """Class that implements a stdout output writer."""

  ENCODING = u'utf-8'

  def Write(self, string):
    """Writes a string to the output.

    Args:
      string: A string containing the output.
    """
    try:
      sys.stdout.write(string.encode(self.ENCODING))
    except UnicodeEncodeError:
      logging.error(
          u'Unable to properly write output, line will be partially '
          u'written out.')
      sys.stdout.write(u'LINE ERROR')
      sys.stdout.write(string.encode(self.ENCODING, 'ignore'))


class Frontend(object):
  """Class that implements a front-end."""

  # The maximum length of the line in number of characters.
  _LINE_LENGTH = 80

  def __init__(self, input_reader, output_writer):
    """Initializes the front-end object.

    Args:
      input_reader: the input reader (instance of FrontendInputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: the output writer (instance of FrontendOutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(Frontend, self).__init__()
    self._input_reader = input_reader
    self._output_writer = output_writer

    # TODO: add preferred_encoding support of the output writer.
    self.preferred_encoding = locale.getpreferredencoding().lower()

  def PrintColumnValue(self, name, description, column_length=25):
    """Prints a value with a name and description aligned to the column length.

    Args:
      name: The name.
      description: The description.
      column_length: Optional column length. The default is 25.
    """
    line_length = self._LINE_LENGTH - column_length - 3

    # The format string of the first line of the column value.
    primary_format_string = u'{{0:>{0:d}s}} : {{1:s}}\n'.format(column_length)

    # The format string of successive lines of the column value.
    secondary_format_string = u'{{0:<{0:d}s}}{{1:s}}\n'.format(
        column_length + 3)

    if len(description) < line_length:
      self._output_writer.Write(primary_format_string.format(name, description))
      return

    # Split the description in words.
    words = description.split()

    current = 0

    lines = []
    word_buffer = []
    for word in words:
      current += len(word) + 1
      if current >= line_length:
        current = len(word)
        lines.append(u' '.join(word_buffer))
        word_buffer = [word]
      else:
        word_buffer.append(word)
    lines.append(u' '.join(word_buffer))

    # Print the column value on multiple lines.
    self._output_writer.Write(primary_format_string.format(name, lines[0]))
    for line in lines[1:]:
      self._output_writer.Write(secondary_format_string.format(u'', line))

  def PrintHeader(self, text, character='*'):
    """Prints the header as a line with centered text.

    Args:
      text: The header text.
      character: Optional header line character. The default is '*'.
    """
    self._output_writer.Write(u'\n')

    format_string = u'{{0:{0:s}^{1:d}}}\n'.format(character, self._LINE_LENGTH)
    header_string = format_string.format(u' {0:s} '.format(text))
    self._output_writer.Write(header_string)

  def PrintSeparatorLine(self):
    """Prints a separator line."""
    self._output_writer.Write(u'{0:s}\n'.format(u'-' * self._LINE_LENGTH))


class Options(object):
  """A simple configuration object."""
