# -*- coding: utf-8 -*-
"""The extraction front-end."""

import logging
import os
import pdb
import traceback

from dfvfs.resolver import context

import plaso
from plaso import parsers   # pylint: disable=unused-import
from plaso import hashers   # pylint: disable=unused-import
from plaso.engine import single_process
from plaso.engine import utils as engine_utils
from plaso.frontend import storage_media_frontend
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import storage
from plaso.lib import timelib
from plaso.multi_processing import multi_process
from plaso.hashers import manager as hashers_manager
from plaso.parsers import manager as parsers_manager

import pytz


class ExtractionFrontend(storage_media_frontend.StorageMediaFrontend):
  """Class that implements an extraction front-end."""

  _DEFAULT_PROFILING_SAMPLE_RATE = 1000

  # Approximately 250 MB of queued items per worker.
  _DEFAULT_QUEUE_SIZE = 125000

  _BYTES_IN_A_MIB = 1024 * 1024

  def __init__(self):
    """Initializes the front-end object."""
    super(ExtractionFrontend, self).__init__()
    self._buffer_size = 0
    self._collection_process = None
    self._collector = None
    self._debug_mode = False
    self._enable_profiling = False
    self._engine = None
    self._filter_expression = None
    self._filter_object = None
    self._mount_path = None
    self._old_preprocess = False
    self._operating_system = None
    self._output_module = None
    self._parser_names = None
    self._preprocess = False
    self._process_archive_files = False
    self._profiling_sample_rate = self._DEFAULT_PROFILING_SAMPLE_RATE
    self._profiling_type = u'all'
    self._queue_size = self._DEFAULT_QUEUE_SIZE
    self._single_process_mode = False
    self._show_worker_memory_information = False
    self._storage_file_path = None
    self._text_prepend = None

  def _CheckStorageFile(self, storage_file_path):
    """Checks if the storage file path is valid.

    Args:
      storage_file_path: The path of the storage file.

    Raises:
      BadConfigOption: if the storage file path is invalid.
    """
    if os.path.exists(storage_file_path):
      if not os.path.isfile(storage_file_path):
        raise errors.BadConfigOption(
            u'Storage file: {0:s} already exists and is not a file.'.format(
                storage_file_path))
      logging.warning(u'Appending to an already existing storage file.')

    dirname = os.path.dirname(storage_file_path)
    if not dirname:
      dirname = '.'

    # TODO: add a more thorough check to see if the storage file really is
    # a plaso storage file.

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          u'Unable to write to storage file: {0:s}'.format(storage_file_path))

  # Note that this function is not called by the normal termination.
  def _CleanUpAfterAbort(self):
    """Signals the tool to stop running nicely after an abort."""
    if self._single_process_mode and self._debug_mode:
      logging.warning(u'Running in debug mode, set up debugger.')
      pdb.post_mortem()
      return

    if self._collector:
      logging.warning(u'Stopping collector.')
      self._collector.SignalEndOfInput()

    if self._engine:
      self._engine.SignalAbort()

  def _GetParserFilterPreset(self, os_guess=u'', os_version=u''):
    """Determines the parser filter preset.

    Args:
      os_guess: optional string containing the operating system guessed by
                the preprocessing. The default is an empty string.
      os_version: optional string containing the operating system version
                  determined by the preprocessing. The default is an empty
                  string.

    Returns:
      The parser filter string or None.
    """
    # TODO: Make this more sane. Currently we are only checking against
    # one possible version of Windows, and then making the assumption if
    # that is not correct we default to Windows 7. Same thing with other
    # OS's, no assumption or checks are really made there.
    # Also this is done by default, and no way for the user to turn off
    # this behavior, need to add a parameter to the frontend that takes
    # care of overwriting this behavior.

    parser_filter_string = None

    if not parser_filter_string and os_version:
      os_version = os_version.lower()

      # TODO: Improve this detection, this should be more 'intelligent', since
      # there are quite a lot of versions out there that would benefit from
      # loading up the set of 'winxp' parsers.
      if u'windows xp' in os_version:
        parser_filter_string = u'winxp'
      elif u'windows server 2000' in os_version:
        parser_filter_string = u'winxp'
      elif u'windows server 2003' in os_version:
        parser_filter_string = u'winxp'

    if not parser_filter_string and os_guess:
      if os_guess == definitions.OS_LINUX:
        parser_filter_string = u'linux'
      elif os_guess == definitions.OS_MACOSX:
        parser_filter_string = u'macosx'

    return parser_filter_string

  def _InitializeMultiProcessModeEngine(self):
    """Initializes the multi process mode engine.

    Returns:
      The engine object (instance of Engine).
    """
    engine = multi_process.MultiProcessEngine(
        maximum_number_of_queued_items=self._queue_size)

    engine.SetEnableDebugOutput(self._debug_mode)
    engine.SetEnableProfiling(
        self._enable_profiling,
        profiling_sample_rate=self._profiling_sample_rate,
        profiling_type=self._profiling_type)
    engine.SetProcessArchiveFiles(self._process_archive_files)

    if self._filter_object:
      engine.SetFilterObject(self._filter_object)

    if self._mount_path:
      engine.SetMountPath(self._mount_path)

    if self._text_prepend:
      engine.SetTextPrepend(self._text_prepend)
    # TODO: add support to handle multiple partitions.
    engine.SetSource(
        self.GetSourcePathSpec(), resolver_context=self._resolver_context)

    return engine

  def _InitializeSingleProcessModeEngine(self):
    """Initializes the single process mode engine.

    Returns:
      The engine object (instance of Engine).
    """
    engine = single_process.SingleProcessEngine(self._queue_size)
    engine.SetEnableDebugOutput(self._debug_mode)
    engine.SetEnableProfiling(
        self._enable_profiling,
        profiling_sample_rate=self._profiling_sample_rate,
        profiling_type=self._profiling_type)
    engine.SetProcessArchiveFiles(self._process_archive_files)

    if self._filter_object:
      engine.SetFilterObject(self._filter_object)

    if self._mount_path:
      engine.SetMountPath(self._mount_path)

    if self._text_prepend:
      engine.SetTextPrepend(self._text_prepend)

    # TODO: add support to handle multiple partitions.
    engine.SetSource(
        self.GetSourcePathSpec(), resolver_context=self._resolver_context)

    return engine

  def _PreprocessSource(self):
    """Preprocesses the source.

    Returns:
      The preprocessing object (instance of PreprocessObject).
    """
    pre_obj = None

    if self._old_preprocess and os.path.isfile(self._storage_file_path):
      # Check if the storage file contains a preprocessing object.
      try:
        with storage.StorageFile(
            self._storage_file_path, read_only=True) as store:
          storage_information = store.GetStorageInformation()
          if storage_information:
            logging.info(u'Using preprocessing information from a prior run.')
            pre_obj = storage_information[-1]
            self._preprocess = False
      except IOError:
        logging.warning(u'Storage file does not exist, running preprocess.')

    logging.debug(u'Starting preprocessing.')

    if (self._preprocess and
        (self.SourceIsDirectory() or self.SourceIsStorageMediaImage())):
      try:
        self._engine.PreprocessSource(
            self._operating_system, resolver_context=self._resolver_context)
      except IOError as exception:
        logging.error(u'Unable to preprocess with error: {0:s}'.format(
            exception))
        return

    logging.debug(u'Preprocessing done.')

    # TODO: Remove the need for direct access to the pre_obj in favor
    # of the knowledge base.
    pre_obj = getattr(self._engine.knowledge_base, u'_pre_obj', None)

    if not pre_obj:
      pre_obj = event.PreprocessObject()

    return pre_obj

  # TODO: have the frontend fill collecton information gradually
  # and set it as the last step of preprocessing?
  # Split in:
  # * extraction preferences (user preferences)
  # * extraction settings (actual settings used)
  # * output/storage settings
  # * processing settings
  # * source settings (support more than one source)
  #   * credentials (encryption)
  #   * mount point

  def _PreprocessSetCollectionInformation(
      self, pre_obj, unused_engine, filter_file=None,
      parser_filter_string=None):
    """Sets the collection information as part of the preprocessing.

    Args:
      pre_obj: the preprocess object (instance of PreprocessObject).
      engine: the engine object (instance of BaseEngine).
      filter_file: a path to a file that contains find specifications.
                   The default is None.
      parser_filter_string: optional parser filter string. The default is None.
    """
    collection_information = {}

    # TODO: informational values.
    collection_information[u'version'] = plaso.GetVersion()
    collection_information[u'debug'] = self._debug_mode

    # TODO: extraction preferences:
    if not parser_filter_string:
      parser_filter_string = u'(no list set)'
    collection_information[u'parser_selection'] = parser_filter_string
    collection_information[u'preferred_encoding'] = self.preferred_encoding

    # TODO: extraction info:
    collection_information[u'configured_zone'] = pre_obj.zone
    collection_information[u'parsers'] = self._parser_names
    collection_information[u'preprocess'] = self._preprocess

    if self._filter_expression:
      collection_information[u'filter'] = self._filter_expression

    if filter_file and os.path.isfile(filter_file):
      filters = []
      with open(filter_file, 'rb') as file_object:
        for line in file_object.readlines():
          filters.append(line.rstrip())
      collection_information[u'file_filter'] = u', '.join(filters)

    if self._operating_system:
      collection_information[u'os_detected'] = self._operating_system
    else:
      collection_information[u'os_detected'] = 'N/A'

    # TODO: processing settings:
    collection_information[u'protobuf_size'] = self._buffer_size
    collection_information[u'time_of_run'] = timelib.Timestamp.GetNow()

    if self._single_process_mode:
      collection_information[u'runtime'] = u'single process mode'
    else:
      collection_information[u'runtime'] = u'multi process mode'
      # TODO: retrieve this value from the multi-process engine.
      # refactor engine to set number_of_extraction_workers
      # before ProcessSource.
      collection_information[u'workers'] = 0

    # TODO: output/storage settings:
    collection_information[u'output_file'] = self._storage_file_path

    # TODO: source settings:
    if self.SourceIsDirectory():
      recursive = True
    else:
      recursive = False

    collection_information[u'file_processed'] = self._source_path
    collection_information[u'recursive'] = recursive
    collection_information[u'vss parsing'] = bool(self.vss_stores)

    if self.SourceIsStorageMediaImage():
      collection_information[u'method'] = u'imaged processed'
      collection_information[u'image_offset'] = self.partition_offset
    else:
      collection_information[u'method'] = u'OS collection'

    pre_obj.collection_information = collection_information

  def _PreprocessSetTimezone(self, pre_obj, timezone=pytz.UTC):
    """Sets the timezone as part of the preprocessing.

    Args:
      pre_obj: the previously created preprocessing object (instance of
               PreprocessObject) or None.
      timezone: optional preferred timezone. The default is UTC.
    """
    if not timezone:
      timezone = pytz.UTC

    if hasattr(pre_obj, u'time_zone_str'):
      logging.info(u'Setting timezone to: {0:s}'.format(pre_obj.time_zone_str))

      try:
        pre_obj.zone = pytz.timezone(pre_obj.time_zone_str)

      except pytz.UnknownTimeZoneError:
        if not timezone:
          logging.warning(u'timezone was not properly set, defaulting to UTC')
          timezone = pytz.UTC
        else:
          logging.warning((
              u'Unable to automatically configure timezone falling back '
              u'to preffered timezone value: {0:s}').format(timezone))
        pre_obj.zone = timezone

    else:
      # TODO: shouldn't the user to be able to always override the timezone
      # detection? Or do we need an input sanitization function.
      pre_obj.zone = timezone

    if not getattr(pre_obj, u'zone', None):
      pre_obj.zone = timezone

  def _ProcessSourceMultiProcessMode(
      self, pre_obj, filter_find_specs=None, include_directory_stat=True,
      number_of_worker_processes=0, parser_filter_string=None,
      hasher_names_string=None,
      storage_serializer_format=definitions.SERIALIZER_FORMAT_PROTOBUF):
    """Processes the source with multiple processes.

    Args:
      pre_obj: the preprocess object (instance of PreprocessObject).
      filter_find_specs: optional list of filter find specifications (instances
                         of dfvfs.FindSpec). The default is None.
      include_directory_stat: Boolean value to indicate whether directory
                              stat information should be collected. The default
                              is True.
      number_of_worker_processes: optional number of worker processes.
                                  The default is 0 which represents deterimine
                                  automatically.
      parser_filter_string: optional parser filter string. The default is None.
      hasher_names_string: optional comma separated string of names of
                           hashers to enable. The default is None.
      storage_serializer_format: optional storage serializer format.
                                 The default is protobuf.
    """
    logging.info(u'Starting extraction in multi process mode.')

    resolver_context = context.Context()

    # TODO: create multi process collector.
    self._collector = self._engine.CreateCollector(
        include_directory_stat, vss_stores=self.vss_stores,
        filter_find_specs=filter_find_specs, resolver_context=resolver_context)

    if self._output_module:
      storage_writer = storage.BypassStorageWriter(
          self._engine.storage_queue, self._storage_file_path,
          output_module_string=self._output_module, pre_obj=pre_obj)
    else:
      storage_writer = storage.StorageFileWriter(
          self._engine.storage_queue, self._storage_file_path,
          buffer_size=self._buffer_size, pre_obj=pre_obj,
          serializer_format=storage_serializer_format)

    try:
      self._engine.ProcessSource(
          self._collector, storage_writer,
          parser_filter_string=parser_filter_string,
          hasher_names_string=hasher_names_string,
          number_of_extraction_workers=number_of_worker_processes,
          show_memory_usage=self._show_worker_memory_information)

    except KeyboardInterrupt:
      self._CleanUpAfterAbort()
      raise errors.UserAbort(u'Process source aborted.')

  def _ProcessSourceSingleProcessMode(
      self, pre_obj, filter_find_specs=None, include_directory_stat=True,
      parser_filter_string=None, hasher_names_string=None,
      storage_serializer_format=definitions.SERIALIZER_FORMAT_PROTOBUF):
    """Processes the source in a single process.

    Args:
      pre_obj: the preprocess object (instance of PreprocessObject).
      include_directory_stat: Boolean value to indicate whether directory
                              stat information should be collected. The default
                              is True.
      filter_find_specs: optional list of filter find specifications (instances
                         of dfvfs.FindSpec). The default is None.
      parser_filter_string: optional parser filter string. The default is None.
      hasher_names_string: optional comma separated string of names of
                           hashers to enable. The default is None.
      storage_serializer_format: optional storage serializer format.
                                 The default is protobuf.
    """
    logging.info(u'Starting extraction in single process mode.')

    try:
      self._StartSingleThread(
          pre_obj, filter_find_specs=filter_find_specs,
          include_directory_stat=include_directory_stat,
          parser_filter_string=parser_filter_string,
          hasher_names_string=hasher_names_string,
          storage_serializer_format=storage_serializer_format)

    except Exception as exception:
      # The tool should generally not be run in single process mode
      # for other reasons than to debug. Hence the general error
      # catching.
      logging.error(u'An uncaught exception occurred: {0:s}.\n{1:s}'.format(
          exception, traceback.format_exc()))
      if self._debug_mode:
        pdb.post_mortem()

  def _StartSingleThread(
      self, pre_obj, filter_find_specs=None, include_directory_stat=True,
      parser_filter_string=None, hasher_names_string=None,
      storage_serializer_format=definitions.SERIALIZER_FORMAT_PROTOBUF):
    """Starts everything up in a single process.

    This should not normally be used, since running the tool in a single
    process buffers up everything into memory until the storage is called.

    Just to make it clear, this starts up the collection, completes that
    before calling the worker that extracts all EventObjects and stores
    them in memory. when that is all done, the storage function is called
    to drain the buffer. Hence the tool's excessive use of memory in this
    mode and the reason why it is not suggested to be used except for
    debugging reasons (and mostly to get into the debugger).

    This is therefore mostly useful during debugging sessions for some
    limited parsing.

    Args:
      pre_obj: the preprocess object (instance of PreprocessObject).
      filter_find_specs: optional list of filter find specifications (instances
                         of dfvfs.FindSpec). The default is None.
      include_directory_stat: Boolean value to indicate whether directory
                              stat information should be collected. The default
                              is True.
      parser_filter_string: optional parser filter string. The default is None.
      hasher_names_string: optional comma separated string of names of
                           hashers to enable. The default is None.
      storage_serializer_format: optional storage serializer format.
                                 The default is protobuf.
    """
    self._collector = self._engine.CreateCollector(
        include_directory_stat, vss_stores=self.vss_stores,
        filter_find_specs=filter_find_specs,
        resolver_context=self._resolver_context)

    if self._output_module:
      storage_writer = storage.BypassStorageWriter(
          self._engine.storage_queue, self._storage_file_path,
          output_module_string=self._output_module, pre_obj=pre_obj)
    else:
      storage_writer = storage.StorageFileWriter(
          self._engine.storage_queue, self._storage_file_path,
          buffer_size=self._buffer_size, pre_obj=pre_obj,
          serializer_format=storage_serializer_format)

    try:
      self._engine.ProcessSource(
          self._collector, storage_writer,
          parser_filter_string=parser_filter_string,
          hasher_names_string=hasher_names_string)

    except KeyboardInterrupt:
      self._CleanUpAfterAbort()
      raise errors.UserAbort(u'Process source aborted.')

  def GetSourceFileSystemSearcher(self):
    """Retrieves the file system searcher of the source.

    Returns:
      A tuple of the file system (instance of dfvfs.FileSystem) and
      the file system searcher object (instance of dfvfs.FileSystemSearcher)
    """
    return self._engine.GetSourceFileSystemSearcher(
        resolver_context=self._resolver_context)

  def ProcessSource(
      self, filter_file=None, parser_filter_string=None,
      hasher_names_string=None,
      storage_serializer_format=definitions.SERIALIZER_FORMAT_PROTOBUF,
      timezone=pytz.UTC):
    """Processes the source.

    Args:
      filter_file: a path to a file that contains find specifications.
                   The default is None.
      parser_filter_string: optional parser filter string. The default is None.
      hasher_names_string: optional comma separated string of names of
                           hashers to enable. The default is None.
      storage_serializer_format: optional storage serializer format.
                                 The default is protobuf.
      timezone: optional preferred timezone. The default is UTC.

    Raises:
      SourceScannerError: if the source scanner could not find a supported
                          file system.
      UserAbort: if the user initiated an abort.
    """
    if self.SourceIsDirectory() or self.SourceIsStorageMediaImage():
      # If the source is a directory or a storage media image
      # run pre-processing.
      self._preprocess = True
    else:
      self._preprocess = False

    self._CheckStorageFile(self._storage_file_path)

    if self.SourceIsFile():
      # No need to multi process a single file source.
      self._single_process_mode = True

    if self._single_process_mode:
      self._engine = self._InitializeSingleProcessModeEngine()
    else:
      self._engine = self._InitializeMultiProcessModeEngine()

    pre_obj = self._PreprocessSource()

    if not parser_filter_string:
      guessed_os = getattr(pre_obj, u'guessed_os', u'')
      os_version = getattr(pre_obj, u'osversion', u'')
      parser_filter_string = self._GetParserFilterPreset(
          os_guess=guessed_os, os_version=os_version)

      if parser_filter_string:
        logging.info(u'Parser filter expression changed to: {0:s}'.format(
            parser_filter_string))

    self._parser_names = []
    for _, parser_class in parsers_manager.ParsersManager.GetParsers(
        parser_filter_string=parser_filter_string):
      self._parser_names.append(parser_class.NAME)

    if u'filestat' in self._parser_names:
      include_directory_stat = True
    else:
      include_directory_stat = False

    self._hasher_names = []
    hasher_manager = hashers_manager.HashersManager
    for hasher_name in hasher_manager.GetHasherNamesFromString(
        hasher_names_string=hasher_names_string):
      self._hasher_names.append(hasher_name)

    self._PreprocessSetTimezone(pre_obj, timezone=timezone)

    if filter_file:
      filter_find_specs = engine_utils.BuildFindSpecsFromFile(
          filter_file, pre_obj=pre_obj)
    else:
      filter_find_specs = None

    self._PreprocessSetCollectionInformation(
        pre_obj, self._engine, filter_file=filter_file,
        parser_filter_string=parser_filter_string)

    if self._single_process_mode:
      self._ProcessSourceSingleProcessMode(
          pre_obj, filter_find_specs=filter_find_specs,
          include_directory_stat=include_directory_stat,
          parser_filter_string=parser_filter_string,
          hasher_names_string=hasher_names_string,
          storage_serializer_format=storage_serializer_format)
    else:
      self._ProcessSourceMultiProcessMode(
          pre_obj, filter_find_specs=filter_find_specs,
          include_directory_stat=include_directory_stat,
          parser_filter_string=parser_filter_string,
          hasher_names_string=hasher_names_string,
          storage_serializer_format=storage_serializer_format)

  def SetEnableProfiling(
      self, enable_profiling, profiling_sample_rate=1000,
      profiling_type=u'all'):
    """Enables or disables profiling.

    Args:
      enable_profiling: boolean value to indicate if the profiling should
                        be enabled.
      profiling_sample_rate: optional integer indicating the profiling sample
                             rate. The value contains the number of files
                             processed. The default value is 1000.
      profiling_type: optional profiling type. The default is 'all'.
    """
    self._enable_profiling = enable_profiling
    self._profiling_sample_rate = profiling_sample_rate
    self._profiling_type = profiling_type

  def SetStorageFile(self, storage_file_path):
    """Sets the storage file path.

    Args:
      storage_file_path: The path of the storage file.
    """
    self._storage_file_path = storage_file_path

  def SetStorageSerializer(self, storage_serializer_format):
    """Sets the storage serializer.

    Args:
      storage_serializer_format: String denoting the type of serializer
                                 to be used in the storage. The values
                                 can be either "proto" or "json".
    """
    if storage_serializer_format not in (
        self._EVENT_SERIALIZER_FORMAT_JSON,
        self._EVENT_SERIALIZER_FORMAT_PROTO):
      return

    self._storage_serializer_format = storage_serializer_format

  def SetShowMemoryInformation(self, show_memory=True):
    """Sets a flag telling the worker monitor to show memory information.

    Args:
      show_memory: A boolean (defaults to True) that indicates whether or not
                   the foreman should include memory information as part of
                   the worker monitoring.
    """
    self._show_worker_memory_information = show_memory
