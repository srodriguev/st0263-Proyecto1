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

import dataNode_pb2
import dataNode_pb2_grpc

import dfs_pb2_grpc
import dfs_pb2

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

def register_user(username, password, client_dir, nn_ip, nn_port):
    url = f"http://{nn_ip}:{nn_port}/register"
    data = {
        "username": username,
        "password": password,
        "peer_ip": client_dir
    }
    response = requests.post(url, json=data)
    return response.text, response.status_code

def login(username, password, nn_ip, nn_port):
    url = f"http://{nn_ip}:{nn_port}/login"
    data = {
        "username": username,
        "peer_ip": client_dir,
        "password": password
    }
    response = requests.post(url, json=data)
    return response.text, response.status_code

def logout(client_dir, nn_ip, nn_port):
    url = f"http://{nn_ip}:{nn_port}/logout"
    data = {
        "peer_ip": client_dir
    }
    response = requests.post(url, json=data)
    return response.json(), response.status_code


# --- 
# METODOS DE LECTURA DE ARCHIVOS

# Método para solicitar el catálogo de archivos
def request_catalog():
    url = f'http://{nameNode_dir}/inventory'
    response = requests.get(url)
    if response.status_code == 200:
        with open('./catalog/catalog.json', 'wb') as f:
            f.write(response.content)
        print("Catálogo descargado exitosamente.")
        print(response.content)
    else:
        print("Error al descargar el catálogo:", response.text)

# Método para solicitar un archivo específico
def request_file(file_name):
    url = f'http://{nameNode_dir}/getfile?file_requested={file_name}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print("Bloques del archivo solicitado:")
        for block in data:
            print(f"Nombre del bloque: {block['block_name']}, URL del bloque: {block['block_url']}")
        return data
    else:
        print("Error al obtener los bloques del archivo:", response.text)


# METODOS DE ESCRITURA DE ARCHIVOS
# Método para enviar la solicitud de asignación de bloques al servidor principal
def write_file(file_name, num_blocks):
    # Construir el JSON con los datos del archivo y el número de bloques
    data = {
        "file_name": file_name,
        "num_blocks": num_blocks
    }

    # URL del servidor principal
    url = f'http://{nameNode_dir}/allocateblocks'

    # Realizar la solicitud POST al servidor principal con los datos JSON
    response = requests.post(url, json=data)

    # Verificar la respuesta del servidor
    if response.status_code == 200:
        block_assignments = response.json()
        print("Asignaciones de bloques recibidas:")
        for block in block_assignments:
            print(f"Nombre del bloque: {block['block_name']}, URL del bloque: {block['block_url']}, DataNode asignado: {block['assigned_datanode']}")
    else:
        print("Error al obtener las asignaciones de bloques:", response.text)

# --- METODOS DE FAILBACK Y FAILOVER DEL NAMENODE
@app.route('/change_namenode', methods=['POST'])
def change_namenode():
    data = request.json
    newLeader_ip = data.get('newLeader_ip')
    newLeader_port = data.get('newLeader_port')

    # Aquí realizar la lógica para actualizar los datos del NameNode
    # Por ejemplo, actualizar las variables de configuración con los nuevos valores
    nn_ip = newLeader_ip
    nn_port = newLeader_port
    nameNode_dir = f"{nn_ip}:{nn_port}"

    # Devolver una respuesta
    return jsonify({"message": "NameNode líder actualizado exitosamente."}), 200


# --- METODOS DE GPRC

def download_block(file_name, block_name):
    # Establecer conexión con el servidor DataNode
    with grpc.insecure_channel('127.0.0.1:50051') as channel:
        # Crear un cliente gRPC
        stub = dfs_pb2_grpc.IOFileStub(channel)
        # Crear la solicitud de descarga de bloque
        request = dfs_pb2.FileRequest(file_name=file_name, block_name=block_name)
        # Llamar al método remoto
        response = stub.GetFile(request)
        # Procesar la respuesta
        if response:
            with open(os.path.join('downloads', block_name), 'wb') as file:
                file.write(response.block_data)
            print(f"Block '{block_name}' downloaded successfully.")
        else:
            print(f"Failed to download block '{block_name}'.")

