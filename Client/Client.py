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
#import file_pb2
#import file_pb2_grpc

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

def register_user(username, password, peer_ip, nn_ip, nn_port):
    url = f"http://{nn_ip}:{nn_port}/register"
    data = {
        "username": username,
        "password": password,
        "peer_ip": peer_ip
    }
    response = requests.post(url, json=data)
    return response.text, response.status_code

def login(peer_ip, password, nn_ip, nn_port):
    url = f"http://{nn_ip}:{nn_port}/login"
    data = {
        "peer_ip": peer_ip,
        "password": password
    }
    response = requests.post(url, json=data)
    return response.text, response.status_code


# --- METODOS DE GPRC
            
    

# --- LOOP PRINCIPAL

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    #config propia
    username = config['Client']['username']
    password = config['Client']['password']
    ip = config['Client']['ip']
    port = config['Client']['port']
    local_files = config['Client']['local_files']
    block_output = config['Client']['block_output']

    peer_ip = f"{ip}:{port}"
    print("--- peer_ip is: "+peer_ip)

    #config NameNode
    nn_ip = config['NameNode']['ip']
    nn_port = config['NameNode']['port']


    #Prueba de cortar y descortar los archivos txt
    split_file_into_blocks("./local_files/LoremIpsum.txt", block_output)
    merge_blocks_into_file("./block_output/LoremIpsum", "./downloaded_files/LoremIpsum1.txt")

    # Llama a la función para registrar un usuario
    registration_result, status_code = register_user(username, password, ip, nn_ip, nn_port)
    print(f"Registro: {registration_result}, Código de estado: {status_code}")

    # Llama a la función para iniciar sesión
    login_result, status_code = login(peer_ip, password, nn_ip, nn_port)
    print(f"Inicio de sesión: {login_result}, Código de estado: {status_code}")

    app.run(host=ip, debug=True, port=int(port))


