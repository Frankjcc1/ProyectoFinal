from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from models import db, Alumno, Profesor

app = Flask(__name__)

# Configuración de la base de datos para MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:db_admin@mydatabase.cxcoe882c78q.us-east-1.rds.amazonaws.com:3306/dbPython'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Crear base de datos :)
with app.app_context():
    db.create_all()

@app.route('/test_connection', methods=['GET'])
def test_connection():
    try:
        db.session.execute('SELECT 1')
        return jsonify({"message": "Conexión exitosa con la base de datos"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def validar_alumno(data):
    required_fields = ['nombres', 'apellidos', 'matricula', 'promedio', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"El campo {field} es obligatorio y no puede estar vacío."
    if not isinstance(data['promedio'], (int, float)):
        return False, "El promedio debe ser un número."
    return True, ""

def validar_profesor(data):
    required_fields = ['numeroEmpleado', 'nombres', 'apellidos', 'horasClase']
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"El campo {field} es obligatorio y no puede estar vacío."
    if not isinstance(data['horasClase'], int):
        return False, "Las horas de clase deben ser un número entero."
    return True, ""

# Endpoints para Alumnos
@app.route('/alumnos', methods=['GET'])
def get_alumnos():
    alumnos = Alumno.query.all()  # Consulta todos los registros
    return jsonify([alumno.to_dict() for alumno in alumnos]), 200

@app.route('/alumnos/<int:id>', methods=['GET'])
def get_alumno(id):
    alumno = Alumno.query.get(id)  # Busca por ID
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404
    return jsonify(alumno.to_dict()), 200

@app.route('/alumnos', methods=['POST'])
def create_alumno():
    data = request.get_json()
    is_valid, message = validar_alumno(data)
    if not is_valid:
        return jsonify({"error": message}), 400

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
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Matrícula duplicada"}), 400

@app.route('/alumnos/<int:id>', methods=['PUT'])
def update_alumno(id):
    data = request.get_json()
    is_valid, message = validar_alumno(data)
    if not is_valid:
        return jsonify({"error": message}), 400

    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404

    alumno.nombres = data.get('nombres', alumno.nombres)
    alumno.apellidos = data.get('apellidos', alumno.apellidos)
    alumno.matricula = data.get('matricula', alumno.matricula)
    alumno.promedio = data.get('promedio', alumno.promedio)
    alumno.password = data.get('password', alumno.password)
    db.session.commit()

    return jsonify(alumno.to_dict()), 200

@app.route('/alumnos/<int:id>', methods=['DELETE'])
def delete_alumno(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404

    db.session.delete(alumno)
    db.session.commit()
    return jsonify({"message": "Alumno eliminado"}), 200

# Endpoints para Profesores
@app.route('/profesores', methods=['GET'])
def get_profesores():
    profesores = Profesor.query.all()
    return jsonify([profesor.to_dict() for profesor in profesores]), 200

@app.route('/profesores/<int:id>', methods=['GET'])
def get_profesor(id):
    profesor = Profesor.query.get(id)  # Busca por ID en la base de datos
    if not profesor:
        return jsonify({"error": "Profesor no encontrado"}), 404
    return jsonify(profesor.to_dict()), 200

@app.route('/profesores', methods=['POST'])
def create_profesor():
    data = request.get_json()
    is_valid, message = validar_profesor(data)
    if not is_valid:
        return jsonify({"error": message}), 400

    try:
        nuevo_profesor = Profesor(
            numeroEmpleado=data['numeroEmpleado'],
            nombres=data['nombres'],
            apellidos=data['apellidos'],
            horasClase=data['horasClase']
        )
        db.session.add(nuevo_profesor)
        db.session.commit()
        return jsonify(nuevo_profesor.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Número de empleado duplicado"}), 400

@app.route('/profesores/<int:id>', methods=['PUT'])
def update_profesor(id):
    data = request.get_json()
    is_valid, message = validar_profesor(data)
    if not is_valid:
        return jsonify({"error": message}), 400

    profesor = Profesor.query.get(id)
    if not profesor:
        return jsonify({"error": "Profesor no encontrado"}), 404

    profesor.numeroEmpleado = data.get('numeroEmpleado', profesor.numeroEmpleado)
    profesor.nombres = data.get('nombres', profesor.nombres)
    profesor.apellidos = data.get('apellidos', profesor.apellidos)
    profesor.horasClase = data.get('horasClase', profesor.horasClase)
    db.session.commit()

    return jsonify(profesor.to_dict()), 200

@app.route('/profesores/<int:id>', methods=['DELETE'])
def delete_profesor(id):
    profesor = Profesor.query.get(id)
    if not profesor:
        return jsonify({"error": "Profesor no encontrado"}), 404

    db.session.delete(profesor)
    db.session.commit()
    return jsonify({"message": "Profesor eliminado"}), 200

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Método no permitido"}), 405

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Ruta no encontrada"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
