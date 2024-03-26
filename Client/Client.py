# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import json
import configparser
import bcrypt
import os

from Helpers.fileSplitter import split_file_into_blocks 

import socket

import grpc
#import file_pb2
#import file_pb2_grpc

app = Flask(__name__)


def testSplit(output_directory):
    # Asegúrate de que el directorio de salida exista
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Llama a la función split_file_into_blocks con el archivo de entrada y el directorio de salida
    split_file_into_blocks(os.path.join(local_files, "LoremIpsum.txt"), output_directory)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    username = config['Client']['username']
    password = config['Client']['password']
    ip = config['Client']['ip']
    port = config['Client']['port']
    local_files = config['Client']['local_files']
    block_output = config['Client']['block_output']


    testSplit(block_output)

    app.run(host=ip, debug=True, port=int(port))


