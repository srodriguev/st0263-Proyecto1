# st0263-Proyecto1
Proyecto 1 - st0263 - Topicos de telematica

# FUNCIONALIDADES YA IMPLEMENTADAS

**General**
- Se tiene un config global para tener coherencia entre los elementos
- carpetas para guardar cada parte del proceso ordenadamente.

**Client:**
- Se corta el archivo en bloques.
- Se reconstruye el archivo desde los bloques.
- Registro de usuarios.
- Login de usuarios.
- Logout de usuarios.
- Leer del config los datos de Cliente y otros nodos.
- Metodos que le envian los request al DataNode del catalogo y la ubicacion de un archivo.
- Metodos Download y Upload de gRPC con el dataNode.
- Forma de interactuar con el programa en vivo (loop principal de acciones o UI)

**DataNode:**
- Se ve el peso de los archivos (espacio ocupada) en bytes
- Se mode el tiempo que lleva vivo el nodo (uptime)
- Puede enviar reportes de salud API Rest
- Puede enviar reportes de Stock API Rest (iventario)
- Se configura con el config file
- Metodos Download y Upload de gRPC con el cliente.

**Namenode (Servidor ppal):**
- Contesta el login
- Contesta el register
- Contesta el remove user (sin probar)
- Contesta el logout
- Hash de contraseñas
- Escribe los clientes registrados en un JSON
- Escribe los clientes en linea en un JSON
- Elimina los clientes registrados en un JSON
- Elimina los clientes en linea en un JSON
- Verifica contraseñas (para login)
- Devuelve un catalogo de archivos (get API Rest con el cliente)
- Devuelve la localizacion de los bloques segun un nombre de archivo (getAPI Rest con cliente)
- Decide donde guardar un archivo nuevo segun el espacio disponible en cada dataNode
- Calcula el espacio disponible en cada dataNode segun la info del inventario.
- Registra un datanode para agregarlo al sistema (api Rest)
- Manda request de health report a todos los DataNode a ver si siguen vivos y lo guarda todo en un log.
- Se actualiza la capacidad del inventario segun la info del health report (sin probar aun)
- Se configura con el config file
- Config manual para el secundario 
- Diferenciar el ppal y el secundario 

# FUNCIONALIDADES POR IMPLEMENTAR

**En general:**
- Se han probado los modulos por separado pero no todo el procedimiento de inicio a fin.
- No se ha probado el manejo de errores en varios módulos.

**Client:**
- mover los helpers a su propio archivo python para que se puedan reutilizar y por orden, corregir errores de importacion (a mi no me estaba dando sobs). 
- Varias funciones del menu tienen logica incorrecta, se estan corrigiendo. -> Corregido

**DataNode:**
- Deberia guardar el hash de cada bloque en algun lado para luego compararlo al enviar el reporte de stock y ver si algun archivo se ha perdido, dañado o corrompido.

**NameNode:**
- Failback del principal al secundario si se muere el otro: avisar a los demas integrantes y que actualicen la IP del namenode pa' los requests. -> En proceso.
- Failover por si el ppal revive 
- Si un dataNode se murió (se entera cuando realiza el health report) repartir los bloques que ese deberia tener entre los demas namenodes, actuando como un minicliente o delegandoselo. -> Parcialmente implementado, identifica cuales debe duplicar y busca donde ponerlos pero aun no "reubica" fisicamente los bloques.


# GRPC METHODS

## Download y Upload Entre datanode y client, ya que son quienes se transfieren el cuerpo de los archivos

En el DataNode hay pedazos de archivos partidos en bloque, cada carpeta tiene el nombre del archivo completo y adentro guarda las partes. 
Hay que crear 2 metodos gRPC entre el cliente y el dataNode para transferir los bloques/fragmentos de archivo

**client.py -> dataNode.py**

**download_Block**(file,filename, blockname, blocknumber, blocksize)
dataNode lo busca en la subcarpeta definida en la variable files_folder y le devuelve el bloque de archivo solicitado.
El formato para buscar es buscar primero la carpeta con el nombre del filename y dentro de esa carpeta el bloque con el blockname.

**client.py -> dataNode.py**

