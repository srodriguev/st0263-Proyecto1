import grpc
import dataNode_pb2
import dataNode_pb2_grpc

def test_grpc_method():
    # Crea un canal gRPC para comunicarse con el servidor
    channel = grpc.insecure_channel('localhost:50051')

    # Crea un cliente gRPC
    stub = dataNode_pb2_grpc.DataNodeStub(channel)

    # Prepara los datos para enviar al servidor
    request = dataNode_pb2.MyRequest()
    request.field = 'value'

    # Envía la solicitud al servidor llamando al método gRPC apropiado
    response = stub.MyMethod(request)

    # Procesa la respuesta recibida del servidor
    print(response.field)

if __name__ == '__main__':
    test_grpc_method()