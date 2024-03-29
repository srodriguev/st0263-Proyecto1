# -*- coding: utf-8 -*-

from flask import Flask, jsonify, send_file
import os
import time
import configparser
import json
from concurrent import futures
import threading


import grpc
import dataNode_pb2
import dataNode_pb2_grpc

app = Flask(__name__)

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

# Método para obtener el tiempo de ejecución del DataNode
def uptime():
    return time.time() - app.start_time

# METODOS API REST

@app.route('/healthReport', methods=['GET'])
def health_report():
    uptime_seconds = uptime()
    response = {
        'status': 'online',
        'address': dataNode_dir,  # Cambiamos esto si es necesario mediante un configfile
        'uptime_seconds': uptime_seconds
    }
    return jsonify(response)

@app.route('/stockReport', methods=['GET'])
def stock_report():
    inventory = []

    # Itera sobre los directorios en la carpeta de archivos configurada
    for dirpath, dirnames, filenames in os.walk(files_folder):
        for dirname in dirnames:
            file_info = {}
            file_info['file_name'] = dirname
            file_info['block_names'] = []

            # Itera sobre los archivos en el directorio (chunks)
            for chunk_filename in os.listdir(os.path.join(dirpath, dirname)):
                block_info = {}
                block_info['block_name'] = chunk_filename

                # Obtener el tamaño del bloque
                block_path = os.path.join(dirpath, dirname, chunk_filename)
                block_size = os.path.getsize(block_path)
                block_info['block_size'] = block_size

                file_info['block_names'].append(block_info)

            # Obtener la cantidad de bloques y la fecha de creación
            file_info['num_blocks'] = len(file_info['block_names'])
            file_info['creation_date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

            inventory.append(file_info)

    # Guardar el inventario en un archivo JSON
    inventory_path = './inventory/inventory.json'
    with open(inventory_path, 'w') as f:
        json.dump(inventory, f, indent=4)

    # Devolver el contenido del JSON junto con el mensaje
    return send_file("./inventory/inventory.json", as_attachment=True)


# METODOS GPRC

# --- gprc logic ---

# Implementación de los métodos gRPC
class DataNodeServicer(dataNode_pb2_grpc.DataNodeServicer):

    # Método para descargar un bloque de archivo
    def download_block(self, request, context):
        file_name = request.file_name
        block_name = request.block_name
        file_path = os.path.join(files_folder, file_name, block_name)
        if not os.path.exists(file_path):
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Block not found")
            return dataNode_pb2.DownloadBlockResponse()
        with open(file_path, "rb") as file:
            block_data = file.read()
        return dataNode_pb2.DownloadBlockResponse(block_data=block_data)

    # Método para cargar un nuevo bloque de archivo
    def upload_block(self, request, context):
        file_name = request.file_name
        block_name = request.block_name
        block_data = request.block_data
        folder_path = os.path.join(files_folder, file_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        block_path = os.path.join(folder_path, block_name)
        with open(block_path, "wb") as file:
            file.write(block_data)
        return dataNode_pb2.UploadBlockResponse(message="Block uploaded successfully")

# Configuración y ejecución del servidor gRPC
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    dataNode_pb2_grpc.add_DataNodeServiceServicer_to_server(DataNodeServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

# --- main ----

def run_grpc_server():
    print("Starting gRPC server...")
    serve()

def run_rest_api_server(host, port):
    print(f"Starting REST API server on {host}:{port}...")
    app.run(host=host, debug=True, port=int(port))   

# LOOP PRINCIPAL
if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('../config.ini')
    id = config['DataNode']['id']
    host = config['DataNode']['ip']
    port = config['DataNode']['port']
    files_folder = config['DataNode']['files_folder']
    datanode_folder = config['DataNode']['datanode_folder']
    app.start_time = time.time()

    dataNode_dir = f"{host}:{port}"

    #rest_api_thread = threading.Thread(target=run_rest_api_server, args=(host, port))
    #grpc_thread = threading.Thread(target=run_grpc_server)
    
    #rest_api_thread.start()
    #time.sleep(2)  # Asegurarse de que el servidor gRPC se inicie completamente antes de iniciar el servidor REST API
    #grpc_thread.start()

    #rest_api_thread.join()
    #grpc_thread.join()

    print("app run")
    app.run(host=host, debug=True, port=int(port))

