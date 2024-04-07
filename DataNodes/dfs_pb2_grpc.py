# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import dfs_pb2 as dfs__pb2


class IOFileStub(object):
    """The greeting service definition.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetFile = channel.unary_unary(
                '/dataNode.IOFile/GetFile',
                request_serializer=dfs__pb2.FileRequest.SerializeToString,
                response_deserializer=dfs__pb2.FileResponse.FromString,
                )
        self.SendFileInfo = channel.unary_unary(
                '/dataNode.IOFile/SendFileInfo',
                request_serializer=dfs__pb2.FileInfoRequest.SerializeToString,
                response_deserializer=dfs__pb2.FileInfoResponse.FromString,
                )


class IOFileServicer(object):
    """The greeting service definition.
    """

    def GetFile(self, request, context):
        """Download File
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendFileInfo(self, request, context):
        """Upload File
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_IOFileServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetFile': grpc.unary_unary_rpc_method_handler(
                    servicer.GetFile,
                    request_deserializer=dfs__pb2.FileRequest.FromString,
                    response_serializer=dfs__pb2.FileResponse.SerializeToString,
            ),
            'SendFileInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.SendFileInfo,
                    request_deserializer=dfs__pb2.FileInfoRequest.FromString,
                    response_serializer=dfs__pb2.FileInfoResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'dataNode.IOFile', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class IOFile(object):
    """The greeting service definition.
    """

    @staticmethod
    def GetFile(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataNode.IOFile/GetFile',
            dfs__pb2.FileRequest.SerializeToString,
            dfs__pb2.FileResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendFileInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataNode.IOFile/SendFileInfo',
            dfs__pb2.FileInfoRequest.SerializeToString,
            dfs__pb2.FileInfoResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)