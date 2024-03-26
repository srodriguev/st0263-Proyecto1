# -*- coding: utf-8 -*-

from flask import Flask, jsonify
import os
import time
import configparser
import json

app = Flask(__name__)

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
    for root, dirs, filenames in os.walk(files_folder):
        for filename in filenames:
            filepath = os.path.relpath(os.path.join(root, filename), files_folder)
            files[filepath] = os.path.getsize(os.path.join(root, filename))
    return jsonify(files)


# METODOS GPRC

#read() // leer los archivos que tiene

#create() //añadir un archivo nuevo


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
