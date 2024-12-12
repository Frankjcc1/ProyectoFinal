import random
import string
import time
import uuid

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import boto3
from botocore.exceptions import NoCredentialsError

from models import db, Alumno, Profesor

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:db_admin@mydatabase.cxcoe882c78q.us-east-1.rds.amazonaws.com/dbPython'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

YOUR_AWS_ACCESS_KEY_ID = 'ASIARAUTZWJBPAEKMVV2'
YOUR_AWS_SECRET_ACCESS_KEY = 'c69Is8oZUkFXHGxg+PWerla0eQ6cD9B343/uhhNO'
YOUR_AWS_SESSION_TOKEN = 'IQoJb3JpZ2luX2VjEPr//////////wEaCXVzLXdlc3QtMiJGMEQCIHWqdL0m/h6ChAeHPNX6dhMogd4du+k+PqBk/3dxTOe6AiAZvDKFqO+lOuMMbySS3pZWdSXCdYVk9z8VhSYbJR7o3irBAgiy//////////8BEAAaDDA3MDEwMzE4MzkzOCIMf+PW1VdVJD0h4B9tKpUCj7uUJHAehawkl4fkPnPl/SaNoOk7XryQ+HZmnkR1xP8fGh/pZ0ETWxA0HWJFpx6dUmsq38MK5Itrs+mt7ZOSJL/D99/limS1n2vQGy54K4yMaJ3+a4tmzrbnxYhn7Hi7DUaNEs+dPwB0QreVtOXWzHaQ4blobRaKOnXZwyaD8xt8SHY0UPyVVU9JzTSnw0YSrX7fGOodnqPvC1cefSpUYZ3x48RnFIUeEsgg2tDaASosQ/vMvayekW6EhGohNtaF9xbEYLd41I8OWwCQC4oVFF6V+9thehPUY5Hnd6S4O/EoRIZ7Xs7Av6PrqWvgvgQvDTWLy9HRDeN5Oh7Fg/hdxwrZnuQw1QEg/mblm8BviMIgU623GzDV8+i6BjqeAYz9IVT8jnfcQha/t/L3/OUD8PkLgnXfTsW2iuC1+t1LD9M2DUHongtX2lCSZXXQIe9shT+WG9Zw+ar9Dwj9UYiXto0bYGx8wMyZhZ63Up+6c8B2u9mHMJpOgjFBscdt3VZ/nxpuIzx7pqcrBgEd1XL6rBoR+aFlRKTP5pdzBjen22DPYcIJDdBjaEbHKbLNdsOJrwt2Fr0f7vAUuoJD'
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


dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY,
    aws_session_token=YOUR_AWS_SESSION_TOKEN,  
    region_name=YOUR_AWS_REGION_NAME   
)


table = dynamodb.Table('sesiones-alumnos')

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

        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            s3_path,
            ExtraArgs={'ACL': 'public-read', 'ContentType': file.content_type}
        )

        photo_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_path}"

        alumno.fotoPerfilUrl = photo_url
        db.session.commit()

        return jsonify({'message': 'Foto de perfil subida con éxito', 'fotoPerfilUrl': photo_url}), 200

    except NoCredentialsError:
        return jsonify({'error': 'No se encontraron credenciales AWS'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/alumnos/<int:id>/email', methods=['POST'])
def send_email_notification(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    email_content = (
        f"Información del alumno:\n"
        f"Nombre: {alumno.nombres} {alumno.apellidos}\n"
        f"Promedio: {alumno.promedio}\n"
    )

    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=email_content,
            Subject="Calificaciones del alumno"
        )
        return jsonify({'message': 'Notificación enviada correctamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/alumnos/<int:id>/session/login', methods=['POST'])
def login_session(id):
    data = request.get_json()
    alumno = Alumno.query.get(id)

    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    if not 'password' in data:
        return jsonify({'error': 'Contraseña requerida'}), 400

    if alumno.password != data['password']:
        return jsonify({'error': 'Contraseña incorrecta'}), 400

    session_id = str(uuid.uuid4())
    session_string = ''.join(random.choices(string.ascii_letters + string.digits, k=128))
    timestamp = int(time.time())

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

@app.route('/alumnos/<int:id>/session/verify', methods=['POST'])
def verify_session(id):
    data = request.get_json()

    if not 'sessionString' in data:
        return jsonify({'error': 'SessionString requerido'}), 400

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

@app.route('/alumnos/<int:id>/session/logout', methods=['POST'])
def logout_session(id):
    data = request.get_json()

    if not 'sessionString' in data:
        return jsonify({'error': 'SessionString requerido'}), 400

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

    table.update_item(
        Key={'id': session['id']},
        UpdateExpression='SET active = :active',
        ExpressionAttributeValues={':active': False}
    )

    return jsonify({'message': 'Sesión cerrada con éxito'}), 200


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

@app.route('/profesores', methods=['GET'])
def get_profesores():
    profesores = Profesor.query.all()
    return jsonify([profesor.to_dict() for profesor in profesores]), 200

@app.route('/profesores/<int:id>', methods=['GET'])
def get_profesor_by_id(id):
    profesor = Profesor.query.get(id)
    if profesor is None:
        return jsonify({'error': 'Profesor no encontrado'}), 404
    return jsonify(profesor.to_dict()), 200


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
