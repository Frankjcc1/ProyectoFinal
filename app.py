import random
import string
import time
import uuid
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from models import db, Alumno, Profesor
import boto3
from botocore.exceptions import NoCredentialsError
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:db_admin@mydatabase.cxcoe882c78q.us-east-1.rds.amazonaws.com/dbPython'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

YOUR_AWS_ACCESS_KEY_ID = 'ASIARAUTZWJBFRO4G7MN'
YOUR_AWS_SECRET_ACCESS_KEY = 'NDrC1MGxgGW0eadUttS0dNFwLc1GPkXiwQU7mOQz'
YOUR_AWS_SESSION_TOKEN = 'IQoJb3JpZ2luX2VjEPb//////////wEaCXVzLXdlc3QtMiJGMEQCIDov16M523ZnmUgFICR2c+RQpkAP7OK634ZePU63ntZlAiAdbc0XttZUhxoiZzZajDY53gN+acemFho80RIZ1BFw8CrBAgiv//////////8BEAAaDDA3MDEwMzE4MzkzOCIMGYig0kUKmAtTtgP6KpUCmbpxuHRv7JoMyILPgqzuSgevlS+C9w7FB2TfJtkJCtgN1QkI0sxe23AePWI+68LXtQBB+M49ImTgn28MxAv+ACwhvDTXBAtfe9xLECesZS6pKCaq9mN8rphuJrD2oNHrfgZFXHTMdz7NgpzhN/3Ks+5QhteloIUb5Hs2NSqy31/Jfbu0Q22NKA6TCuigZV+jrLmd7cl31O/+I/cOXKwO20emJgaJQN8AEluRhpzMyrha7WzQVSnWL7w4eSnh4HHHROcuBFwU22cCVtvscKDmh42N5Ieu46L1ncQ3ByNL8RoMRI8X2NwMFyJjDjh4kqham1yiyrC7V/18v2viyrOtyntmxpQEsjUnYCjIow2rs5OMBIrkzzDaiui6BjqeAb56euVljNodPU2jgHzKMFjHL65K3NNtd6sJ7GvH81hXy27zwYUMSq1NS8C99isVda0aKJXJwQO+jYVefGIdfygEZrDEvqInZuphbjj2HMgyZmit5WfS1Q6H4kW3afCMANcCHjHUkcJ9c/85sgVnyPQfZwOWL3egeAnhc8SoFxmuC8bATvRvqiwtU0i8SzwAKLrjJS24kBbw8KwpKtbI'
YOUR_AWS_REGION_NAME = 'us-east-1' 

s3 = boto3.client(
    's3',
    aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY,
    aws_session_token=YOUR_AWS_SESSION_TOKEN,
    region_name=YOUR_AWS_REGION_NAME
)

BUCKET_NAME = 'alumnos-profile-pictures'

sns_client = boto3.client(
    'sns',
    aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY,
    aws_session_token=YOUR_AWS_SESSION_TOKEN,  
    region_name=YOUR_AWS_REGION_NAME 
)

SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:070103183938:MiTema'  

# Configurer le client DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY,
    aws_session_token=YOUR_AWS_SESSION_TOKEN,  
    region_name=YOUR_AWS_REGION_NAME   
)

# Table DynamoDB
table = dynamodb.Table('sesiones-alumnos')

# --- Routes pour Alumnos ---

# POST /alumnos - Ajouter un nouvel Alumno
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

# GET /alumnos - Obtenir la liste de tous les Alumnos
@app.route('/alumnos', methods=['GET'])
def get_alumnos():
    alumnos = Alumno.query.all()
    return jsonify([alumno.to_dict() for alumno in alumnos]), 200

# GET /alumnos/{id} - Obtenir un Alumno par ID
@app.route('/alumnos/<int:id>', methods=['GET'])
def get_alumno_by_id(id):
    alumno = Alumno.query.get(id)
    if alumno is None:
        return jsonify({'error': 'Alumno no encontrado'}), 404
    return jsonify(alumno.to_dict()), 200

# PUT /alumnos/{id} - Mettre à jour un Alumno
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
    

# DELETE /alumnos/{id} - Supprimer un Alumno
@app.route('/alumnos/<int:id>', methods=['DELETE'])
def delete_alumno(id):
    alumno = Alumno.query.get(id)
    if alumno is None:
        return jsonify({'error': 'Alumno no encontrado'}), 404
    db.session.delete(alumno)
    db.session.commit()
    return jsonify({'message': 'Alumno eliminado'}), 200

