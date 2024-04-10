# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, send_file
import json
import os
import sys
import time
import bcrypt
import socket
import requests
import threading
import argparse
import configparser

import grpc
import dfs_pb2
import dfs_pb2_grpc


app = Flask(__name__)

# --- METODOS DE APOYO / HELPERS

# corta un archivo en bloques
def split_file_into_blocks(input_file, output_directory):
    print("Time to divide this file into chunks")
    
    # Completar la ruta de entrada con la variable local_files si no es una ruta absoluta
    if not os.path.isabs(input_file):
        input_file = os.path.join(local_files, input_file)
    
    # Revisar que la ruta donde guardar los bloques exista, y crearla si no existe
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    try:
        # Obtener el nombre del archivo de entrada con la extensión
        input_filename_with_extension = os.path.basename(input_file)

        # Crear la subcarpeta con el mismo nombre que el archivo de entrada
        output_subdirectory = os.path.join(output_directory, f"{input_filename_with_extension}")
        if not os.path.exists(output_subdirectory):
            os.makedirs(output_subdirectory)

        block_size = 4 * 1024  # 4KB
        with open(input_file, 'rb') as file:
            block_number = 1  # Iniciar desde 1 en lugar de 0 !!
            while True: 
                block_data = file.read(block_size)
                if not block_data:
                    break
                block_filename = os.path.join(output_subdirectory, f"block{block_number}")
                print(f"block number: {block_number}")
                with open(block_filename, 'wb') as block_file:
                    block_file.write(block_data)
                block_number += 1
        return block_number
    except FileNotFoundError:
        print("File not found.")
        return None

#combina los bloques en 1 archivo.
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
    else:
        print("Error al obtener los bloques del archivo:", response.text)


# METODOS DE ESCRITURA DE ARCHIVOS

#Helper para hacer los llamados rpc para cada bloquecito
def process_block_assignments(file_name, block_assignments):
    for block in block_assignments:
        block_name = block['block_name']
        block_url = block['block_url']
        flask_dir = block['flask_dir']
        grpc_dir = block['grpc_dir']
        assigned_datanode = block['assigned_datanode']
        print(f"Inside procblockass: {file_name}, {block_name}, {grpc_dir}")
        #UploadBlock("file_01.txt", 'chunk1', "127.0.0.1:50051")
        UploadBlock(file_name, block_name, grpc_dir)
        
# Método para enviar la solicitud de asignación de bloques al servidor principal
def upload_request(file_name, num_blocks):
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

        # Llamar al método para procesar las asignaciones de bloques
        process_block_assignments(file_name, block_assignments)
    else:
        print("Error al obtener las asignaciones de bloques:", response.text)

# --- METODOS DE FAILBACK Y FAILOVER DEL NAMENODE

# recibe la solicitud de cambiar el namenode al reemplazo (failover)       
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

def UploadBlock(file_name, block_name, datanode_server_url):
    # Crea un canal gRPC para la comunicación con el servidor
    with grpc.insecure_channel(datanode_server_url) as channel:
        # Crea un cliente para el servicio gRPC
        stub = dfs_pb2_grpc.IOFileServicerStub(channel)
        
        # Construye la ruta del bloque
        block_path = os.path.join(block_output, file_name, block_name)
        print(f"block path: {block_path}")
        
        # Verifica si el bloque existe
        if not os.path.exists(block_path):
            print(f"Block not found.Adress searched for: {block_path}")
            return
        
        # Lee los datos del bloque
        with open(block_path, "rb") as file:
            block_data = file.read()
        
        # Crea una solicitud para cargar un nuevo bloque de archivo
        print("Creating the grpc request...")
        request = dfs_pb2.UploadBlockRequest(file_name=file_name, block_name=block_name, block_data=block_data)
        
        print("Assigning response from server...")
        # Envía la solicitud al servidor gRPC
        response = stub.UploadBlock(request)
        
        print("Manage response success or failure...")
        # Maneja la respuesta del servidor
        if response.success:
            print("Upload successful.")
        else:
            print("Upload failed.")

def DownloadBlock(file_name, block_name, datanode_rpc_url):
    # Crea un canal gRPC para la comunicación con el servidor
    with grpc.insecure_channel(datanode_rpc_url) as channel:
        # Crea un cliente para el servicio gRPC
        stub = dfs_pb2_grpc.IOFileServicerStub(channel)
        
        # Crea una solicitud de descarga de un bloque de archivo
        request = dfs_pb2.DownloadBlockRequest(file_name=file_name, block_name=block_name)
        
        # Envía la solicitud al servidor gRPC
        response = stub.DownloadBlock(request)
        
        # Maneja la respuesta del servidor
        if response.block_data:
            print("Downloaded data:", response.block_data)
        else:
            print("Download failed.")



# --- LOOP PRINCIPAL


