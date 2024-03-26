from flask import Flask, jsonify
import os
import time

app = Flask(__name__)

# Ruta de la carpeta donde se almacenan los archivos
FILES_FOLDER = 'files'

# Ruta de la carpeta del DataNode
DATANODE_FOLDER = '/path/to/your/datanode/folder'

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
    for root, dirs, filenames in os.walk(os.path.join(DATANODE_FOLDER, FILES_FOLDER)):
        for filename in filenames:
            filepath = os.path.relpath(os.path.join(root, filename), DATANODE_FOLDER)
            files[filepath] = os.path.getsize(os.path.join(root, filename))
    return jsonify(files)


# METODOS GPRC




# LOOP PRINCIPAL


if __name__ == '__main__':
    app.start_time = time.time()
    app.run(debug=True)
