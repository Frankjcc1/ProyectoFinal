import random
import string
import time
import uuid
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from models import db, Alumno, Profesor
import boto3
from botocore.exceptions import NoCredentialsError
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:db_admin@mydatabase.cxcoe882c78q.us-east-1.rds.amazonaws.com/dbPython'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


# Inicialización de AWS
AWS_CONFIG = {
    'aws_access_key_id': 'ASIARAUTZWJBFRO4G7MN',
    'aws_secret_access_key': 'NDrC1MGxgGW0eadUttS0dNFwLc1GPkXiwQU7mOQz',
    'aws_session_token': 'IQoJb3JpZ2luX2VjEPb//////////wEaCXVzLXdlc3QtMiJGMEQCIDov16M523ZnmUgFICR2c+RQpkAP7OK634ZePU63ntZlAiAdbc0XttZUhxoiZzZajDY53gN+acemFho80RIZ1BFw8CrBAgiv//////////8BEAAaDDA3MDEwMzE4MzkzOCIMGYig0kUKmAtTtgP6KpUCmbpxuHRv7JoMyILPgqzuSgevlS+C9w7FB2TfJtkJCtgN1QkI0sxe23AePWI+68LXtQBB+M49ImTgn28MxAv+ACwhvDTXBAtfe9xLECesZS6pKCaq9mN8rphuJrD2oNHrfgZFXHTMdz7NgpzhN/3Ks+5QhteloIUb5Hs2NSqy31/Jfbu0Q22NKA6TCuigZV+jrLmd7cl31O/+I/cOXKwO20emJgaJQN8AEluRhpzMyrha7WzQVSnWL7w4eSnh4HHHROcuBFwU22cCVtvscKDmh42N5Ieu46L1ncQ3ByNL8RoMRI8X2NwMFyJjDjh4kqham1yiyrC7V/18v2viyrOtyntmxpQEsjUnYCjIow2rs5OMBIrkzzDaiui6BjqeAb56euVljNodPU2jgHzKMFjHL65K3NNtd6sJ7GvH81hXy27zwYUMSq1NS8C99isVda0aKJXJwQO+jYVefGIdfygEZrDEvqInZuphbjj2HMgyZmit5WfS1Q6H4kW3afCMANcCHjHUkcJ9c/85sgVnyPQfZwOWL3egeAnhc8SoFxmuC8bATvRvqiwtU0i8SzwAKLrjJS24kBbw8KwpKtbI',
    'region_name': 'us-east-1'
}

# Clientes de AWS
s3 = boto3.client('s3', **AWS_CONFIG)
BUCKET_NAME = 'alumnos-profile-pictures'

# Crear base de datos si no existe
with app.app_context():
    db.create_all()

# --- Rutas ya existentes ---
@app.route('/alumnos', methods=['POST'])
def add_alumno():
    data = request.get_json()
    try:
        nuevo_alumno = Alumno(
            nombres=data['nombres'],
            apellidos=data['apellidos'],
            matricula=data['matricula'],
            promedio=data['promedio'],
            password=data['password']
        )
        db.session.add(nuevo_alumno)
        db.session.commit()
        return jsonify(nuevo_alumno.to_dict()), 201
    except (KeyError, ValueError) as e:
        return jsonify({'error': str(e)}), 400

@app.route('/alumnos', methods=['GET'])
def get_alumnos():
    alumnos = Alumno.query.all()
    return jsonify([alumno.to_dict() for alumno in alumnos]), 200

@app.route('/alumnos/<int:id>', methods=['GET'])
def get_alumno_by_id(id):
    alumno = Alumno.query.get(id)
    if alumno is None:
        return jsonify({'error': 'Alumno no encontrado'}), 404
    return jsonify(alumno.to_dict()), 200

@app.route('/alumnos/<int:id>', methods=['PUT'])
def update_alumno(id):
    data = request.get_json()
    alumno = Alumno.query.get(id)
    if alumno is None:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    try:
        if 'nombres' in data and (not data['nombres'] or not isinstance(data['nombres'], str)):
            return jsonify({'error': 'Nombre inválido'}), 400
        if 'apellidos' in data and (not data['apellidos'] or not isinstance(data['apellidos'], str)):
            return jsonify({'error': 'Apellido inválido'}), 400
        if 'promedio' in data and (not isinstance(data['promedio'], (int, float)) or data['promedio'] < 0 or data['promedio'] > 10):
            return jsonify({'error': 'Promedio inválido'}), 400

        alumno.nombres = data.get('nombres', alumno.nombres)
        alumno.apellidos = data.get('apellidos', alumno.apellidos)
        alumno.matricula = data.get('matricula', alumno.matricula)
        alumno.promedio = data.get('promedio', alumno.promedio)
        db.session.commit()
        return jsonify(alumno.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/alumnos/<int:id>', methods=['DELETE'])
def delete_alumno(id):
    alumno = Alumno.query.get(id)
    if alumno is None:
        return jsonify({'error': 'Alumno no encontrado'}), 404
    db.session.delete(alumno)
    db.session.commit()
    return jsonify({'message': 'Alumno eliminado'}), 200

# --- Endpoint adicional: Subir foto de perfil ---
@app.route('/alumnos/<int:id>/fotoPerfil', methods=['POST'])
def upload_profile_picture(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    if 'foto' not in request.files:
        return jsonify({'error': 'Archivo no proporcionado'}), 400

    file = request.files['foto']
    if file.filename == '':
        return jsonify({'error': 'El nombre del archivo está vacío'}), 400

    try:
        filename = secure_filename(file.filename)
        s3_path = f"{id}/{filename}"
        s3.upload_fileobj(file, BUCKET_NAME, s3_path, ExtraArgs={'ACL': 'public-read', 'ContentType': file.content_type})
        photo_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_path}"
        alumno.fotoPerfilUrl = photo_url
        db.session.commit()

        return jsonify({'message': 'Foto de perfil subida con éxito', 'fotoPerfilUrl': photo_url}), 200
    except NoCredentialsError:
        return jsonify({'error': 'No se encontraron credenciales AWS'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Endpoint adicional: Logout ---
@app.route('/alumnos/<int:id>/session/logout', methods=['POST'])
def logout_session(id):
    data = request.get_json()
    if 'sessionString' not in data:
        return jsonify({'error': 'SessionString requerido'}), 400

    response = table.scan(
        FilterExpression='alumnoId = :alumnoId AND sessionString = :sessionString',
        ExpressionAttributeValues={':alumnoId': id, ':sessionString': data['sessionString']}
    )
    items = response.get('Items', [])
    if not items:
        return jsonify({'error': 'Sesión no encontrada'}), 400

    session = items[0]
    if not session['active']:
        return jsonify({'error': 'La sesión ya está cerrada'}), 400

    table.update_item(
        Key={'id': session['id']},
        UpdateExpression='SET active = :active',
        ExpressionAttributeValues={':active': False}
    )

    return jsonify({'message': 'Sesión cerrada correctamente'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
