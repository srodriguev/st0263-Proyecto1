# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import json
import configparser
import bcrypt
import os
import sys
import socket
import grpc
import requests
import configparser

import grpc
import dataNode_pb2
import dataNode_pb2_grpc


'''
# Obtiene la ruta del directorio raíz del proyecto
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Añade la ruta del directorio Helpers al sys.path
helpers_dir = os.path.join(root_dir, 'Helpers')
sys.path.append(helpers_dir)

# Imprime información de depuración
print("Ruta del directorio raíz:", root_dir)
print("Ruta del directorio Helpers:", helpers_dir)
print("sys.path:", sys.path)

# Intenta importar la función split_file_into_blocks desde fileSplitter
try:
    from Helpers.fileSplitter import split_file_into_blocks
except ModuleNotFoundError as e:
    print("Error al importar fileSplitter:", e)
'''

app = Flask(__name__)

# --- METODOS DE APOYO / HELPERS

def split_file_into_blocks(input_file, output_directory):
    print("Time to divide this file in chunks")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Obtener el nombre del archivo de entrada sin la extensión
    input_filename_without_extension = os.path.splitext(os.path.basename(input_file))[0]

    # Crear la subcarpeta con el mismo nombre que el archivo de entrada
    output_subdirectory = os.path.join(output_directory, input_filename_without_extension)
    if not os.path.exists(output_subdirectory):
        os.makedirs(output_subdirectory)

    block_size = 4 * 1024  # 4KB
    with open(input_file, 'rb') as file:
        block_number = 0
        while True:
            block_data = file.read(block_size)
            if not block_data:
                break
            block_filename = os.path.join(output_subdirectory, f"block_{block_number}")
            with open(block_filename, 'wb') as block_file:
                block_file.write(block_data)
            block_number += 1
    return block_number


def merge_blocks_into_file(blocks_directory, output_file):
    print("Time to put back together the chunks")
    with open(output_file, 'wb') as output:
        block_number = 0
        while True:
            block_filename = os.path.join(blocks_directory, f"block_{block_number}")
            if not os.path.exists(block_filename):
                break
            with open(block_filename, 'rb') as block_file:
                block_data = block_file.read()
                output.write(block_data)
            block_number += 1



# --- METODOS DE COMUNICACION API REST

def register_user(username, password, nameNode_dir, nn_ip, nn_port):
    url = f"http://{nn_ip}:{nn_port}/register"
    data = {
        "username": username,
        "password": password,
        "nameNode_dir": nameNode_dir
    }
    response = requests.post(url, json=data)
    return response.text, response.status_code

def login(nameNode_dir, password, nn_ip, nn_port):
    url = f"http://{nn_ip}:{nn_port}/login"
    data = {
        "nameNode_dir": nameNode_dir,
        "password": password
    }
    response = requests.post(url, json=data)
    return response.text, response.status_code

def logout(nameNode_dir, nn_ip, nn_port):
    url = f"http://{nn_ip}:{nn_port}/logout"
    data = {
        "nameNode_dir": nameNode_dir
    }
    response = requests.post(url, json=data)
    return response.json(), response.status_code


# --- 
#mode = w write, r read
def open_file(file_location, mode, num_blocks, nn_ip, nn_port):
    if mode == 'w':
        url = f"http://{nn_ip}:{nn_port}/openfile"
        data = {
            "file_location": file_location,
            "mode": mode,
            "num_blocks": num_blocks
        }
        response = requests.post(url, json=data)
        return response.json(), response.status_code
    else:
        return {"message": "El modo de apertura debe ser 'w' para escritura. a r para lectura"}, 400

# --- METODOS DE GPRC

def download_block(file_name, block_name):
    # Establecer conexión con el servidor DataNode
    with grpc.insecure_channel('127.0.0.1:50051') as channel:
        # Crear un cliente gRPC
        stub = dataNode_pb2_grpc.DataNodeServiceStub(channel)
        # Crear la solicitud de descarga de bloque
        request = dataNode_pb2.DownloadBlockRequest(file_name=file_name, block_name=block_name)
        # Llamar al método remoto
        response = stub.DownloadBlock(request)
        # Procesar la respuesta
        if response:
            with open(os.path.join('downloads', block_name), 'wb') as file:
                file.write(response.block_data)
            print(f"Block '{block_name}' downloaded successfully.")
        else:
            print(f"Failed to download block '{block_name}'.")

def upload_block(file_name, block_name):
    # Leer el contenido del bloque a cargar
    with open(os.path.join('uploads', block_name), 'rb') as file:
        block_data = file.read()
    # Establecer conexión con el servidor DataNode
    with grpc.insecure_channel('127.0.0.1:50051') as channel:
        # Crear un cliente gRPC
        stub = dataNode_pb2_grpc.DataNodeServiceStub(channel)
        # Crear la solicitud de carga de bloque
        request = dataNode_pb2.UploadBlockRequest(file_name=file_name, block_name=block_name, block_data=block_data)
        # Llamar al método remoto
        response = stub.UploadBlock(request)
        # Procesar la respuesta
        print(response.message)

       
    

# --- LOOP PRINCIPAL

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('../config.ini')

    #config propia
    username = config['Client']['username']
    password = config['Client']['password']
    ip = config['Client']['ip']
    port = config['Client']['port']
    local_files = config['Client']['local_files']
    block_output = config['Client']['block_output']

    nameNode_dir = f"{ip}:{port}"

    #config NameNode
    nn_ip = config['NameNode']['ip']
    nn_port = config['NameNode']['port']


    #Prueba de cortar y descortar los archivos txt
    num_blocks = split_file_into_blocks("./local_files/LoremIpsum.txt", block_output)
    merge_blocks_into_file("./block_output/LoremIpsum", "./downloaded_files/LoremIpsum1.txt")

    # Llama a la función para registrar un usuario
    registration_result, status_code = register_user(username, password, nameNode_dir, nn_ip, nn_port)
    print(f"Registro: {registration_result}, Código de estado: {status_code}")

    # Llama a la función para iniciar sesión
    login_result, status_code = login(nameNode_dir, password, nn_ip, nn_port)
    print(f"Inicio de sesión: {login_result}, Código de estado: {status_code}")

    # Llama a la función para cerrar la sesión
    logout_result, status_code = logout(nameNode_dir, nn_ip, nn_port)
    print(f"Cierre de sesión: {logout_result['message']}, Código de estado: {status_code}")

    print("grpc read test")
    download_block('example.txt', 'block1')
    # Llamar al método read_chunk

    print("grpc create test")
    upload_block('example.txt', 'block2')
    # Llamar al método create_chunk

    app.run(host=ip, debug=True, port=int(port))


