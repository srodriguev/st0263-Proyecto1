# st0263-Proyecto1
Proyecto 1 - st0263 - Topicos de telematica


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

El resto de la comunicacion es API REST

# CONFIGS

Puse un config global por fuera para no estar revisando en cual puerto esta corriendo que cosa, se le puede poner que haga override si al ejecutar el comando de inicio se ingresa un ip/puerto diferentes para poder correr por ejemplo varios datanodes en 1 maquina.

# Threading

Para que Flask y gRPC corran a la vez debe estar debug en false, o si no no se pueden mezclar. 


# Sobre el NameNode

Por ahora no esta checkeando el login, pero antes de hacer una consulta en el archivo final debo verificar que desde la ip que se hace la consulta de inventario o getfile sea una ip en logged_peers.json

Ya tiene los metodos de consulta y de agregar archivos, le devuelve en que 2 nodos debe guardar cada chunk y es trabajo del cliente guardar cada chunk 2 veces. 