def main_menu():
    print("Bienvenido al cliente CLI para el sistema de archivos distribuidos")
    print("1. Login")
    print("2. Registro")
    choice = input("R: ")
    if choice == '1':
        print(nn_ip, nn_port)
        username = input("Ingresa tu usuario: ")
        password = input("Ingresa tu clave: ")
        login(username, password, nn_ip, nn_port)
    elif choice == '2':
        username = input("Ingresa tu usuario: ")
        password = input("Ingresa tu clave: ")
        register_user(username, password, client_dir, nn_ip, nn_port)

    # Menú
    while True:
        print("1. Ver catálogo")
        print("2. Descargar un archivo")
        print("3. Subir un archivo")
        print("4. Logout")
        print("0. Salir")
        choice_menu = input("R: ")
        if choice_menu == '1':
            print("Obteniendo catálogo...")
            request_catalog()
        elif choice_menu == '2':
            file_name = input("Ingresa el nombre del archivo que deseas descargar: ")
            data = request_file(file_name)
            for block in data:
                DownloadBlock(file_name, block['block_name'])
        elif choice_menu == '3':
            input_file = input("Ingresa el nombre del archivo: ")
            num_blocks = split_file_into_blocks(input_file, block_output)
            upload_request(input_file, num_blocks)
        elif choice_menu == '4':
            print("Cerrando sesión...")
            logout(client_dir, nn_ip, nn_port)
        elif choice_menu == '0':
            print("Saliendo del cliente...")
            break

def run_flask():
    print(f"Yo (este proceso client) voy a correr en {ip} y {port}")
    app.run(host=ip, debug=False, port=int(port))

if __name__ == '__main__':
    #config inicial

    # Argumentos de línea de comandos
    # por ejemplo: python namenode.py --host 192.168.1.100 --port 8080 --is_leader False
    parser = argparse.ArgumentParser(description='Start the NameNode.')
    parser.add_argument('--host', default=None, help='Host of the NameNode')
    parser.add_argument('--port', default=None, help='Port of the NameNode')
    
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('../config.ini')

    #config propia
    username = config['Client']['username']
    password = config['Client']['password']
    ip = config['Client']['ip']
    port = config['Client']['port']
    local_files = config['Client']['local_files']
    block_output = config['Client']['block_output']

  # Actualizar los valores si se proporcionan argumentos en la línea de comandos
    if args.host:
        ip = args.host
    if args.port:
        port = args.port

    client_dir = f"{ip}:{port}"

    #config NameNode
    nn_ip = config['NameNode']['leader_ip']
    nn_port = config['NameNode']['leader_port']
    nameNode_dir = f"{nn_ip}:{nn_port}"

    # config del estandar para los datanodes
    datanode_port = config ['DataNode']['grpc_port']

    # Actualizar los valores si se proporcionan argumentos en la línea de comandos
    if args.host:
        ip = args.host
    if args.port:
        port = args.port


    #main menu

    # Iniciar los hilos para ejecutar el menú y el servidor Flask simultáneamente
    flask_thread = threading.Thread(target=run_flask)
    menu_thread = threading.Thread(target=main_menu)

    flask_thread.start()  # Iniciar el hilo para el servidor Flask
    time.sleep(3) 
    menu_thread.start()  # Iniciar el hilo para el menú

    flask_thread.join()  # Esperar a que el hilo del servidor Flask termine (no debería terminar)
    menu_thread.join()  # Esperar a que el hilo del menú termine (no debería terminar)   

    """
    #testing
    #Prueba de cortar y descortar los archivos txt
    #num_blocks = split_file_into_blocks("./local_files/LoremIpsum.txt", block_output)
    #merge_blocks_into_file("./block_output/LoremIpsum", "./downloaded_files/LoremIpsum1.txt")

    # Llama a la función para registrar un usuario
    #registration_result, status_code = register_user(username, password, client_dir, nn_ip, nn_port)
    #print(f"Registro: {registration_result}, Código de estado: {status_code}")

    # Llama a la función para iniciar sesión
    #login_result, status_code = login(username, password, nn_ip, nn_port)
    #print(f"Inicio de sesión: {login_result}, Código de estado: {status_code}")

    # Llama a la función para cerrar la sesión
    #logout_result, status_code = logout(nameNode_dir, nn_ip, nn_port)
    #print(f"Cierre de sesión: {logout_result['message']}, Código de estado: {status_code}")

    # Solicitar el catálogo
    #request_catalog()

    # Solicitar información sobre un archivo específico (reemplaza 'nombre_del_archivo' con el nombre real del archivo)
    #request_file('loremIpsum.txt')

    # Ejemplo de uso de grpc
    blocks_info = [
        {"block_name": "block1", "block_url": "http://127.0.0.1:6000/files/file_01.txt/chunk1"},
        {"block_name": "block2", "block_url": "http://127.0.0.1:6000/files/file_01.txt/chunk2"}
    ]

    UploadBlock("file_01.txt", 'chunk1', "127.0.0.1:50051")
    DownloadBlock("file_01.txt", 'chunk2', "127.0.0.1:50051")
    """

    print(f"Yo voy a correr en {ip} y {port}")
    app.run(host=ip, debug=True, port=int(port))



