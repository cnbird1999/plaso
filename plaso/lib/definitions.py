# -*- coding: utf-8 -*-
"""The definitions."""

SERIALIZER_FORMAT_JSON = u'json'
SERIALIZER_FORMAT_PROTOBUF = u'proto'

SERIALIZER_FORMATS = frozenset([
    SERIALIZER_FORMAT_JSON, SERIALIZER_FORMAT_PROTOBUF])

RESERVED_VARIABLE_NAMES = frozenset([
    u'body',
    u'data_type',
    u'display_name',
    u'filename',
    u'hostname',
    u'http_headers',
    u'inode',
    u'mapped_files',
    u'metadata',
    u'offset',
    u'parser',
    u'pathspec',
    u'query',
    u'regvalue',
    u'source_long',
    u'source_short',
    u'store_index',
    u'store_number',
    u'tag',
    u'timestamp',
    u'timestamp_desc',
    u'timezone',
    u'username',
    u'uuid'])

OS_LINUX = u'Linux'
OS_MACOSX = u'MacOSX'
# TODO: keeping this compatible with the existing code for now.
# Rename None to Unknown in the future.
OS_UNKNOWN = u'None'
OS_WINDOWS = u'Windows'
