# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import json
import configparser
import bcrypt

import socket

import grpc
#import file_pb2
#import file_pb2_grpc

app = Flask(__name__)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    username = config['Client']['username']
    password = config['Client']['password']
    ip = config['Client']['ip']
    port = config['Client']['port']
    local_files = config['Client']['local_files']
    app.run(host=ip, debug=True, port=int(port))
