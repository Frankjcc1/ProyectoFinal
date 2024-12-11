from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:db_admin@<endpoint>:3306/database-1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Modelos de la base de datos
class Alumno(db.Model):
    __tablename__ = 'alumnos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    matricula = db.Column(db.String(50), unique=True, nullable=False)
    promedio = db.Column(db.Float, nullable=False)
    foto_perfil_url = db.Column(db.String(255), nullable=True)

class Profesor(db.Model):
    __tablename__ = 'profesores'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numero_empleado = db.Column(db.String(50), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    horas_clase = db.Column(db.Integer, nullable=False)

# Crear las tablas en la base de datos
with app.app_context():
    db.create_all()

# Endpoint de prueba de conexión
@app.route('/test_connection', methods=['GET'])
def test_connection():
    try:
        db.session.execute('SELECT 1')
        return jsonify({"message": "Conexión exitosa con la base de datos"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Agregar otros endpoints para manejar alumnos y profesores aquí...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
