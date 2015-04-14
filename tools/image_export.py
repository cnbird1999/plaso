#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The image export front-end."""

import argparse
import logging
import os
import sys
import textwrap

from plaso.cli import storage_media_tool
from plaso.frontend import image_export
from plaso.lib import errors


class ImageExportTool(storage_media_tool.StorageMediaTool):
  """Class that implements the image export CLI tool."""

  NAME = u'image_export'
  DESCRIPTION = (
      u'This is a simple collector designed to export files inside an '
      u'image, both within a regular RAW image as well as inside a VSS. '
      u'The tool uses a collection filter that uses the same syntax as a '
      u'targeted plaso filter.')

  EPILOG = u'And that is how you export files, plaso style.'

  _SOURCE_OPTION = u'image'

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader: the input reader (instance of InputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: the output writer (instance of OutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(ImageExportTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._data_location = None
    self._destination_path = None
    self._filter_file = None
    self._front_end = image_export.ImageExportFrontend()
    self._remove_duplicates = True
    self.has_filters = False
    self.list_signature_identifiers = False

  def ListSignatureIdentifiers(self):
    """Lists the signature identifier.

    Raises:
      BadConfigOption: if the data location is invalid.
    """
    if not self._data_location:
      raise errors.BadConfigOption(u'Missing data location.')

    path = os.path.join(self._data_location, u'signatures.conf')
    if not os.path.exists(path):
      raise errors.BadConfigOption(
          u'No such format specification file: {0:s}'.format(path))

    try:
      specification_store = self._ReadSpecificationFile(path)
    except IOError as exception:
      raise errors.BadConfigOption((
          u'Unable to read format specification file: {0:s} with error: '
          u'{1:s}').format(path, exception))

    identifiers = []
    for format_specification in specification_store.specifications:
      identifiers.append(format_specification.identifier)

    self._output_writer.Write(u'Available signature identifiers:\n')
    self._output_writer.Write(
        u'\n'.join(textwrap.wrap(u', '.join(sorted(identifiers)), 79)))
    self._output_writer.Write(u'\n\n')

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      A boolean value indicating the arguments were successfully parsed.
    """
    logging.basicConfig(
        level=logging.INFO, format=u'[%(levelname)s] %(message)s')

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, epilog=self.EPILOG)

    self.AddBasicOptions(argument_parser)

    argument_parser.add_argument(
        u'-d', u'--debug', dest=u'debug', action=u'store_true', default=False,
        help=u'Turn on debugging information.')

    argument_parser.add_argument(
        u'-w', u'--write', action=u'store', dest=u'path', type=unicode,
        metavar=u'PATH', default=u'export', help=(
            u'The directory in which extracted files should be stored.'))

    argument_parser.add_argument(
        u'-f', u'--filter', action=u'store', dest=u'filter', type=unicode,
        metavar=u'FILTER_FILE', help=(
            u'Full path to the file that contains the collection filter, '
            u'the file can use variables that are defined in preprocesing, '
            u'just like any other log2timeline/plaso collection filter.'))

    argument_parser.add_argument(
        u'--data', action=u'store', dest=u'data_location', type=unicode,
        metavar=u'PATH', default=None, help=u'the location of the data files.')

    argument_parser.add_argument(
        u'--date-filter', u'--date_filter', action=u'append', type=unicode,
        dest=u'date_filters', metavar=u'TYPE_START_END', default=None, help=(
            u'Filter based on file entry date and time ranges. This parameter '
            u'is formatted as "TIME_VALUE,START_DATE_TIME,END_DATE_TIME" where '
            u'TIME_VALUE defines which file entry timestamp the filter applies '
            u'to e.g. atime, ctime, crtime, bkup, etc. START_DATE_TIME and '
            u'END_DATE_TIME define respectively the start and end of the date '
            u'time range. A date time range requires at minimum start or end '
            u'to time of the boundary and END defines the end time. Both '
            u'timestamps be set. The date time values are formatted as: '
            u'YYYY-MM-DD hh:mm:ss.######[+-]##:## Where # are numeric digits '
            u'ranging from 0 to 9 and the seconds fraction can be either 3 '
            u'or 6 digits. The time of day, seconds fraction and timezone '
            u'offset are optional. The default timezone is UTC. E.g. "atime, '
            u'2013-01-01 23:12:14, 2013-02-23". This parameter can be repeated '
            u'as needed to add additional date date boundaries, eg: once for '
            u'atime, once for crtime, etc.'))

    argument_parser.add_argument(
        u'-x', u'--extensions', dest=u'extensions_string', action=u'store',
        type=unicode, metavar=u'EXTENSIONS', help=(
            u'Filter based on file name extensions. This option accepts '
            u'multiple multiple comma separated values e.g. "csv,docx,pst".'))

    argument_parser.add_argument(
        u'--names', dest=u'names_string', action=u'store',
        type=str, metavar=u'NAMES', help=(
            u'If the purpose is to find all files given a certain names '
            u'this options should be used. This option accepts a comma '
            u'separated string denoting all file names, eg: -x '
            u'"NTUSER.DAT,UsrClass.dat".'))

    argument_parser.add_argument(
        u'--signatures', dest=u'signature_identifiers', action=u'store',
        type=unicode, metavar=u'IDENTIFIERS', help=(
            u'Filter based on file format signature identifiers. This option '
            u'accepts multiple comma separated values e.g. "esedb,lnk". '
            u'Use "list" to show an overview of the supported file format '
            u'signatures.'))

    argument_parser.add_argument(
        u'--include_duplicates', dest=u'include_duplicates',
        action=u'store_true', default=False, help=(
            u'If extraction from VSS is enabled, by default a digest hash '
            u'is calcuted for each file. These hases are compared to the '
            u'previously exported files and duplicates are skipped. Use '
            u'this option to include duplicate files in the export.'))

    self.AddStorageMediaImageOptions(argument_parser)
    self.AddVssProcessingOptions(argument_parser)

    argument_parser.add_argument(
        u'image', nargs='?', action=u'store', metavar=u'IMAGE', default=None,
        type=unicode, help=(
            u'The full path to the image file that we are about to extract '
            u'files from, it should be a raw image or another image that '
            u'plaso supports.'))

    try:
      options = argument_parser.parse_args()
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write(u'')
      self._output_writer.Write(argument_parser.format_help())
      return False

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      logging.error(u'{0:s}'.format(exception))

      self._output_writer.Write(u'')
      self._output_writer.Write(argument_parser.format_help())

      return False

    return True

  def ParseOptions(self, options):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_option: optional name of the source option. The default is source.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(ImageExportTool, self).ParseOptions(options)

    format_str = u'%(asctime)s [%(levelname)s] %(message)s'

    debug = getattr(options, u'debug', False)
    if debug:
      logging.basicConfig(level=logging.DEBUG, format=format_str)
    else:
      logging.basicConfig(level=logging.INFO, format=format_str)

    self._destination_path = getattr(options, u'path', u'export')

    filter_file = getattr(options, u'filter', None)
    if filter_file and not os.path.isfile(filter_file):
      raise errors.BadConfigOption(
          u'Unable to proceed, filter file: {0:s} does not exist.'.format(
              filter_file))

    self._filter_file = filter_file

    if (getattr(options, u'no_vss', False) or
        getattr(options, u'include_duplicates', False)):
      self._remove_duplicates = False

    # TODO: move data location code to a location shared with psort.
    data_location = getattr(options, u'data_location', None)
    if not data_location:
      # Determine if we are running from the source directory.
      data_location = os.path.dirname(__file__)
      data_location = os.path.dirname(data_location)
      data_location = os.path.join(data_location, u'data')

      if not os.path.exists(data_location):
        # Otherwise determine if there is shared plaso data location.
        data_location = os.path.join(sys.prefix, u'share', u'plaso')

      if not os.path.exists(data_location):
        logging.warning(u'Unable to automatically determine data location.')
        data_location = None

    self._data_location = data_location

    date_filters = getattr(options, u'date_filters', None)
    try:
      self._front_end.ParseDateFilters(date_filters)
    except ValueError as exception:
      raise errors.BadConfigOption(exception)

    extensions_string = getattr(options, u'extensions_string', None)
    self._front_end.ParseExtensionsString(extensions_string)

    names_string = getattr(options, u'names_string', None)
    self._front_end.ParseNamesString(names_string)

    signature_identifiers = getattr(options, u'signature_identifiers', None)
    if signature_identifiers == u'list':
      self.list_signature_identifiers = True
    else:
      try:
        self._frontend.ParseSignatureIdentifiers(
            self._data_location, signature_identifiers)
      except (IOError, ValueError) as exception:
        raise errors.BadConfigOption(exception)

    self.has_filters = self._frontend.HasFilters()

  def PrintFilterCollection(self):
    """Prints the filter collection."""
    self._front_end.PrintFilterCollection(self._output_writer)

  def ProcessSource(self):
    """Processes the source.

    Raises:
      SourceScannerError: if the source scanner could not find a supported
                          file system.
      UserAbort: if the user initiated an abort.
    """
    self._front_end.ScanSource(
        self._source_path, partition_number=self._partition_number,
        partition_offset=self._partition_offset, enable_vss=self._process_vss,
        vss_stores=self._vss_stores)

    logging.info(u'Processing started.')
    self._front_end.ProcessSource(
        self._destination_path, filter_file=self._filter_file,
        remove_duplicates=self._remove_duplicates)
    logging.info(u'Processing completed.')


def Main():
  """The main function."""
  tool = ImageExportTool()

  if not tool.ParseArguments():
    return False

  if tool.list_signature_identifiers:
    tool.ListSignatureIdentifiers()
    return True

  if not tool.has_filters:
    logging.warning(u'No filter defined exporting all files.')

  # TODO: print more status information like PrintOptions.
  tool.PrintFilterCollection()

  try:
    tool.ProcessSource()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning(u'Aborted by user.')
    return False

  except errors.SourceScannerError as exception:
    logging.warning((
        u'Unable to scan for a supported filesystem with error: {0:s}\n'
        u'Most likely the image format is not supported by the '
        u'tool.').format(exception))
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
