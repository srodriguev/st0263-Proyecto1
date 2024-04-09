# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import dfs_pb2 as dfs__pb2


class IOFileServicerStub(object):
    """The file service definition.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.DownloadBlock = channel.unary_unary(
                '/IOFileServicer/DownloadBlock',
                request_serializer=dfs__pb2.DownloadBlockRequest.SerializeToString,
                response_deserializer=dfs__pb2.DownloadBlockResponse.FromString,
                )
        self.UploadBlock = channel.unary_unary(
                '/IOFileServicer/UploadBlock',
                request_serializer=dfs__pb2.UploadBlockRequest.SerializeToString,
                response_deserializer=dfs__pb2.UploadBlockResponse.FromString,
                )


class IOFileServicerServicer(object):
    """The file service definition.
    """

    def DownloadBlock(self, request, context):
        """Download Block
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UploadBlock(self, request, context):
        """Upload Block
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_IOFileServicerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'DownloadBlock': grpc.unary_unary_rpc_method_handler(
                    servicer.DownloadBlock,
                    request_deserializer=dfs__pb2.DownloadBlockRequest.FromString,
                    response_serializer=dfs__pb2.DownloadBlockResponse.SerializeToString,
            ),
            'UploadBlock': grpc.unary_unary_rpc_method_handler(
                    servicer.UploadBlock,
                    request_deserializer=dfs__pb2.UploadBlockRequest.FromString,
                    response_serializer=dfs__pb2.UploadBlockResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'IOFileServicer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class IOFileServicer(object):
    """The file service definition.
    """

    @staticmethod
    def DownloadBlock(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/IOFileServicer/DownloadBlock',
            dfs__pb2.DownloadBlockRequest.SerializeToString,
            dfs__pb2.DownloadBlockResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UploadBlock(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/IOFileServicer/UploadBlock',
            dfs__pb2.UploadBlockRequest.SerializeToString,
            dfs__pb2.UploadBlockResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
