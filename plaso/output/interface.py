# -*- coding: utf-8 -*-
"""This file contains the interface for output modules."""

import abc
import logging
import sys

from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import utils

import pytz


class OutputModule(object):
  """Class that implements the output module object interface."""

  # TODO: refactor this to the cli classes (aka storage helper).
  # Optional arguments to be added to the argument parser.
  # An example would be:
  #   ARGUMENTS = [('--myparameter', {
  #       'action': 'store',
  #       'help': 'This is my parameter help',
  #       'dest': 'myparameter',
  #       'default': '',
  #       'type': 'unicode'})]
  #
  # Where all arguments into the dict object have a direct translation
  # into the argparse parser.
  ARGUMENTS = []

  NAME = u''
  DESCRIPTION = u''

  def __init__(
      self, store, formatter_mediator, filehandle=sys.stdout, config=None,
      filter_use=None):
    """Initializes the output module object.

    Args:
      store: A storage file object (instance of StorageFile) that defines
             the storage.
      formatter_mediator: The formatter mediator object (instance of
                          FormatterMediator).
      filehandle: Optional file-like object that can be written to.
                  The default is sys.stdout.
      config: Optional configuration object, containing config information.
              The default is None.
      filter_use: Optional filter object (instance of FilterObject).
                  The default is None.
    """
    super(OutputModule, self).__init__()
    self._config = config
    self._filter = filter_use
    self._file_object = filehandle
    self._formatter_mediator = formatter_mediator

    timezone = getattr(config, u'timezone', u'UTC')
    try:
      self._timezone = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
      logging.warning(u'Unkown timezone: {0:s} defaulting to: UTC'.format(
          timezone))
      self._timezone = pytz.utc

    self.encoding = getattr(config, u'preferred_encoding', u'utf-8')
    self.store = store

  def _GetEventFormatter(self, event_object):
    """Retrieves the event formatter for a specific event object type.

    Args:
      event_object: the event object (instance of EventObject)

    Returns:
      The event formatter object (instance of EventFormatter) or None.
    """
    data_type = getattr(event_object, u'data_type', None)
    if not data_type:
      return

    return formatters_manager.FormattersManager.GetFormatterObject(data_type)

  def Close(self):
    """Closes the output."""
    pass

  def Open(self):
    """Opens the output."""
    pass

  def WriteEvent(self, event_object):
    """Writes the event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self.WriteEventStart()

    try:
      self.WriteEventBody(event_object)
    except errors.NoFormatterFound:
      logging.error(
          u'Unable to retrieve formatter for event object: {0:s}:'.format(
              event_object.GetString()))

    self.WriteEventEnd()

  @abc.abstractmethod
  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """

  def WriteEventEnd(self):
    """Writes the end of an event object to the output.

    Can be used for post-processing or output after an individual event object
    has been written, such as writing closing XML tags, etc.
    """
    pass

  def WriteEventStart(self):
    """Writes the start of an event object to the output.

    Can be used for pre-processing or output before an individual event object
    has been written, such as writing opening XML tags, etc.
    """
    pass

  def WriteFooter(self):
    """Writes the footer to the output.

    Can be used for post-processing or output after the last event object
    is written, such as writing a file footer.
    """
    pass

  def WriteHeader(self):
    """Writes the header to the output.

    Can be used for pre-processing or output before the first event object
    is written, such as writing a file header.
    """
    pass


# Need to suppress this since these classes do not implement the
# abstract method WriteEventBody, classes that inherit from one of these
# classes need to implement that function.
# pylint: disable=abstract-method
class FileOutputModule(OutputModule):
  """A file-based output module."""

  def __init__(
      self, store, formatter_mediator, filehandle=sys.stdout, config=None,
      filter_use=None):
    """Initializes the output module object.

    Args:
      store: A storage file object (instance of StorageFile) that defines
             the storage.
      formatter_mediator: The formatter mediator object (instance of
                          FormatterMediator).
      filehandle: Optional file-like object that can be written to.
                  The default is sys.stdout.
      config: Optional configuration object, containing config information.
              The default is None.
      filter_use: Optional filter object (instance of FilterObject).
                  The default is None.

    Raises:
      ValueError: if the filehandle value is not supported.
    """
    super(FileOutputModule, self).__init__(
        store, formatter_mediator, config=config, filter_use=filter_use)

    if isinstance(filehandle, basestring):
      open_file_object = open(filehandle, 'wb')

    # Check if the filehandle object has a write method.
    elif hasattr(filehandle, u'write'):
      open_file_object = filehandle

    else:
      raise ValueError(u'Unsupported file handle.')

    self._file_object = OutputFilehandle(self.encoding)
    self._file_object.Open(open_file_object)

  def _WriteLine(self, line):
    """Write a single line to the supplied file-like object.

    Args:
      line: the line of text to write.
    """
    self._file_object.WriteLine(line)

  def Close(self):
    """Closes the output."""
    self._file_object.Close()