# POST- ajouter une photo de profil
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
        # Sécuriser le nom du fichier
        filename = secure_filename(file.filename)

        # Construire le chemin de l'objet dans S3
        s3_path = f"{id}/{filename}"

        # Téléverser l'image dans S3
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            s3_path,
            ExtraArgs={'ACL': 'public-read', 'ContentType': file.content_type}
        )

        # Construire l'URL publique de l'image
        photo_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_path}"

        # Mettre à jour l'URL dans la base de données
        alumno.fotoPerfilUrl = photo_url
        db.session.commit()

        return jsonify({'message': 'Foto de perfil subida con éxito', 'fotoPerfilUrl': photo_url}), 200

    except NoCredentialsError:
        return jsonify({'error': 'No se encontraron credenciales AWS'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#POST - envoyer une notification
@app.route('/alumnos/<int:id>/email', methods=['POST'])
def send_email_notification(id):
    # Récupérer les données de l'élève
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    # Construire le contenu de l'email
    email_content = (
        f"Información del alumno:\n"
        f"Nombre: {alumno.nombres} {alumno.apellidos}\n"
        f"Promedio: {alumno.promedio}\n"
    )

    try:
        # Publier le message dans le topic SNS
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=email_content,
            Subject="Calificaciones del alumno"
        )
        return jsonify({'message': 'Notificación enviada correctamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST - login session
@app.route('/alumnos/<int:id>/session/login', methods=['POST'])
def login_session(id):
    data = request.get_json()
    alumno = Alumno.query.get(id)

    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    if not 'password' in data:
        return jsonify({'error': 'Contraseña requerida'}), 400

    # Vérifier le mot de passe
    if alumno.password != data['password']:
        return jsonify({'error': 'Contraseña incorrecta'}), 400

    # Générer un UUID et un sessionString aléatoire
    session_id = str(uuid.uuid4())
    session_string = ''.join(random.choices(string.ascii_letters + string.digits, k=128))
    timestamp = int(time.time())

    # Insérer une entrée dans DynamoDB
    table.put_item(
        Item={
            'id': session_id,
            'fecha': timestamp,
            'alumnoId': id,
            'active': True,
            'sessionString': session_string
        }
    )

    return jsonify({'message': 'Sesión creada', 'sessionString': session_string, 'sessionId': session_id}), 200

# POST - vérifier si une session est valide
@app.route('/alumnos/<int:id>/session/verify', methods=['POST'])
def verify_session(id):
    data = request.get_json()

    if not 'sessionString' in data:
        return jsonify({'error': 'SessionString requerido'}), 400

    # Chercher l'entrée dans DynamoDB
    response = table.scan(
        FilterExpression='alumnoId = :alumnoId AND sessionString = :sessionString',
        ExpressionAttributeValues={
            ':alumnoId': id,
            ':sessionString': data['sessionString']
        }
    )

    items = response.get('Items', [])
    if not items:
        return jsonify({'error': 'Sesión no válida'}), 400

    session = items[0]
    if not session['active']:
        return jsonify({'error': 'Sesión inactiva'}), 400

    return jsonify({'message': 'Sesión válida'}), 200

# POST - session logout
@app.route('/alumnos/<int:id>/session/logout', methods=['POST'])
def logout_session(id):
    data = request.get_json()

    if not 'sessionString' in data:
        return jsonify({'error': 'SessionString requerido'}), 400

    # Chercher l'entrée dans DynamoDB
    response = table.scan(
        FilterExpression='alumnoId = :alumnoId AND sessionString = :sessionString',
        ExpressionAttributeValues={
            ':alumnoId': id,
            ':sessionString': data['sessionString']
        }
    )

    items = response.get('Items', [])
    if not items:
        return jsonify({'error': 'Sesión no encontrada'}), 400

    session = items[0]

    # Désactiver la session
    table.update_item(
        Key={'id': session['id']},
        UpdateExpression='SET active = :active',
        ExpressionAttributeValues={':active': False}
    )

    return jsonify({'message': 'Sesión cerrada con éxito'}), 200



# POST /profesores - Ajouter un nouveau Profesor
@app.route('/profesores', methods=['POST'])
def add_profesor():
    data = request.get_json()
    try:
        nuevo_profesor = Profesor(
            nombres=data['nombres'],
            apellidos=data['apellidos'],
            numeroEmpleado=data['numeroEmpleado'],
            horasClase=data['horasClase']
        )
        db.session.add(nuevo_profesor)
        db.session.commit()
        return jsonify(nuevo_profesor.to_dict()), 201
    except (KeyError, ValueError) as e:
        return jsonify({'error': str(e)}), 400

# GET /profesores - Obtenir la liste de tous les Profesores
@app.route('/profesores', methods=['GET'])
def get_profesores():
    profesores = Profesor.query.all()
    return jsonify([profesor.to_dict() for profesor in profesores]), 200

# GET /profesores/{id} - Obtenir un Profesor par ID
@app.route('/profesores/<int:id>', methods=['GET'])
def get_profesor_by_id(id):
    profesor = Profesor.query.get(id)
    if profesor is None:
        return jsonify({'error': 'Profesor no encontrado'}), 404
    return jsonify(profesor.to_dict()), 200

# PUT /profesores/{id} - Mettre à jour un Profesor
@app.route('/profesores/<int:id>', methods=['PUT'])
def update_profesor(id):
    data = request.get_json()
    profesor = Profesor.query.get(id)
    if profesor is None:
        return jsonify({'error': 'Profesor no encontrado'}), 404

    try:
        if 'nombres' in data and (not data['nombres'] or not isinstance(data['nombres'], str)):
            return jsonify({'error': 'Nombre inválido'}), 400
        if 'apellidos' in data and (not data['apellidos'] or not isinstance(data['apellidos'], str)):
            return jsonify({'error': 'Apellido inválido'}), 400
        if 'numeroEmpleado' in data and not isinstance(data['numeroEmpleado'], int):
            return jsonify({'error': 'Numero empleado inválido'}), 400
        if 'horasClase' in data and (not isinstance(data['horasClase'], (int, float)) or data['horasClase'] < 0):
            return jsonify({'error': 'Horas de Clase inválidas'}), 400
        
        profesor.nombres = data.get('nombres', profesor.nombres)
        profesor.apellidos = data.get('apellidos', profesor.apellidos)
        profesor.numeroEmpleado = data.get('numeroEmpleado', profesor.numeroEmpleado)
        profesor.horasClase = data.get('horasClase', profesor.horasClase)
        db.session.commit()
        return jsonify(profesor.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
# DELETE /profesores/{id} - Supprimer un Profesor
@app.route('/profesores/<int:id>', methods=['DELETE'])
def delete_profesor(id):
    profesor = Profesor.query.get(id)
    if profesor is None:
        return jsonify({'error': 'Profesor no encontrado'}), 404
    db.session.delete(profesor)
    db.session.commit()
    return jsonify({'message': 'Profesor eliminado'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