**upload_block**(file,filename, blockname, blocknumber, blocksize)
el cliente le envia la solicitud al dataNode para almacenar ahi un nuevo bloque de archivo.
Si ya existe la carpeta con el filename del archivo mete el nuevo bloque ahi, si no existia la crea. Si ya habia el mismo blockname dentro lo reemplaza.

el archivo asociado debera llamarse dataNode.proto

# API REST METHODS

El resto de la comunicacion es API REST, metodos como:

-Login
-Logout
-RegisterUser
-DeleteUser
-Ping
-GetInventory
-GetFileBlocks
-AllocateBlocks
-RegisterDataNode
-RegisterNameNode

# NOTAS DE DISEÑO Y CONFIGURACIÓN

## Configs

Puse un config global por fuera para no estar revisando en cual puerto esta corriendo que cosa, se le puede poner que haga override si al ejecutar el comando de inicio se ingresa un ip/puerto diferentes para poder correr por ejemplo varios datanodes en 1 maquina.

## Threading

Para que Flask y gRPC corran a la vez debe estar debug en false, o si no no se pueden mezclar. 


## Sobre el NameNode

Por ahora no esta checkeando el login, pero antes de hacer una consulta en el archivo final debo verificar que desde la ip que se hace la consulta de inventario o getfile sea una ip en logged_peers.json

Ya tiene los metodos de consulta y de agregar archivos, le devuelve en que 2 nodos debe guardar cada chunk y es trabajo del cliente guardar cada chunk 2 veces. 

Correrlo con parametros custom o como follower. 

# Decisiones de diseño

Por ahora cuando se inscribe el dataNode de manera inicial se guarda en el csv de registered_datanodes el espacio total y el disponible por si por algun motivo hay menos espacio disponible alla. 

Pero ese dato no se actualiza y se puede usar para comparar si alguna discrepancia, el espacio disponible actual solo se mantiene actualizado en el inventory.json

Podria ser mas eficiente, si, pero por ahora esta asi.


# Orden en que se deberian poner a correr las piezas para un correcto funcionamiento:

1. NameNode principal
2. NameNode secundario
3. DataNode 1
4. DataNode 2
5. DataNode 3
6. Client

# Comandos relevantes

Para correr el codigo en orden, por ejemplo

```python
python3 namenode.py
python3 namenode.py --host 127.0.0.1 --port 5001 --is_leader False
python3 datanode.py
python3 datanode.py --host 127.0.0.1 --port 6001 --grpc_port 50052
python3 datanode.py --host 127.0.0.1 --port 6002 --grpc_port 50053
python3 client.py 
python3 client.py --host 127.0.0.1 --port 5501
```

```
sudo apt update && sudo apt upgrade &&  sudo apt install python3
sudo apt install python3-pip

git clone https://github.com/srodriguev/st0263-Proyecto1
pip install -r requirements.txt

# por si necesita borrar un key 
ssh-keygen -R ec2-100-27-63-134.compute-1.amazonaws.com

sudo  apt install python3.12-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


pip install Flask && pip install grpcio && pip install grpcio-tools && pip install bcrypt

sudo  apt install python3.12-venv && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

```
Por si tiene problemas con ubuntu
pip install --upgrade Flask Werkzeug


```
python3 nameNode2.py --host 100.27.63.134 --port 5000 --is_leader True
python3 nameNode2.py --host 18.233.43.223 --port 5001 --is_leader False
python3 dataNode2.py --host 3.220.100.118 --port 6000 --grpc_port 50051
python3 datanode2.py --host 23.31.23.168 --port 6000 --grpc_port 50051
python3 datanode2.py --host 100.28.19.122 --port 6000 --grpc_port 50051
python3 client.py --host 127.0.0.1 --port 5501
```

```
python3 nameNode2.py --host 172.31.36.253 --port 5000 --is_leader True

python3 nameNode2.py --host 172.31.37.164 --port 5000 --is_leader False
# wildcard para pruebs -> python3 nameNode2.py --host 0.0.0.0 --port 5001 --is_leader False

python3 dataNode2.py --host 172.31.45.139 --port 6000 --grpc_port 50051
python3 dataNode2.py --host 172.31.34.1 --port 6000 --grpc_port 50051
python3 dataNode2.py --host 172.31.36.193 --port 6000 --grpc_port 50051


python3 client2.py --host 172.31.44.11 --port 3000
```

