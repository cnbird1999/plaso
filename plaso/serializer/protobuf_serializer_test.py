#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the serializer object implementation using protobuf."""

import unittest

from plaso.lib import event
from plaso.proto import plaso_storage_pb2
from plaso.serializer import protobuf_serializer


class ProtobufAnalysisReportSerializerTest(unittest.TestCase):
  """Tests for the protobuf analysis report serializer object."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    # TODO: add an analysis report test.
    pass

  def testReadSerialized(self):
    """Test the read serialized functionality."""
    # TODO: add an analysis report test.
    pass

  def testWriteSerialized(self):
    """Test the write serialized functionality."""
    # TODO: add an analysis report test.
    pass


class ProtobufEventObjectSerializerTest(unittest.TestCase):
  """Tests for the protobuf event object serializer object."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    proto = plaso_storage_pb2.EventObject()

    proto.data_type = 'test:event2'
    proto.timestamp = 1234124
    proto.timestamp_desc = 'Written'

    serializer = protobuf_serializer.ProtobufEventAttributeSerializer

    proto_attribute = proto.attributes.add()
    serializer.WriteSerializedObject(proto_attribute, 'zero_integer', 0)

    proto_attribute = proto.attributes.add()
    dict_object = {
        'a': 'not b', 'c': 34, 'list': ['sf', 234], 'an': [234, 32]}
    serializer.WriteSerializedObject(proto_attribute, 'my_dict', dict_object)

    proto_attribute = proto.attributes.add()
    tuple_object = (
        'some item', [234, 52, 15], {'a': 'not a', 'b': 'not b'}, 35)
    serializer.WriteSerializedObject(proto_attribute, 'a_tuple', tuple_object)

    proto_attribute = proto.attributes.add()
    list_object = ['asf', 4234, 2, 54, 'asf']
    serializer.WriteSerializedObject(proto_attribute, 'my_list', list_object)

    proto_attribute = proto.attributes.add()
    serializer.WriteSerializedObject(
        proto_attribute, 'unicode_string', u'And I\'m a unicorn.')

    proto_attribute = proto.attributes.add()
    serializer.WriteSerializedObject(proto_attribute, 'integer', 34)

    proto_attribute = proto.attributes.add()
    serializer.WriteSerializedObject(proto_attribute, 'string', 'Normal string')

    proto.uuid = '5a78777006de4ddb8d7bbe12ab92ccf8'

    self._proto_string = proto.SerializeToString()

  def testReadSerialized(self):
    """Test the read serialized functionality."""
    serializer = protobuf_serializer.ProtobufEventObjectSerializer
    event_object = serializer.ReadSerialized(self._proto_string)

    # An integer value containing 0 should get stored.
    self.assertTrue(hasattr(event_object, 'zero_integer'))

    attribute_value = getattr(event_object, 'integer', 0)
    self.assertEquals(attribute_value, 34)

    attribute_value = getattr(event_object, 'my_list', [])
    self.assertEquals(len(attribute_value), 5)

    attribute_value = getattr(event_object, 'string', '')
    self.assertEquals(attribute_value, 'Normal string')

    attribute_value = getattr(event_object, 'unicode_string', u'')
    self.assertEquals(attribute_value, u'And I\'m a unicorn.')

    attribute_value = getattr(event_object, 'a_tuple', ())
    self.assertEquals(len(attribute_value), 4)

  def testWriteSerialized(self):
    """Test the write serialized functionality."""
    event_object = event.EventObject()

    event_object.data_type = 'test:event2'
    event_object.timestamp = 1234124
    event_object.timestamp_desc = 'Written'
    # Prevent the event object for generating its own UUID.
    event_object.uuid = '5a78777006de4ddb8d7bbe12ab92ccf8'

    event_object.empty_string = u''
    event_object.zero_integer = 0
    event_object.integer = 34
    event_object.string = 'Normal string'
    event_object.unicode_string = u'And I\'m a unicorn.'
    event_object.my_list = ['asf', 4234, 2, 54, 'asf']
    event_object.my_dict = {
        'a': 'not b', 'c': 34, 'list': ['sf', 234], 'an': [234, 32]}
    event_object.a_tuple = (
        'some item', [234, 52, 15], {'a': 'not a', 'b': 'not b'}, 35)
    event_object.null_value = None

    serializer = protobuf_serializer.ProtobufEventObjectSerializer
    proto_string = serializer.WriteSerialized(event_object)
    self.assertEquals(proto_string, self._proto_string)

    event_object = serializer.ReadSerialized(proto_string)

    # An empty string should not get stored.
    self.assertFalse(hasattr(event_object, 'empty_string'))

    # A None (or Null) value should not get stored.
    self.assertFalse(hasattr(event_object, 'null_value'))


class ProtobufEventTagSerializerTest(unittest.TestCase):
  """Tests for the protobuf event tag serializer object."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    proto = plaso_storage_pb2.EventTagging()
    proto.store_number = 234
    proto.store_index = 18
    proto.comment = u'My first comment.'
    proto.color = u'Red'
    proto_tag = proto.tags.add()
    proto_tag.value = u'Malware'
    proto_tag = proto.tags.add()
    proto_tag.value = u'Common'

    self._proto_string = proto.SerializeToString()

  def testReadSerialized(self):
    """Test the read serialized functionality."""
    serializer = protobuf_serializer.ProtobufEventTagSerializer
    event_tag = serializer.ReadSerialized(self._proto_string)

    self.assertEquals(event_tag.color, u'Red')
    self.assertEquals(event_tag.comment, u'My first comment.')
    self.assertEquals(event_tag.store_index, 18)
    self.assertEquals(len(event_tag.tags), 2)
    self.assertEquals(event_tag.tags, [u'Malware', u'Common'])

  def testWriteSerialized(self):
    """Test the write serialized functionality."""
    event_tag = event.EventTag()

    event_tag.store_number = 234
    event_tag.store_index = 18
    event_tag.comment = u'My first comment.'
    event_tag.color = u'Red'
    event_tag.tags = [u'Malware', u'Common']

    serializer = protobuf_serializer.ProtobufEventTagSerializer
    proto_string = serializer.WriteSerialized(event_tag)
    self.assertEquals(proto_string, self._proto_string)


class ProtobufPreprocessObjectSerializerTest(unittest.TestCase):
  """Tests for the protobuf preprocess object serializer object."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    # TODO: add a preprocess object test.
    pass

  def testReadSerialized(self):
    """Test the read serialized functionality."""
    # TODO: add a preprocess object test.
    pass

  def testWriteSerialized(self):
    """Test the write serialized functionality."""
    # TODO: add a preprocess object test.
    pass


if __name__ == '__main__':
  unittest.main()
