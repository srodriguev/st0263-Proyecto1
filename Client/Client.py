import grpc
import file_pb2
import file_pb2_grpc

class Client:
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:50051')  # Cambia la dirección y el puerto según tu configuración
        self.name_node_stub = file_pb2_grpc.NameNodeStub(self.channel)
        self.data_node_stub = file_pb2_grpc.DataNodeStub(self.channel)

    def Open(self, filename, mode):
        file_request = file_pb2.FileRequest(filename=filename, mode=mode)
        file_fragments = self.name_node_stub.Open(file_request)
        return file_fragments.fragments

    def ReadFile(self, fragment):
        fragment_stream = self.data_node_stub.ReadFile(fragment)
        data = b''
        for chunk in fragment_stream:
            data += chunk
        return data

# Ejemplo de uso
if __name__ == "__main__":
    client = Client()

    # Abrir el archivo y obtener la lista de fragmentos
    filename = "ejemplo.txt"
    mode = "read"
    fragments = client.Open(filename, mode)

    # Leer cada fragmento y concatenarlos
    for fragment in fragments:
        data = client.ReadFile(fragment)
        print(f"Contenido del fragmento '{fragment.name}':")
        print(data.decode('utf-8'))  # Decodificar los bytes a texto si es necesario