def upload_block(file_name, block_name):
    # Leer el contenido del bloque a cargar
    with open(os.path.join('block_output/hola/', block_name), 'rb') as file:
        block_data = file.read()
    # Establecer conexión con el servidor DataNode
    with grpc.insecure_channel('127.0.0.1:50051') as channel:
        # Crear un cliente gRPC
        stub = dfs_pb2_grpc.IOFileStub(channel)
        # Crear la solicitud de carga de bloque
        request = dfs_pb2.FileInfoRequest(file_name=file_name, block_name=block_name, block_data=block_data)
        # Llamar al método remoto
        response = stub.SendFileInfo(request)
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

    client_dir = f"{ip}:{port}"

    #config NameNode
    nn_ip = config['NameNode']['leader_ip']
    nn_port = config['NameNode']['leader_port']

    nameNode_dir = f"{nn_ip}:{nn_port}"

    '''print("Bienvenido al cliente CLI para el sistema de archivos distribuidos")
    print("1. Login")
    print("2. Registro")
    choice = input("R: ")
    if choice == 1:
        username = input("Ingresa tu usuario: ")
        password = input("Ingresa tu clave: ")
        register_user(username, password, nn_ip, nn_port)
    elif choice == 2:
        username = input("Ingresa tu usuario: ")
        password = input("Ingresa tu clave: ")
        client_dir = input("Ingresa tu IP: ")
        register_user(username, password, client_dir, nn_ip, nn_port)'''
    
    # Menu
    while True:
        print("1. Ver catalogo")
        print("2. Descargar un archivo")
        print("3. Subir un archivo")
        print("4. Logout")
        print("0. Salir")
        choice_menu = int(input("R: "))
        if choice_menu == 1:
            print("Obteniendo catalogo...")
            request_catalog()
        elif choice_menu == 2:
            file_name = input("Ingresa el nombre del archivo que deseas descargar: ")
            data = request_file(file_name)
            for block in data:
                download_block(file_name, block['block_name'])
        elif choice_menu == 3:
            input_file = input("Ingresa el nombre del archivo: ")
            output_directory = input("Ingrese el nombre de la carpeta donde se guardaran los bloques: ")
            num_blocks = split_file_into_blocks(input_file, output_directory)
            write_file(input_file, num_blocks)
            for block in range(0,num_blocks):
                upload_block(input_file, f"block_{block}")
        elif choice_menu == 4:
            print("Cerrando sesion...")
            logout(client_dir, nn_ip, nn_port)
        elif choice_menu == 0:
            print("Saliendo del cliente...")
            break


    '''
    #Prueba de cortar y descortar los archivos txt
    num_blocks = split_file_into_blocks("./local_files/file/hola.txt", block_output)
    merge_blocks_into_file("./block_output/LoremIpsum", "./downloaded_files/LoremIpsum1.txt")

    # Llama a la función para registrar un usuario
    registration_result, status_code = register_user(username, password, client_dir, nn_ip, nn_port)
    print(f"Registro: {registration_result}, Código de estado: {status_code}")

    # Llama a la función para iniciar sesión
    login_result, status_code = login(username, password, nn_ip, nn_port)
    print(f"Inicio de sesión: {login_result}, Código de estado: {status_code}")

    # Llama a la función para cerrar la sesión
    #logout_result, status_code = logout(nameNode_dir, nn_ip, nn_port)
    #print(f"Cierre de sesión: {logout_result['message']}, Código de estado: {status_code}")

    # Solicitar el catálogo
    request_catalog()

    # Solicitar información sobre un archivo específico (reemplaza 'nombre_del_archivo' con el nombre real del archivo)
    request_file('loremIpsum.txt')

    # ---
    #test de escritura
    #write_file("test_file_99.txt", num_blocks)
    #print("grpc read test")
    #download_block('example.txt', 'block1')
    # Llamar al método read_chunk
    #print("grpc create test")
    #upload_block('example.txt', 'block2')
    # Llamar al método create_chunk

    #app.run(host=ip, debug=True, port=int(port))'''