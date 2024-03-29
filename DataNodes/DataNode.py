# -*- coding: utf-8 -*-

from flask import Flask, jsonify
import os
import time
import configparser
import json

import grpc
import dataNode_pb2
import dataNode_pb2_grpc

app = Flask(__name__)

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
files_folder = None

# Método para obtener el tiempo de ejecución del DataNode
def uptime():
    return time.time() - app.start_time

# METODOS API REST

@app.route('/healthReport', methods=['GET'])
def health_report():
    uptime_seconds = uptime()
    response = {
        'status': 'online',
        'address': 'localhost:5000',  # Cambiamos esto si es necesario mediante un configfile
        'uptime_seconds': uptime_seconds
    }
    return jsonify(response)

@app.route('/stockReport', methods=['GET'])
def stock_report():
    files = {}

    # Itera sobre los directorios en la carpeta de archivos configurada
    for dirpath, dirnames, filenames in os.walk(files_folder):
        for dirname in dirnames:
            # Agrega el nombre del directorio (nombre del archivo) al diccionario de archivos
            files[dirname] = []

            # Itera sobre los archivos en el directorio (chunks)
            for chunk_filename in os.listdir(os.path.join(dirpath, dirname)):
                # Agrega el nombre del archivo (chunk) al diccionario de archivos
                files[dirname].append(chunk_filename)

    return jsonify(files)


# METODOS GPRC

# --- gprc logic ---
# Método para descargar un bloque de archivo
def download_block(request):
    file_name = request.file_name
    block_name = request.block_name
    file_path = os.path.join(files_folder, file_name, block_name)
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as file:
        block_data = file.read()
    return block_data

# Método para cargar un nuevo bloque de archivo
def upload_block(request):
    file_name = request.file_name
    block_name = request.block_name
    block_data = request.block_data
    folder_path = os.path.join(files_folder, file_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    block_path = os.path.join(folder_path, block_name)
    with open(block_path, "wb") as file:
        file.write(block_data)
    return "Block uploaded successfully"

# --- main ----
# LOOP PRINCIPAL
if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    id = config['DataNode']['id']
    host = config['DataNode']['ip']
    port = config['DataNode']['port']
    files_folder = config['DataNode']['files_folder']
    datanode_folder = config['DataNode']['datanode_folder']
    app.start_time = time.time()
    app.run(host=host, debug=True, port=int(port))
