# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: dataNode.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0e\x64\x61taNode.proto\x12\x08\x64\x61taNode\"=\n\x14\x44ownloadBlockRequest\x12\x11\n\tfile_name\x18\x01 \x01(\t\x12\x12\n\nblock_name\x18\x02 \x01(\t\"+\n\x15\x44ownloadBlockResponse\x12\x12\n\nblock_data\x18\x01 \x01(\x0c\"O\n\x12UploadBlockRequest\x12\x11\n\tfile_name\x18\x01 \x01(\t\x12\x12\n\nblock_name\x18\x02 \x01(\t\x12\x12\n\nblock_data\x18\x03 \x01(\x0c\"&\n\x13UploadBlockResponse\x12\x0f\n\x07message\x18\x01 \x01(\t2\xaf\x01\n\x0f\x44\x61taNodeService\x12P\n\rDownloadBlock\x12\x1e.dataNode.DownloadBlockRequest\x1a\x1f.dataNode.DownloadBlockResponse\x12J\n\x0bUploadBlock\x12\x1c.dataNode.UploadBlockRequest\x1a\x1d.dataNode.UploadBlockResponse2\xb0\x01\n\x10\x44\x61taNodeServicer\x12P\n\rDownloadBlock\x12\x1e.dataNode.DownloadBlockRequest\x1a\x1f.dataNode.DownloadBlockResponse\x12J\n\x0bUploadBlock\x12\x1c.dataNode.UploadBlockRequest\x1a\x1d.dataNode.UploadBlockResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'dataNode_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_DOWNLOADBLOCKREQUEST']._serialized_start=28
  _globals['_DOWNLOADBLOCKREQUEST']._serialized_end=89
  _globals['_DOWNLOADBLOCKRESPONSE']._serialized_start=91
  _globals['_DOWNLOADBLOCKRESPONSE']._serialized_end=134
  _globals['_UPLOADBLOCKREQUEST']._serialized_start=136
  _globals['_UPLOADBLOCKREQUEST']._serialized_end=215
  _globals['_UPLOADBLOCKRESPONSE']._serialized_start=217
  _globals['_UPLOADBLOCKRESPONSE']._serialized_end=255
  _globals['_DATANODESERVICE']._serialized_start=258
  _globals['_DATANODESERVICE']._serialized_end=433
  _globals['_DATANODESERVICER']._serialized_start=436
  _globals['_DATANODESERVICER']._serialized_end=612
# @@protoc_insertion_point(module_scope)
