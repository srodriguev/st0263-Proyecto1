# -*- coding: utf-8 -*-
from flask import Flask, jsonify, send_file, request
import os
import time
import requests
import configparser
import json
from concurrent import futures
import threading
import argparse

import grpc
import dfs_pb2
import dfs_pb2_grpc



app = Flask(__name__)

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
used_capacity = None

# Método para obtener el tiempo de ejecución del DataNode
def uptime():
    return time.time() - app.start_time

#metodo para ver el peso de los archivos en bytes. 
def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            total_size += os.path.getsize(file_path)
    return total_size

# METODOS API REST


@app.route('/healthReport', methods=['GET'])
def health_report():
    uptime_seconds = uptime()
    used_space_now = get_folder_size(files_folder) # en bytes
    available_capacity = float(capacity) - used_space_now
    print("Used space:", used_space_now, "bytes. Available space:", available_capacity, "bytes.")
    response = {
        'status': 'online',
        'address': dataNode_dir,  # Cambiamos esto si es necesario mediante un configfile
        'capacity': capacity,
        'available_capacity': available_capacity,
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

# -- METODOS DE FAILBACK Y FAILOVER DEL NAMENODE

@app.route('/change_namenode', methods=['POST'])
def change_namenode():
    data = request.json
    newLeader_ip = data.get('newLeader_ip')
    newLeader_port = data.get('newLeader_port')

    # actualizando las variables del namenode
    nn_ip = newLeader_ip
    nn_port = newLeader_port
    nameNode_dir = f"{nn_ip}:{nn_port}"

    # Devolver una respuesta
    return jsonify({"message": "NameNode líder actualizado exitosamente"}), 200

# METODO PARA REGISTRARME CON EL NAMENODE

def register_to_namenode():
    attempts = 0
    max_attempts = 3
    retry_interval = 60  # segundos

    while attempts < max_attempts:
        try:
            url = f"http://{nameNode_dir}/registerdatanode"
            uptime_seconds = uptime()
            used_space_now = get_folder_size(files_folder)  # en bytes
            available_capacity = float(capacity) - used_space_now
            print("Used space:", used_space_now, "bytes. Available space:", available_capacity, "bytes.")

            data = {
                'datanode_address': dataNode_dir,
                'uptime_seconds': uptime_seconds,
                'total_space': capacity,
                'available_space': available_capacity,
                'grpc_dir': grpc_dir
            }

            response = requests.post(url, json=data)
            return response.json(), response.status_code

        except requests.RequestException as e:
            print(f"Error al intentar registrarse en el Namenode: {e}")
            attempts += 1
            if attempts < max_attempts:
                print(f"Intento #{attempts}. Reintentando en {retry_interval} segundos...")
                time.sleep(retry_interval)
            else:
                print("Se han agotado los intentos. Esperando 60 segundos antes de volver a intentar.")
                time.sleep(60)
                attempts = 0  # Reiniciar el contador de intentos

    return None, None  # Si todos los intentos fallan

# METODOS GPRC

# --- gprc logic ---

# Implementación de los métodos gRPC

class IOFileServicer(dfs_pb2_grpc.IOFileServicer):
    
    # Método para descargar un bloque de archivo
    def DownloadBlock(self, request, context):
        print("Got a download request")
        file_name = request.file_name
        block_name = request.block_name
        file_path = os.path.join(files_folder, file_name, block_name)
        if not os.path.exists(file_path):
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Block not found")
            return dfs_pb2.DownloadBlockResponse()
        with open(file_path, "r") as file:
            block_data = file.read()
        return dfs_pb2.DownloadBlockResponse(block_data=block_data)
    
    # Método para cargar un nuevo bloque de archivo
    def UploadBlock(self, request, context):
        print("Got an upload request!!!")
        file_name = request.file_name
        block_name = request.block_name
        block_data = request.block_data
    
        print("Creating variables to store block...")
        folder_path = os.path.join(files_folder, file_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        block_path = os.path.join(folder_path, block_name)
        file_name = request.block_name

        print(f"block_path: {block_path}")
        print(f"file_name: {file_name}")
        #print(f"block_data: {block_data}")
        try:
            with open(block_path, "w") as file:
                file.write(block_data)
            return dfs_pb2.UploadBlockResponse(status="File information received successfully.", success=True)
        except Exception as e:
            return dfs_pb2.UploadBlockResponse(status=f"Error: {str(e)}", success=False)





# Configuración y ejecución del servidor gRPC
def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    dfs_pb2_grpc.add_IOFileServicerServicer_to_server(IOFileServicer(), server)
    #server.add_insecure_port('[::]:50051')
    server.add_insecure_port(f'[::]:{grpc_port}')  # Usar el puerto de la configuración
    server.start()
    server.wait_for_termination()


# --- main ----

def run_grpc_server():
    print(f"Starting gRPC server...on: {grpc_port}")
    serve_grpc()

def run_rest_api_server(host, port):
    print(f"Starting REST API server on: {host}:{port}...")
    register_to_namenode()
    print(dataNode_dir)
    app.run(host=host, debug=False, port=int(port))   

# LOOP PRINCIPAL
if __name__ == '__main__':

    # Argumentos de línea de comandos
    # por ejemplo: python namenode.py --host 192.168.1.100 --port 8080 --is_leader False
    parser = argparse.ArgumentParser(description='Start the NameNode.')
    parser.add_argument('--host', default=None, help='Host of the NameNode')
    parser.add_argument('--port', default=None, help='Port of the NameNode')
    parser.add_argument('--grpc_port', default=None, help='Port for gRPC server')


    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('../config.ini')
    id = config['DataNode']['id']
    host = config['DataNode']['ip']
    port = config['DataNode']['port']
    files_folder = config['DataNode']['files_folder']
    datanode_folder = config['DataNode']['datanode_folder']
    capacity = config['DataNode']['capacity']
    available_capacity = config['DataNode']['available_capacity']
    grpc_port = config['DataNode']['grpc_port']

    #config NameNode dir (EL LIDER)
    nn_ip = config['NameNode']['leader_ip']
    nn_port = config['NameNode']['leader_port']
    
    app.start_time = time.time()

    # Actualizar los valores si se proporcionan argumentos en la línea de comandos
    if args.host:
        ip = args.host
    if args.port:
        port = args.port
    if args.grpc_port:
        grpc_port = args.grpc_port

    # Direccion en que corro Flask
    dataNode_dir = f"{host}:{port}"
    # Direccion de mi NameNode leader
    nameNode_dir = f"{nn_ip}:{nn_port}"
    # Direccion RPC
    grpc_dir = f"{host}:{grpc_port}"

    # Creamos los threads
    rest_api_thread = threading.Thread(target=run_rest_api_server, args=(host, port))
    grpc_thread = threading.Thread(target=run_grpc_server)
    
    #Corremos los threads
    rest_api_thread.start()
    time.sleep(2)  # Asegurarse de que el servidor 1 se inicie completamente antes de iniciar el servidor 2
    grpc_thread.start()

    #Nos unimos a los threads
    rest_api_thread.join()
    time.sleep(2) 
    grpc_thread.join()

    #print("Yo voy a correr en: ",dataNode_dir)
    #app.run(host=host, debug=True, port=int(port))

