# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import json
import requests
import configparser
import bcrypt
import csv
import time
import threading


import socket

app = Flask(__name__)

# --- METODOS API REST

# Funciones para cargar el json
def load_registered_peers():
    try:
        with open(registered_peers_file, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def load_logged_peers():
    try:
        with open(logged_peers_file, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# manejo de usuarios
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = hash_password(data.get('password'))
        peer_ip = data.get('peer_ip')
        
        # Cargar los pares IP-usuario existentes
        registered_peers = load_registered_peers()
        
        if peer_ip in registered_peers:
            return "La dirección IP ya está registrada.", 400
        
        # Si la IP no está registrada, agregarla
        registered_peer = {peer_ip: [username, password]}
        write_registered_peers(registered_peer)
        
        return "¡Registro exitoso!"
    except Exception as e:
        error_message = f"Oops, algo salió mal con el registro: {str(e)}"
        return error_message, 401

@app.route('/remove_user', methods=['POST'])
def remove_user():
    try:
        data = request.json
        peer_ip = data.get('peer_ip')

        # Cargar los pares IP-usuario existentes
        registered_peers = load_registered_peers()

        if peer_ip not in registered_peers:
            return "La dirección IP no está registrada.", 400

        # Eliminar el usuario asociado a la dirección IP
        del registered_peers[peer_ip]
        with open(registered_peers_file, 'w') as file:
            json.dump(registered_peers, file, indent=4)

        return "Usuario eliminado correctamente."
    except Exception as e:
        error_message = f"Oops, algo salió mal al eliminar el usuario: {str(e)}"
        return error_message, 401

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        peer_ip = data.get('peer_ip')
        password = data.get('password')
        initial_files = [".git"]
        if verify_password(registered_peers_file, peer_ip, password):
            logged_peer = {peer_ip: {"files": initial_files}}
            write_logged_peers(logged_peer)
            return "¡Bienvenido!"
        else:
            return "Los datos ingresados no coinciden, intentalo nuevamente.", 401
    except Exception as e:
        error_message = f"Oops, algo salió mal con el inicio de sesión: {str(e)}"
        return error_message, 500

@app.route('/logout', methods=['POST'])
def logout():
    try:
        data = request.json
        peer_ip = data.get('peer_ip')
        remove_logged_peer(peer_ip)
        return jsonify({"message": f"Se cerró la sesión del id: {peer_ip}"}), 200
    except Exception as e:
        error_message = f"Oops, algo salió mal: {str(e)}"
        return error_message, 500

# helpers
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
    with open(registered_peers_file, 'w') as file:
        json.dump(registered_peers, file, indent=4)

def write_logged_peers(logged_peer):
    logged_peers = load_logged_peers() 
    for peer_name, peer_ip in logged_peer.items():
        if peer_name in logged_peers:
            logged_peers[peer_name].append([peer_ip])  
        else:
            logged_peers[peer_name] = [peer_ip] 
    with open(logged_peers_file, 'w') as file:
        json.dump(logged_peers, file, indent=4)

def remove_logged_peer(peer_ip):
    logged_peers = load_logged_peers()
    keys_to_delete = []
    for ip, info_list in logged_peers.items():
        if ip == peer_ip:
            del logged_peers[ip]
            break
    with open(logged_peers_file, 'w') as file:
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

# helper
def register_datanode(namenode_address, uptime_seconds):
    with open(registered_datanodes_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([namenode_address, True, uptime_seconds])

@app.route('/registerdatanode', methods=['POST'])
def register_dn():
    data = request.get_json()

    # Extraer la información del JSON recibido
    namenode_address = str(data.get('namenode_address'))  # Convertir a cadena
    uptime_seconds = data.get('uptime_seconds')

    # Registrar el data node
    register_datanode(namenode_address, uptime_seconds)

    # Devolver una respuesta JSON
    response = {
        'message': 'Data node registrado exitosamente',
        'namenode_address': namenode_address,
        'uptime_seconds': uptime_seconds
    }
    return jsonify(response), 200


def check_datanode_health():
    print("check DN health")
    while True:
        # Abrir el archivo CSV de data nodes registrados y leer las direcciones
        with open(registered_datanodes_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                address = row['address']
                try:
                    # Realizar una solicitud GET a /healthReport en la dirección del data node
                    response = requests.get(f'http://{address}/healthReport')
                    if response.status_code == 200:
                        # Si la solicitud es exitosa, obtener los datos JSON de la respuesta
                        data = response.json()
                        # Formatear los datos y guardarlos en el archivo de logs
                        formatted_data = {
                            'address': address,
                            'status': 'online',
                            'uptime_seconds': data['uptime_seconds']
                        }
                        with open(dn_logs, 'a') as logfile:
                            logfile.write(json.dumps(formatted_data) + '\n')
                    else:
                        # Si la solicitud no es exitosa, marcar el data node como no disponible
                        formatted_data = {
                            'address': address,
                            'status': 'unavailable',
                            'uptime_seconds': None
                        }
                        with open(dn_logs, 'a') as logfile:
                            logfile.write(json.dumps(formatted_data) + '\n')
                except requests.RequestException:
                    # Si hay un error al realizar la solicitud, marcar el data node como no disponible
                    formatted_data = {
                        'address': address,
                        'status': 'unavailable',
                        'uptime_seconds': None
                    }
                    with open(dn_logs, 'a') as logfile:
                        logfile.write(json.dumps(formatted_data) + '\n')
        # Esperar casi 2 minutos antes de realizar la próxima verificación
        time.sleep(100)
        print("Slept 1 time more.")

# --- MAIN LOOP
# IS LEADER = BOOLEANO SI ES UN NAMENODE LIDER O FOLLOWER
# LEADER_DIR = SI ES FOLLOWER TOMAR LA DIRECCION DEL LIDER DEL CONFIG.INI
def run_health_check():
    threading.Thread(target=check_datanode_health).start()

if __name__ == '__main__':
    #config_path = 'config/config.ini'
    config = configparser.ConfigParser()
    #config.read(config_path)
    config.read('../config.ini')
    id = config['NameNode']['name']
    ip = config['NameNode']['ip']
    port = config['NameNode']['port']
    is_leader = config['NameNode']['is_leader'].lower() == 'true'
    leader_ip = config['NameNode']['leader_ip']
    leader_port = config['NameNode']['leader_port']
    dn_logs = config['NameNode']['dn_logs']
    registered_peers_file = config['NameNode']['registered_clients_file']
    logged_peers_file = config['NameNode']['logged_clients_file']
    registered_datanodes_file = config['NameNode']['registered_datanodes_file']
    active_datanodes_file = config['NameNode']['active_datanodes_file']
    archive_url = config['NameNode']['archive_url']
    
    # Inicia la verificación de la salud del datanode en un hilo separado
    #run_health_check()
    check_datanode_health()

    app.run(host=ip, debug=True, port=int(port))
    



