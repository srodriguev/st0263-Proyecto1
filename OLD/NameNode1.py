# -*- coding: utf-8 -*-


from flask import Flask, request, jsonify
import json
import configparser
import bcrypt

import socket

app = Flask(__name__)
REGISTERED_PEERS_FILE = "registered_peers.json"
LOGGED_PEERS_FILE = "logged_peers.json"

# Funciones para cargar el json
def load_registered_peers():
    try:
        with open(REGISTERED_PEERS_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def load_logged_peers():
    try:
        with open(LOGGED_PEERS_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = hash_password(data.get('password'))
        peer_ip = data.get('peer_ip') 
        registered_peer = {peer_ip: [username, password]}
        write_registered_peers(registered_peer)
        return "¡Registro exitoso!"
    except:
        return "Oops, algo salio mal", 401

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    peer_ip = data.get('peer_ip')
    password = data.get('password')
    initial_files = [".git"]
    if verify_password(REGISTERED_PEERS_FILE, peer_ip, password):
        logged_peer = {peer_ip: {"files": initial_files}}
        write_logged_peers(logged_peer)
        return "¡Bienvenido!"
    else:
        return "Los datos ingresados no coinciden, intentalo nuevamente.", 401

@app.route('/logout', methods=['POST'])
def logout():
    data = request.json
    peer_ip = data.get('peer_ip')
    remove_logged_peer(peer_ip)
    return jsonify({"message': f'Logged out peer with IP {peer_ip}"}), 200

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Funciones para escribir en los json correspondientes
def write_registered_peers(logged_peer):
    registered_peers = load_registered_peers() 
    for peer_name, peer_ip in logged_peer.items():
        if peer_name in registered_peers:
            registered_peers[peer_name].append([peer_ip])  
        else:
            registered_peers[peer_name] = [peer_ip] 
    with open(REGISTERED_PEERS_FILE, 'w') as file:
        json.dump(registered_peers, file, indent=4)

def write_logged_peers(logged_peer):
    logged_peers = load_logged_peers() 
    for peer_name, peer_ip in logged_peer.items():
        if peer_name in logged_peers:
            logged_peers[peer_name].append([peer_ip])  
        else:
            logged_peers[peer_name] = [peer_ip] 
    with open(LOGGED_PEERS_FILE, 'w') as file:
        json.dump(logged_peers, file, indent=4)

def remove_logged_peer(peer_ip):
    logged_peers = load_logged_peers()
    keys_to_delete = []
    for ip, info_list in logged_peers.items():
        if ip == peer_ip:
            del logged_peers[ip]
            break
    with open(LOGGED_PEERS_FILE, 'w') as file:
        json.dump(logged_peers, file, indent=4)

def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

def verify_password(json_file, ip_address, password):
    with open(json_file, 'r') as f:
        data = json.load(f)
    if ip_address in data:
        for entry in data[ip_address]:
            stored_hash = entry[1]
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                return True
            else:
                return False
        return False
    else:
        return False

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    host = config['config.ini']['ip']
    port = config['config.ini']['port']
    app.run(host=host, debug=True, port=int(port))