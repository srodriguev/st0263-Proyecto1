# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_file
import json
import requests
import configparser
import bcrypt
import csv
import time
import os
import threading


import socket

app = Flask(__name__)

# --- METODOS API REST

# --- FUNCIONES DEL LADO DEL CLIENTE

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

# funciones de consulta de archivos
    
# LEER

# ver el catalogo    
@app.route('/inventory', methods=['GET'])
def get_inventory():
    catalog_path = os.path.join(archive_url, 'catalog.json')
    if os.path.exists(catalog_path):
        return send_file(catalog_path, as_attachment=True)
    else:
        return jsonify({'error': 'El archivo catalog.json no existe. Hay un problema.'}), 404

# buscar en que nodos esta un archivo del catalogo
@app.route('/getfile', methods=['GET'])
def get_file_blocks():
    # Obtener el nombre del archivo solicitado del parámetro en la solicitud
    file_requested = request.args.get('file_requested')

    # Comprobar si el archivo inventory.json existe en la ruta especificada
    inventory_path = os.path.join(archive_url, 'inventory.json')
    if not os.path.exists(inventory_path):
        return jsonify({'error': 'El archivo inventory.json no existe'}), 404

    # Leer el archivo inventory.json
    with open(inventory_path, 'r') as inventory_file:
        inventory_data = json.load(inventory_file)

    # Buscar el archivo solicitado en el inventario
    file_blocks = []
    for datanode in inventory_data['datanodes']:
        for file_entry in datanode['files']:
            if file_entry['name'] == file_requested:
                file_blocks = file_entry['blocks']
                break
        if file_blocks:
            break

    # Verificar si el archivo solicitado está en el inventario
    if not file_blocks:
        return jsonify({'error': f'El archivo {file_requested} no está en el inventario'}), 404

    # Construir la respuesta con la lista de bloques y sus URL
    result = [{'block_name': block['name'], 'block_url': block['url']} for block in file_blocks]

    return jsonify(result), 200


# ESCRIBIR

@app.route('/allocateblocks', methods=['POST'])
def allocate_blocks():
    data = request.get_json()

    # Extraer la información del JSON recibido
    file_name = data.get('file_name')
    num_blocks = data.get('num_blocks')

    # Verificar si el archivo inventory.json existe en la ruta especificada
    inventory_path = os.path.join(archive_url, 'inventory.json')
    if not os.path.exists(inventory_path):
        return jsonify({'error': 'El archivo inventory.json no existe'}), 404

    # Leer el archivo inventory.json
    with open(inventory_path, 'r') as inventory_file:
        inventory_data = json.load(inventory_file)

    # Verificar si el archivo ya está en el inventario
    for datanode in inventory_data['datanodes']:
        for file_data in datanode['files']:
            if file_data['name'] == file_name:
                print("el archivo ya estaba registrado")
                return jsonify({'error': f'El archivo {file_name} ya está en el inventario'}), 400

    # Obtener la lista de nodos de datos disponibles y ordenarlos por espacio disponible de menor a mayor
    available_datanodes = sorted(get_available_datanodes(inventory_data), key=lambda x: x['available_space'])

    print(available_datanodes)
    print(num_blocks)
    # Verificar si hay suficientes nodos de datos disponibles para almacenar todos los bloques
    if len(available_datanodes) < num_blocks:
        return jsonify({'error': 'No hay suficientes nodos de datos disponibles para almacenar todos los bloques'}), 400

    # Lista para almacenar las asignaciones de bloques
    block_assignments = []

    # Iterar sobre cada bloque que debe ser almacenado
    for i in range(1, num_blocks + 1):
        block_name = f"block{i}"

        # Almacenar cada bloque en dos nodos de datos diferentes
        for j in range(2):
            datanode = available_datanodes[j]
            block_url = f"http://{datanode['address']}/files/{file_name}/{block_name}"
            block_assignments.append({'block_name': block_name, 'block_url': block_url, 'assigned_datanode': datanode['address']})

    return jsonify(block_assignments), 200


def get_available_datanodes(inventory_data):
    available_datanodes = []
    for datanode in inventory_data['datanodes']:
        if datanode['status'] == 'online':
            total_space = datanode['total_space']
            available_space = datanode['available_space']
            # Si hay suficiente espacio disponible, añadir el nodo de datos a la lista
            if available_space >= total_space * 0.2:  # Solo considerar nodos con al menos el 20% de su espacio disponible
                available_datanodes.append(datanode)
    return available_datanodes



