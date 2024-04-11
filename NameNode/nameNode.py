# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_file
from collections import defaultdict
import json
import csv
import requests
import configparser
import bcrypt
import time
import os
import threading
import argparse

import socket

import grpc
import dfs_pb2
import dfs_pb2_grpc

app = Flask(__name__)
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

# Método para obtener el tiempo de ejecución del NameNode
def get_uptime():
    return time.time() - app.start_time

# --- METODOS API REST

# --- FUNCIONES DEL LADO DEL CLIENTE

# Funciones para cargar el json
def load_registered_peers():
    try:
        with open(registered_peers_file, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Funciones para cargar el json
def load_logged_peers():
    try:
        with open(logged_peers_file, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# manejo de usuarios/clientes
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

# manejo de usuarios/clientes
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

# manejo de usuarios/clientes
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        peer_ip = data.get('peer_ip')
        password = data.get('password')
        initial_files = ["init.git"]
        if verify_password(registered_peers_file, peer_ip, password):
            logged_peer = {peer_ip: {"files": initial_files}}
            write_logged_peers(logged_peer)
            return "¡Bienvenido!"
        else:
            return "Los datos ingresados no coinciden, intentalo nuevamente.", 401
    except Exception as e:
        error_message = f"Oops, algo salió mal con el inicio de sesión: {str(e)}"
        return error_message, 500

# manejo de usuarios/clientes
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

#hash de la contraseña
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Funciones para escribir en los json correspondientes

#escribir los clientes registrados
def write_registered_peers(logged_peer):
    registered_peers = load_registered_peers() 
    for peer_name, peer_ip in logged_peer.items():
        if peer_name in registered_peers:
            registered_peers[peer_name].append([peer_ip])  
        else:
            registered_peers[peer_name] = [peer_ip] 
    with open(registered_peers_file, 'w') as file:
        json.dump(registered_peers, file, indent=4)

#escribir los clientes loggeados
def write_logged_peers(logged_peer):
    logged_peers = load_logged_peers() 
    for peer_name, peer_ip in logged_peer.items():
        if peer_name in logged_peers:
            logged_peers[peer_name].append([peer_ip])  
        else:
            logged_peers[peer_name] = [peer_ip] 
    with open(logged_peers_file, 'w') as file:
        json.dump(logged_peers, file, indent=4)

#escribir los clientes eliminados
def remove_logged_peer(peer_ip):
    logged_peers = load_logged_peers()
    keys_to_delete = []
    for ip, info_list in logged_peers.items():
        if ip == peer_ip:
            del logged_peers[ip]
            break
    with open(logged_peers_file, 'w') as file:
        json.dump(logged_peers, file, indent=4)

#obtener direccion ip
def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

#verificar contraseña
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

# para que el cliente vea el catalogo    
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
    file_blocks = None
    grpc_dir = None
    for datanode in inventory_data['datanodes']:
        if 'files' in datanode:
            if file_requested in datanode['files']:
                file_blocks = datanode['files'][file_requested]['blocks']
                grpc_dir = datanode['grpc_dir']  # Obtenemos la dirección gRPC del datanode
                break
    # Verificar si el archivo solicitado está en el inventario
    if file_blocks is None:
        return jsonify({'error': f'El archivo {file_requested} no está en el inventario'}), 404

    # Construir la respuesta con la lista de bloques y sus URL
    result = [{'block_name': block['name'], 'block_url': block['url'], 'grpc_dir': grpc_dir} for block in file_blocks]

    return jsonify(result), 200


# ESCRIBIR

# Metodo para actualizar el catálogo
def updateCatalog(file_name):
    # Obtener la ruta completa del archivo de catálogo
    catalog_path = os.path.join(archive_url, "catalog.json")

    # Cargar el archivo de catálogo si existe, o inicializar un nuevo diccionario si no existe
    if os.path.exists(catalog_path):
        with open(catalog_path, "r") as catalog_file:
            catalog = json.load(catalog_file)
    else:
        catalog = {"files": []}

    # Verificar si el archivo ya está en el catálogo
    file_exists = False
    for file_entry in catalog['files']:
        if file_entry['name'] == file_name:
            # Actualizar la disponibilidad del archivo
            file_entry['available'] = True
            file_exists = True
            break

    # Si el archivo no está en el catálogo, agregarlo
    if not file_exists:
        catalog['files'].append({"name": file_name, "available": True})

    # Guardar el catálogo actualizado en el archivo JSON
    with open(catalog_path, "w") as catalog_file:
        json.dump(catalog, catalog_file, indent=4)

# Hay que actualizar inventario cada vez que agrego un archivo nuevo
def addToInventory(file_name, block_assignments, available_datanodes):
    # Obtener la ruta completa del archivo de inventario
    inventory_path = os.path.join(archive_url, "inventory.json")

    # Cargar el archivo de inventario si existe, o inicializar un nuevo diccionario si no existe
    if os.path.exists(inventory_path):
        with open(inventory_path, "r") as inventory_file:
            inventory = json.load(inventory_file)
    else:
        inventory = {"datanodes": []}

    # Iterar sobre las asignaciones de bloques y actualizar el inventario
    for assignment in block_assignments:
        block_name = assignment['block_name']
        block_url = assignment['block_url']
        grpc_dir = assignment['grpc_dir']
        assigned_datanode = assignment['assigned_datanode']

        # Verificar si el datanode ya está en el inventario
        datanode_exists = False
        for node in inventory['datanodes']:
            if node['address'] == assigned_datanode:
                # Agregar el bloque al datanode existente
                block_info = {"name": block_name, "url": block_url}
                node['files'][file_name]['blocks'].append(block_info)
                datanode_exists = True
                break

        # Si el datanode no está en el inventario, agregarlo
        if not datanode_exists:
            # Obtener información adicional del datanode desde el CSV
            datanode_info = get_datanode_info(assigned_datanode, available_datanodes)

            # Crear el nuevo datanode en el inventario
            new_node = {
                "address": assigned_datanode,
                "grpc_dir": grpc_dir,
                "status": datanode_info['status'],
                "uptime": datanode_info['uptime'],
                "total_space": datanode_info['total_space'],
                "available_space": datanode_info['available_space'],
                "files": {
                    file_name: {"blocks": [{"name": block_name, "url": block_url}]}
                }
            }

            inventory['datanodes'].append(new_node)

    # Guardar el inventario actualizado en el archivo JSON
    with open(inventory_path, "w") as inventory_file:
        json.dump(inventory, inventory_file, indent=4)



# Método HELPER para obtener información adicional del datanode desde el CSV
def get_datanode_info(assigned_datanode, available_datanodes):
    for node in available_datanodes:
        if node['address'] == assigned_datanode:
            return {
                'status': node['status'],
                'uptime': node['uptime'],
                'total_space': node['total_space'],
                'available_space': node['available_space']
            }

    # Si no se encuentra la información, devolver un diccionario vacío
    return {}


# Método HELPER para obtener datanodes disponibles desde el archivo CSV de registered datanodes
def get_available_datanodes_from_csv():
    available_datanodes = []
    with open(registered_datanodes_file, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['status'] == 'True':
                available_datanodes.append({
                    'address': row['address'],
                    'status': row['status'],
                    'uptime': row['uptime'],
                    'total_space': int(row['total_space']),
                    'available_space': float(row['available_space']),
                    'grpc_dir': row['grpc_dir']
                })
    return available_datanodes

# Método para asignar bloques
@app.route('/allocateblocks', methods=['POST'])
def allocate_blocks():
    data = request.get_json()

    # Extraer la información del JSON recibido
    file_name = data.get('file_name')
    num_blocks = data.get('num_blocks')

    # Obtener los datanodes disponibles desde el archivo CSV
    available_datanodes = get_available_datanodes_from_csv()

    # Verificar si hay suficientes datanodes disponibles
    if len(available_datanodes) < 2:
        return jsonify({'error': 'No hay suficientes datanodes disponibles para almacenar todos los bloques'}), 400

    # Lista para almacenar las asignaciones de bloques
    block_assignments = []

    # Iterar sobre cada bloque que debe ser almacenado
    for i in range(1, num_blocks ):
        block_name = f"block{i}"

        # Almacenar cada bloque en dos nodos de datos diferentes
        for j in range(2):
            datanode = available_datanodes[j]
            block_url = f"http://{datanode['address']}/files/{file_name}/{block_name}"
            block_assignments.append({
                'block_name': block_name,
                'block_url': block_url,
                'flask_dir': datanode['address'],
                'grpc_dir': datanode['grpc_dir'],
                'assigned_datanode': datanode['address']
            })
    # Llamar al método addToInventory para actualizar el inventario
    addToInventory(file_name, block_assignments, available_datanodes)
    updateCatalog(file_name)
    return jsonify(block_assignments), 200

# devuelve datanodes que estan disponibles
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

#realocar los bloques que tiene un datanode caido
def reallocate_blocks1(address):
    # Leer el archivo inventory.json
    inventory_path = os.path.join(archive_url, 'inventory.json')

    if not os.path.exists(inventory_path):
        print("El archivo inventory.json no existe.")
        return

    with open(inventory_path, 'r') as inventory_file:
        inventory_data = json.load(inventory_file)

    # Buscar el DataNode caído
    failed_datanode = None
    for datanode in inventory_data['datanodes']:
        if datanode['address'] == address:
            failed_datanode = datanode
            break

    if failed_datanode is None:
        print(f"No se encontró ningún DataNode con la dirección {address} en el inventario.")
        return

    # Buscar los bloques almacenados en el DataNode caído
    blocks_to_reallocate = []
    for datanode in inventory_data['datanodes']:
        if datanode != failed_datanode:
            for file_data in datanode['files']:
                for block in file_data['blocks']:
                    for failed_block in failed_datanode.get('files', []):
                        if failed_block['name'] == file_data['name']:
                            blocks_to_reallocate.append((datanode, block['name']))
                            break

    if not blocks_to_reallocate:
        print(f"No hay bloques para realojar del DataNode {address}.")
        return

    # Imprimir la información sobre los bloques a realojar
    print("Bloques a realojar:")
    for datanode, block_name in blocks_to_reallocate:
        print(f"  - Bloque {block_name} está almacenado en el DataNode {datanode['address']}")

    # Obtener los DataNodes disponibles para realojar los bloques
    available_datanodes = get_available_datanodes(inventory_data)

    if not available_datanodes:
        print("No hay DataNodes disponibles para realojar los bloques.")
        return

    print("DataNodes disponibles para realojar los bloques:")
    for datanode in available_datanodes:
        print(f"  - DataNode {datanode['address']}")

    # Realizar la realocación de bloques
    for datanode, block_name in blocks_to_reallocate:
        # Elegir un DataNode disponible para realojar el bloque
        target_datanode = available_datanodes.pop(0)
        # Actualizar el inventario para reflejar la realocación del bloque
        for file_data in target_datanode.get('files', []):
            if file_data['name'] == block_name:
                file_data['blocks'].append({'name': block_name, 'url': f"http://{target_datanode['address']}/files/{file_data['name']}/{block_name}"})
                break

    # Guardar los cambios en el archivo inventory.json
    with open(inventory_path, 'w') as inventory_file:
        json.dump(inventory_data, inventory_file, indent=2)

    print("Reasignación de bloques completada.")

def reallocate_blocks2(address):
    print("Vamos a realocar bloques: ")
    # Leer el archivo inventory.json
    inventory_path = os.path.join(archive_url, 'inventory.json')

    if not os.path.exists(inventory_path):
        print("El archivo inventory.json no existe.")
        return

    with open(inventory_path, 'r') as inventory_file:
        inventory_data = json.load(inventory_file)

    print("Buscar el datanode caido ")
    # Buscar el DataNode caído
    failed_datanode = None
    for datanode in inventory_data['datanodes']:
        if datanode['address'] == address:
            failed_datanode = datanode
            break

    if failed_datanode is None:
        print(f"No se encontró ningún DataNode con la dirección {address} en el inventario.")
        return

    print("Relocalizar bloques")
    # Realizar la realocación de bloques
    for file_data in failed_datanode.get('files', []):
        file_name = file_data['name']
        blocks_to_reallocate = []
        for block in file_data.get('blocks', []):
            block_name = block['name']
            # Encontrar otros DataNodes que también almacenan una copia del mismo bloque y que estén disponibles
            target_datanodes = []
            for datanode in inventory_data['datanodes']:
                if datanode != failed_datanode:
                    for other_file_data in datanode.get('files', []):
                        if other_file_data['name'] == file_name:
                            for other_block in other_file_data.get('blocks', []):
                                if other_block['name'] == block_name:
                                    target_datanodes.append((datanode, other_block))
                                    break
                            break

            if not target_datanodes:
                print(f"No se encontró un DataNode disponible para realojar el bloque {block_name} del archivo {file_name}.")
                continue

            # Imprimir la información sobre los bloques a realojar
            print(f"Bloque {block_name} del archivo {file_name} está almacenado en el DataNode {address}.")
            print("DataNodes disponibles para realojar el bloque:")
            for datanode, _ in target_datanodes:
                print(f"  - DataNode {datanode['address']}")

            # Descargar el bloque del DataNode que aún está en línea
            download_response = DownloadBlock(file_name, block_name, failed_datanode['grpc_dir'])

            # Subir el bloque al primer DataNode disponible
            target_datanode, _ = target_datanodes[0]
            UploadBlock(file_name, block_name, target_datanode['address'], download_response)

            # Actualizar el inventario para reflejar la realocación del bloque
            for other_file_data, other_block in target_datanodes:
                other_file_data['blocks'].append({'name': block_name, 'url': f"http://{target_datanode['address']}/files/{file_name}/{block_name}"})

    # Guardar los cambios en el archivo inventory.json
    with open(inventory_path, 'w') as inventory_file:
        json.dump(inventory_data, inventory_file, indent=2)

    print("Reasignación de bloques completada.")

def reallocate_blocks(address):
    print("Reallocation of blocks is a wip, stay tuned!")

# --- FUNCIONES DEL LADO DEL DATANODE

# helper para registro de datanode
def register_datanode(namenode_address, uptime_seconds, total_space, available_space,grpc_dir):
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
            entry[5] = grpc_dir
            address_found = True
            break

    # Si la dirección no está registrada, agregar una nueva entrada
    if not address_found:
        entries.append([namenode_address, True, uptime_seconds, total_space, available_space, grpc_dir])

    # Escribir las entradas actualizadas en el archivo CSV
    with open(registered_datanodes_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(entries)

#registremos el datanode nuevo 
@app.route('/registerdatanode', methods=['POST'])
def register_dn():
    data = request.get_json()

    # Extraer la información del JSON recibido
    datanode_address = str(data.get('datanode_address'))  # Convertir a cadena
    uptime_seconds = data.get('uptime_seconds')
    total_space = data.get('total_space')
    available_space = data.get('available_space')
    grpc_dir = data.get('grpc_dir')

    # Registrar el data node
    register_datanode(datanode_address, uptime_seconds, total_space, available_space, grpc_dir)
    print(f"Registré exitosemanete este datanode: {datanode_address}")

    # Devolver una respuesta JSON
    response = {
        'message': 'Data node registrado exitosamente',
        'namenode_address': datanode_address,
        'uptime_seconds': uptime_seconds,
        'total_space': total_space,
        'available_space': available_space,
        'grpc_dir': grpc_dir
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
                            'available_capacity': data['available_capacity']
                        }

                        #print("update space definition in inventory: ")
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
                        update_datanode_status(address, 'offline')
                        #LLamar al método que decide donde reguardar lo que habia en ese nodo.
                        reallocate_blocks(address)
                except requests.RequestException:
                    # Si hay un error al realizar la solicitud, marcar el data node como no disponible
                    formatted_data = {
                        'address': address,
                        'status': 'unavailable',
                        'uptime_seconds': None
                    }
                    with open(dn_logs, 'a') as logfile:
                        logfile.write(json.dumps(formatted_data) + '\n')
                    update_datanode_status(address, 'offline')
                    #LLamar al método que decide donde reguardar lo que habia en ese nodo.
                    reallocate_blocks(address)
        # Esperar 1 minuto (o lo que pongamos el timer) antes de realizar la próxima verificación
        time.sleep(timer_healthRequest)

# Cambiar el status de un datanode de online a offline o viceversa
def update_datanode_status(address, status):
    # Leer el archivo de inventario JSON
    inventory_file_path = os.path.join(archive_url, 'inventory.json')
    with open(inventory_file_path, 'r') as inventory_file:
        inventory_data = json.load(inventory_file)
    
    # Buscar el nodo de datos con la dirección especificada
    for datanode in inventory_data['datanodes']:
        if datanode['address'] == address:
            # Actualizar el campo status
            datanode['status'] = status
            break
    
    # Escribir los datos actualizados de inventario de nuevo al archivo JSON
    with open(inventory_file_path, 'w') as inventory_file:
        json.dump(inventory_data, inventory_file, indent=4)

#Actualizar la capacidad del datanode a medida que se va llenando con archivos
def update_inventory_capacity(address, available_capacity, capacity, inventory_file_path):
    # Leer el archivo de inventario JSON
    with open(inventory_file_path, 'r') as inventory_file:
        inventory_data = json.load(inventory_file)
    
    # Buscar el nodo de datos con la dirección especificada
    for datanode in inventory_data['datanodes']:
        if datanode['address'] == address:
            # Actualizar los valores de capacidad
            datanode['available_space'] = available_capacity
            datanode['total_space'] = capacity
            break
    
    # Escribir los datos actualizados de inventario de nuevo al archivo JSON
    with open(inventory_file_path, 'w') as inventory_file:
        json.dump(inventory_data, inventory_file, indent=4)

#ping de follower a leader
def ping_leader(ip, port):
    url = f"http://{leader_ip}:{leader_port}/ping"
    try:
        response = requests.get(url)
        if response.status_code == 200 and response.text == 'pong':
            return True
        else:
            return False
    except requests.RequestException:
        return False



# --- METODOS CON EL NAME NODE = FUNCION DE FOLLOWER

# registrar un namenode nuevo        
def register_nn_follower():
    url = f"http://{leader_ip}:{leader_port}/registernn"
    my_uptime = get_uptime()
    data = {"ip": ip, "port": port, "uptime": my_uptime, "up2date": False}
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("NameNode Follower registrado exitosamente en el NameNode Leader.")
        else:
            print("Error al registrar el NameNode Follower en el NameNode Leader.")
    except Exception as e:
        print("Error de conexión al intentar registrar el NameNode Follower:", e)


# monitoreo hacia el leader para ver si sigue vivo
def check_leader_nn_status():
    print("Check si mi lider sigue con vida!")
    failback_counter = 0
    while True:
        if ping_leader(leader_ip, leader_port):
            print('Ping al líder exitoso')
            failback_counter = 0
            updateAllfiles()
        else:
            print('Ping al líder fallido')
            failback_counter += 1

        if failback_counter >= fail_threshold:
            print('Cumplimos las condiciones para comenzar el failover...')
            do_failover()
            failback_counter = 0  # Reiniciar contador después del failover
            #time.sleep(fail_threshold)  # Esperar antes de volver a intentar?

        time.sleep(5)  # Esperar x tiempo antes de enviar el próximo ping

# metodo de failover, en proceso!!!
def do_failover():
    failover_results = {"registered_clients": {}, "registered_datanodes": {}}
    #print("Iniciamos failover...")
    # Paso 1: Cambiar el NameNode en los clientes registrados
    try:
        with open(registered_peers_file, 'r') as file:
            #print("registered peers: ", registered_peers_file)
            clients_data = json.load(file)
            for ip, _ in clients_data.items():
                print(f"---{clients_data}")
                print(f"---{clients_data.items}")
                client_url = f"http://{ip}/changenamenode"
                print(client_url)
                success = change_namenode(client_url, my_dir)
                failover_results["registered_clients"][ip] = success
    except FileNotFoundError:
        print("Error: No se encontró el archivo de clientes registrados.")
    except json.JSONDecodeError:
        print("Error: No se pudo decodificar el archivo JSON de clientes registrados.")
    except Exception as e:
        print(f"Error inesperado al procesar el archivo de clientes registrados: {e}")

    # Paso 2: Cambiar el NameNode en los DataNodes registrados
    try:
        with open(registered_datanodes_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ip = row["address"].split(":")[0]
                dn_dir = row["address"]
                url = f"http://{dn_dir}/changenamenode"
                success = change_namenode(url, my_dir)
                failover_results["registered_datanodes"][ip] = success
    except FileNotFoundError:
        print("Error: No se encontró el archivo de DataNodes registrados.")
    except Exception as e:
        print(f"Error inesperado al procesar el archivo de DataNodes registrados: {e}")

    # Paso 3: Guardar los resultados del failover
    try:
        with open(fail_logs, 'w') as file:
            json.dump(failover_results, file, indent=2)
    except Exception as e:
        print(f"Error al guardar los resultados del failover en el archivo de registros: {e}")

def change_namenode(url, my_dir):
    try:
        response = requests.post(url, json={"new_url": my_dir})
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error al enviar solicitud POST a {url}: {e}")
        return False

#cambiar el namenode por la nueva url, llamada a rest
def change_namenode1(url):
    url = f"http://{url}/change_namenode"

    try:
        response = requests.post(url)
        return response.status_code == 200
    except requests.RequestException:
        return False


# --- METODOS CON EL NAME NODE = FUNCION DE LEADER

#ping de follower a leader para asegurarse que sigue vivo.
@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'

# helper para que no se repitan los namenodes registrados
def is_combination_present(file_path, ip, port):
    with open(file_path, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == f"{ip}:{port}":
                return True
    return False

# update al archivo de namenodes registrados        
def update_registered_namenodes(ip, port, uptime):
    with open(registered_namenodes_file, mode='r+', newline='') as file:
        writer = csv.writer(file)
        file.seek(0, 2)  # Coloca el cursor al final del archivo
        writer.writerow([f"{ip}:{port}", "active", uptime, ""])

# update a los namenodes activos
def update_active_namenodes(ip, port, uptime):
    with open(active_namenodes_file, mode='r+', newline='') as file:
        writer = csv.writer(file)
        file.seek(0, 2)  # Coloca el cursor al final del archivo
        writer.writerow([f"{ip}:{port}", "active", uptime, ""])

#Registrar un nn follower nuevo.
@app.route('/registernn', methods=['POST'])
def register_nn():
    data = request.json
    ip = data.get('ip')
    port = data.get('port')
    uptime = data.get('uptime')
    if ip and port and uptime:
        update_registered_namenodes(ip, port, uptime)
        update_active_namenodes(ip, port, uptime)
        return jsonify({"message": "NameNode Follower registrado exitosamente en el NameNode Leader."}), 200
    else:
        return jsonify({"error": "Se requieren las direcciones IP, de puerto y el tiempo de uptime del NameNode Follower."}), 400


# -- METODOS PARA ACTUALIZAR LOS ARCHIVOS DEL NAMENODE FOLLOWER SEGUN EL LIDER

# metodos en el lider.

def csv_to_json(csv_file):
    reader = csv.DictReader(csv_file)
    json_data = [row for row in reader]
    return json_data

def json_to_csv(json_data, csv_file):
    # Extraer las claves del primer diccionario para usarlas como encabezados del CSV
    fieldnames = json_data[0].keys()

    # Abrir el archivo CSV en modo escritura
    with open(csv_file, 'w', newline='') as file:
        # Crear un escritor de CSV utilizando los encabezados extraídos
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Escribir los encabezados en el archivo CSV
        writer.writeheader()

        # Escribir cada fila del JSON en el archivo CSV
        for row in json_data:
            writer.writerow(row)
    

# Método para obtener el contenido del archivo de clientes registrados
@app.route('/get_registered_clients')
def get_registered_clients():
    try:
        with open(registered_peers_file, 'r') as file:
            data = json.load(file)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Archivo de clientes registrados no encontrado"})

# Método para obtener el contenido del archivo de clientes conectados
@app.route('/get_logged_clients')
def get_logged_clients():
    try:
        with open(logged_peers_file, 'r') as file:
            data = json.load(file)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Archivo de clientes conectados no encontrado"})

# Método para obtener el contenido del archivo de datanodes registrados
@app.route('/get_registered_datanodes')
def get_registered_datanodes():
    try:
        with open(registered_datanodes_file, 'r') as file:
            # Implementa la lógica para leer el archivo CSV y convertirlo a JSON si es necesario
            # Ejemplo:
            data = csv_to_json(file)
            pass
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Archivo de datanodes registrados no encontrado"})

# Método para obtener el contenido del archivo de datanodes activos
@app.route('/get_active_datanodes')
def get_active_datanodes():
    try:
        with open(active_datanodes_file, 'r') as file:
            # Implementa la lógica para leer el archivo CSV y convertirlo a JSON si es necesario
            # Ejemplo:
            data = csv_to_json(file)
            pass
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Archivo de datanodes activos no encontrado"})

# Método para obtener el contenido del archivo de namenodes registrados
@app.route('/get_registered_namenodes')
def get_registered_namenodes():
    try:
        with open(registered_namenodes_file, 'r') as file:
            # Implementa la lógica para leer el archivo CSV y convertirlo a JSON si es necesario
            # Ejemplo:
            data = csv_to_json(file)
            pass
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Archivo de namenodes registrados no encontrado"})

# Método para obtener el contenido del archivo de namenodes activos
@app.route('/get_active_namenodes')
def get_active_namenodes():
    try:
        with open(active_namenodes_file, 'r') as file:
            # Implementa la lógica para leer el archivo CSV y convertirlo a JSON si es necesario
            # Ejemplo:
            data = csv_to_json(file)
            pass
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Archivo de namenodes activos no encontrado"})

# ---

# - metodos desde el follower para hacer los reemplazos

def update_registered_clients_file(leader_ip, leader_port):
    try:
        # Realizar solicitud al Namenode líder
        response = requests.get(f"http://{leader_ip}:{leader_port}/get_registered_clients")
        
        # Verificar si la solicitud fue exitosa (código de estado 200)
        if response.status_code == 200:
            # Leer el contenido de la respuesta como JSON
            data = response.json()
            
            # Abrir el archivo local en modo escritura y escribir el contenido recibido
            with open('registered_clients.json', 'w') as file:
                json.dump(data, file, indent=2)
                
            print("Archivo de clientes registrados actualizado correctamente.")
        else:
            print("Error al obtener el archivo de clientes registrados del líder.")
    except Exception as e:
        print(f"Error al realizar la solicitud al líder: {e}")

def update_logged_clients_file(leader_ip, leader_port):
    try:
        # Realizar solicitud al Namenode líder
        response = requests.get(f"http://{leader_ip}:{leader_port}/get_logged_clients")
        
        # Verificar si la solicitud fue exitosa (código de estado 200)
        if response.status_code == 200:
            # Leer el contenido de la respuesta como JSON
            data = response.json()
            
            # Abrir el archivo local en modo escritura y escribir el contenido recibido
            with open('logged_clients.json', 'w') as file:
                json.dump(data, file, indent=2)
                
            print("Archivo de clientes conectados actualizado correctamente.")
        else:
            print("Error al obtener el archivo de clientes conectados del líder.")
    except Exception as e:
        print(f"Error al realizar la solicitud al líder: {e}")

def update_registered_datanodes_file(leader_ip, leader_port):
    try:
        # Realizar solicitud al Namenode líder
        response = requests.get(f"http://{leader_ip}:{leader_port}/get_registered_datanodes")
        
        # Verificar si la solicitud fue exitosa (código de estado 200)
        if response.status_code == 200:
            # Leer el contenido de la respuesta como JSON
            data = response.json()
            
            # Abrir el archivo local en modo escritura y escribir el contenido recibido
            with open('registered_datanodes.csv', 'w', newline='') as file:
                # Crear un escritor de CSV
                writer = csv.DictWriter(file, fieldnames=data[0].keys())
                
                # Escribir los encabezados del CSV
                writer.writeheader()
                
                # Escribir cada fila de datos en el archivo CSV
                for row in data:
                    writer.writerow(row)
                
            print("Archivo de datanodes registrados actualizado correctamente.")
        else:
            print("Error al obtener el archivo de datanodes registrados del líder.")
    except Exception as e:
        print(f"Error al realizar la solicitud al líder: {e}")

def get_active_datanodes(leader_ip, leader_port):
    try:
        response = requests.get(f"http://{leader_ip}:{leader_port}/get_active_datanodes")
        if response.status_code == 200:
            data = response.json()
            with open('active_datanodes.csv', 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=data[0].keys())
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            print("Archivo de datanodes activos actualizado correctamente.")
        else:
            print("Error al obtener el archivo de datanodes activos del líder.")
    except Exception as e:
        print(f"Error al realizar la solicitud al líder: {e}")

def get_registered_namenodes(leader_ip, leader_port):
    try:
        response = requests.get(f"http://{leader_ip}:{leader_port}/get_registered_namenodes")
        if response.status_code == 200:
            data = response.json()
            with open('registered_namenodes.csv', 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=data[0].keys())
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            print("Archivo de namenodes registrados actualizado correctamente.")
        else:
            print("Error al obtener el archivo de namenodes registrados del líder.")
    except Exception as e:
        print(f"Error al realizar la solicitud al líder: {e}")

def get_active_namenodes(leader_ip, leader_port):
    try:
        response = requests.get(f"http://{leader_ip}:{leader_port}/get_active_namenodes")
        if response.status_code == 200:
            data = response.json()
            with open('active_namenodes.csv', 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=data[0].keys())
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            print("Archivo de namenodes activos actualizado correctamente.")
        else:
            print("Error al obtener el archivo de namenodes activos del líder.")
    except Exception as e:
        print(f"Error al realizar la solicitud al líder: {e}")

def updateAllfiles():
    try:
        get_active_namenodes(leader_ip, leader_port)
    except Exception as e:
        print("Error al obtener los namenodes activos:", e)
    
    try:
        get_registered_namenodes(leader_ip, leader_port)
    except Exception as e:
        print("Error al obtener los namenodes registrados:", e)
    
    try:
        get_active_datanodes(leader_ip, leader_port)
    except Exception as e:
        print("Error al obtener los datanodes activos:", e)
    
    try:
        update_registered_datanodes_file(leader_ip, leader_port)
    except Exception as e:
        print("Error al actualizar el archivo de datanodes registrados:", e)
    
    try:
        update_logged_clients_file(leader_ip, leader_port)
    except Exception as e:
        print("Error al actualizar el archivo de clientes conectados:", e)
    
    try:
        update_registered_clients_file(leader_ip, leader_port)
    except Exception as e:
        print("Error al actualizar el archivo de clientes registrados:", e)

# --- METODOS GRPC, MINI CLIENTE PARA ENVIAR SOLICITUDES AL DATANODE DE REALOCAR VAINAS CUANDO OTRO DATANODE SE CAE

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
        print("Download request created in client.")
        
        # Envía la solicitud al servidor gRPC
        response = stub.DownloadBlock(request)
        print("Sent download request to server")
        
        # Maneja la respuesta del servidor
        if response.block_data:
            #print("Downloaded data:", response.block_data)
            print("Download was successful")
            return response.block_data
        else:
            print("Download failed.")
            return None
        

# --- MAIN LOOP
# IS LEADER = BOOLEANO SI ES UN NAMENODE LIDER O FOLLOWER
# LEADER_DIR = SI ES FOLLOWER TOMAR LA DIRECCION DEL LIDER DEL CONFIG.INI
        
# threads 
def run_health_check():
    threading.Thread(target=check_datanode_health).start()

def run_nn_health_check():
    threading.Thread(target=check_leader_nn_status).start()

# main
if __name__ == '__main__':

    # Argumentos de línea de comandos
    # por ejemplo: python namenode.py --host 192.168.1.100 --port 8080 --is_leader False
    parser = argparse.ArgumentParser(description='Start the NameNode.')
    parser.add_argument('--host', default=None, help='Host of the NameNode')
    parser.add_argument('--port', default=None, help='Port of the NameNode')
    parser.add_argument('--is_leader', default=None, help='Whether the NameNode is the leader or not')
    
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('../config.ini')
    id = config['NameNode']['name']
    ip = config['NameNode']['ip']
    port = config['NameNode']['port']
    is_leader = config['NameNode']['is_leader'].lower() == 'true'
    leader_ip = config['NameNode']['leader_ip']
    leader_port = config['NameNode']['leader_port']
    dn_logs = config['NameNode']['dn_logs']
    fail_logs = config['NameNode']['fail_logs']
    registered_peers_file = config['NameNode']['registered_clients_file']
    logged_peers_file = config['NameNode']['logged_clients_file']
    registered_datanodes_file = config['NameNode']['registered_datanodes_file']
    active_datanodes_file = config['NameNode']['active_datanodes_file']
    registered_namenodes_file = config['NameNode']['registered_namenodes_file']
    active_namenodes_file = config['NameNode']['active_namenodes_file']
    archive_url = config['NameNode']['archive_url']
    timer_healthResponse = float(config['NameNode']['timer_healthResponse'])
    timer_healthRequest = float(config['NameNode']['timer_healthRequest'])
    fail_threshold = float(config['NameNode']['fail_threshold'])

    app.start_time = time.time()

    # Actualizar los valores si se proporcionan argumentos en la línea de comandos
    if args.host:
        ip = args.host
    if args.port:
        port = args.port
    if args.is_leader:
        is_leader = args.is_leader.lower() == 'true'

    leader_dir = f"{leader_ip}:{leader_port}"
    my_dir = f"{ip}:{port}"
    
    if (is_leader):
        # Inicia la verificación de la salud del datanode en un hilo separado
        print("Soy un NameNode leader, checkeo que mis followers sigan vivos.")
        run_health_check()
    else:
        print("Soy un nameNode follower, me registro con mi lider")
        register_nn_follower()
        run_nn_health_check()


    print(f"Yo voy a correr en {ip} y {port}")
    app.run(host=ip, debug=True, port=int(port))
    


