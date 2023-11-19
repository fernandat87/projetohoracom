from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False)

    def __init__(self, email, senha, tipo_usuario):
        self.email = email
        self.senha_hash = generate_password_hash(senha)
        self.tipo_usuario = tipo_usuario

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

class Academico(User):
    __tablename__ = 'academicos'

    id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)
    # Adicione outros campos específicos do acadêmico, se necessário

class Coordenador(User):
    __tablename__ = 'coordenadores'

    id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)
    # Adicione outros campos específicos do coordenador, se necessário