# --- FUNCIONES DEL LADO DEL DATANODE

# helper para registro de datanode
def register_datanode(namenode_address, uptime_seconds, total_space, available_space):
    # Leer todas las entradas existentes del archivo CSV
    entries = []
    with open(registered_datanodes_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            entries.append(row)

    # Buscar si la dirección ya está registrada
    address_found = False
    for entry in entries:
        if entry[0] == namenode_address:
            # Reemplazar la entrada existente con los nuevos datos
            entry[1] = True  # Cambiar el estado a True
            entry[2] = uptime_seconds
            entry[3] = total_space
            entry[4] = available_space
            address_found = True
            break

    # Si la dirección no está registrada, agregar una nueva entrada
    if not address_found:
        entries.append([namenode_address, True, uptime_seconds, total_space, available_space])

    # Escribir las entradas actualizadas en el archivo CSV
    with open(registered_datanodes_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(entries)

#registremos el datanode nuevo 
@app.route('/registerdatanode', methods=['POST'])
def register_dn():
    data = request.get_json()

    # Extraer la información del JSON recibido
    namenode_address = str(data.get('namenode_address'))  # Convertir a cadena
    uptime_seconds = data.get('uptime_seconds')
    total_space = data.get('total_space')
    available_space = data.get('available_space')

    # Registrar el data node
    register_datanode(namenode_address, uptime_seconds, total_space, available_space)

    # Devolver una respuesta JSON
    response = {
        'message': 'Data node registrado exitosamente',
        'namenode_address': namenode_address,
        'uptime_seconds': uptime_seconds,
        'total_space': total_space,
        'available_space': available_space
    }
    return jsonify(response), 200

def check_datanode_health():
    while True:
        # Abrir el archivo CSV de data nodes registrados y leer las direcciones
        with open(registered_datanodes_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                address = row['address']
                try:
                    # Realizar una solicitud GET a /healthReport en la dirección del data node
                    
                    response = requests.get(f'http://{address}/healthReport', timeout=timer_healthResponse)
                    if response.status_code == 200:
                        # Si la solicitud es exitosa, obtener los datos JSON de la respuesta
                        data = response.json()
                        # Formatear los datos y guardarlos en el archivo de logs
                        formatted_data = {
                            'address': address,
                            'status': 'online',
                            'uptime_seconds': data['uptime_seconds'],
                            'capacity': data['capacity'],
                            'available_capacity':data['available_capacity']
                        }

                        print("update space definition in inventory: ")
                        inventory_file_path = os.path.join(archive_url, 'inventory.json')
                        update_inventory_capacity(address, data['available_capacity'], data['capacity'], inventory_file_path)

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
        # Esperar 1 minuto antes de realizar la próxima verificación
        time.sleep(timer_healthRequest)

def update_inventory_capacity(address, available_capacity, capacity, inventory_file_path):
    # Leer el archivo de inventario JSON
    with open(inventory_file_path, 'r') as inventory_file:
        inventory_data = json.load(inventory_file)
    
    # Buscar el nodo de datos con la dirección especificada
    for datanode in inventory_data['datanodes']:
        if datanode['address'] == address:
            # Actualizar los valores de capacidad
            datanode['space']['available_space'] = available_capacity
            datanode['space']['capacity'] = capacity
            break
    
    # Escribir los datos actualizados de inventario de nuevo al archivo JSON
    with open(inventory_file_path, 'w') as inventory_file:
        json.dump(inventory_data, inventory_file, indent=4)


# --- METODOS CON EL NAME NODE (LEADER Y FOLLOWER)
        
def nameNodeHealthReport():
    print("Health report de follower al leader. Si falla: failback y failover")
    print("un if (si soy follower o leader)")

# --- MAIN LOOP
# IS LEADER = BOOLEANO SI ES UN NAMENODE LIDER O FOLLOWER
# LEADER_DIR = SI ES FOLLOWER TOMAR LA DIRECCION DEL LIDER DEL CONFIG.INI
        
# threads 
def run_health_check():
    threading.Thread(target=check_datanode_health).start()

# main
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
    timer_healthResponse = float(config['NameNode']['timer_healthResponse'])
    timer_healthRequest = float(config['NameNode']['timer_healthRequest'])
    
    # Inicia la verificación de la salud del datanode en un hilo separado
    run_health_check()
    #check_datanode_health()

    app.run(host=ip, debug=True, port=int(port))
    