class EventBuffer(object):
  """Buffer class for EventObject output processing."""

  MERGE_ATTRIBUTES = ['inode', 'filename', 'display_name']

  def __init__(self, formatter, check_dedups=True):
    """Initialize the EventBuffer.

    This class is used for buffering up events for duplicate removals
    and for other post-processing/analysis of events before being presented
    by the appropriate output module.

    Args:
      formatter: An OutputFormatter object.
      check_dedups: Optional boolean value indicating whether or not the buffer
                    should check and merge duplicate entries or not.
    """
    self._buffer_dict = {}
    self._current_timestamp = 0
    self.duplicate_counter = 0
    self.check_dedups = check_dedups

    self.formatter = formatter
    self.formatter.Open()
    self.formatter.WriteHeader()

  def Append(self, event_object):
    """Append an EventObject into the processing pipeline.

    Args:
      event_object: The EventObject that is being added.
    """
    if not self.check_dedups:
      self.formatter.WriteEvent(event_object)
      return

    if event_object.timestamp != self._current_timestamp:
      self._current_timestamp = event_object.timestamp
      self.Flush()

    key = event_object.EqualityString()
    if key in self._buffer_dict:
      self.JoinEvents(event_object, self._buffer_dict.pop(key))
    self._buffer_dict[key] = event_object

  def Flush(self):
    """Flushes the buffer by sending records to a formatter and prints."""
    if not self._buffer_dict:
      return

    for event_object in self._buffer_dict.values():
      try:
        self.formatter.WriteEvent(event_object)
      except errors.WrongFormatter as exception:
        logging.error(u'Unable to write event: {:s}'.format(exception))

    self._buffer_dict = {}

  def JoinEvents(self, event_a, event_b):
    """Join this EventObject with another one."""
    self.duplicate_counter += 1
    # TODO: Currently we are using the first event pathspec, perhaps that
    # is not the best approach. There is no need to have all the pathspecs
    # inside the combined event, however which one should be chosen is
    # perhaps something that can be evaluated here (regular TSK in favor of
    # an event stored deep inside a VSS for instance).
    for attr in self.MERGE_ATTRIBUTES:
      val_a = set(utils.GetUnicodeString(getattr(event_a, attr, '')).split(';'))
      val_b = set(utils.GetUnicodeString(getattr(event_b, attr, '')).split(';'))
      values_list = list(val_a | val_b)
      values_list.sort() # keeping this consistent across runs helps with diffs
      setattr(event_a, attr, u';'.join(values_list))

    # Special instance if this is a filestat entry we need to combine the
    # description field.
    if getattr(event_a, 'parser', u'') == 'filestat':
      description_a = set(getattr(event_a, 'timestamp_desc', u'').split(';'))
      description_b = set(getattr(event_b, 'timestamp_desc', u'').split(';'))
      descriptions = list(description_a | description_b)
      descriptions.sort()
      if event_b.timestamp_desc not in event_a.timestamp_desc:
        setattr(event_a, 'timestamp_desc', u';'.join(descriptions))

  def End(self):
    """Call the formatter to produce the closing line."""
    self.Flush()

    if self.formatter:
      self.formatter.WriteFooter()
      self.formatter.Close()

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.End()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self


# TODO: replace by output writer.
class OutputFilehandle(object):
  """A simple wrapper for filehandles to make character encoding easier.

  All data is stored as an unicode text internally. However there are some
  issues with clients that try to output unicode text to a non-unicode terminal.
  Therefore a wrapper is created that checks if we are writing to a file, thus
  using the default unicode encoding or if the attempt is to write to the
  terminal, for which the default encoding of that terminal is used to encode
  the text (if possible).
  """

  DEFAULT_ENCODING = 'utf-8'

  def __init__(self, encoding='utf-8'):
    """Initialize the output file handler.

    Args:
      encoding: The default terminal encoding, only used if attempted to write
                to the terminal.
    """
    super(OutputFilehandle, self).__init__()
    self._encoding = encoding
    self._file_object = None
    # An attribute stating whether or not this is STDOUT.
    self._standard_out = False

  def Open(self, filehandle=sys.stdout, path=''):
    """Open a filehandle to an output file.

    Args:
      filehandle: A file-like object that is used to write data to.
      path: If a file like object is not passed in it is possible
            to pass in a path to a file, and a file-like object will be created.
    """
    if path:
      self._file_object = open(path, 'wb')
    else:
      self._file_object = filehandle

    if not hasattr(self._file_object, 'name'):
      self._standard_out = True
    elif self._file_object.name.startswith('<stdout>'):
      self._standard_out = True

  def WriteLine(self, line):
    """Write a single line to the supplied filehandle.

    Args:
      line: the line of text to write.
    """
    if not self._file_object:
      return

    if self._standard_out:
      # Write using preferred user encoding.
      try:
        self._file_object.write(line.encode(self._encoding))
      except UnicodeEncodeError:
        logging.error(
            u'Unable to properly write logline, save output to a file to '
            u'prevent missing data.')
        self._file_object.write(line.encode(self._encoding, 'ignore'))

    else:
      # Write to a file, use unicode.
      self._file_object.write(line.encode(self.DEFAULT_ENCODING))

  def Close(self):
    """Close the filehandle, if applicable."""
    if self._file_object and not self._standard_out:
      self._file_object.close()

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.Close()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self
