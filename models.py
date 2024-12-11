from flask_sqlalchemy import SQLAlchemy

# Inicializar SQLAlchemy
db = SQLAlchemy()

class Alumno(db.Model):
    __tablename__ = 'alumnos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    matricula = db.Column(db.String(50), unique=True, nullable=False)
    promedio = db.Column(db.Float, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    fotoPerfilUrl = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombres': self.nombres,
            'apellidos': self.apellidos,
            'matricula': self.matricula,
            'promedio': self.promedio,
            'fotoPerfilUrl': self.fotoPerfilUrl
        }

class Profesor(db.Model):
    __tablename__ = 'profesores'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numeroEmpleado = db.Column(db.String(50), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    horasClase = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'numeroEmpleado': self.numeroEmpleado,
            'nombres': self.nombres,
            'apellidos': self.apellidos,
            'horasClase': self.horasClase
        }
