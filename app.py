from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_ultra_secret_2026'

# --- CONFIGURACIÓN DE CARPETAS ---
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- BASE DE DATOS ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DE USUARIO ---
class Usuario(db.Model):
    __tablename__ = 'usuario_v2'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(100)) 
    saldo = db.Column(db.Float, default=0.0)
    tipo_usuario = db.Column(db.String(50), default='CLIENTE')
    foto_cedula = db.Column(db.String(200))
    foto_selfie = db.Column(db.String(200))

# Crear tablas y usuario administrador
with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(cedula='13496133').first():
        admin = Usuario(nombre="Wilfredo Donquiz", cedula="13496133", password="admin", tipo_usuario="CEO", saldo=100.0)
        db.session.add(admin)
        db.session.commit()

# --- RUTAS DE LA SECUENCIA ---

@app.route('/')
def index():
    # PASO 1: SPLASH
    return render_template('auth/splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # PASO 2: ACCESO
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        password = request.form.get('password')
        user = Usuario.query.filter_by(cedula=cedula, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('admin_panel' if user.tipo_usuario == 'CEO' else 'dashboard'))
        return "Datos incorrectos"
    return render_template('auth/acceso.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    # PASO 3: REGISTRO
    if request.method == 'POST':
        # Guardar fotos y crear usuario
        f_cedula = request.files.get('foto_cedula')
        f_selfie = request.files.get('foto_selfie')
        
        nuevo_user = Usuario(
            nombre=request.form.get('nombre'),
            cedula=request.form.get('cedula'),
            password=request.form.get('password'),
            foto_cedula=secure_filename(f_cedula.filename) if f_cedula else None,
            foto_selfie=secure_filename(f_selfie.filename) if f_selfie else None
        )
        
        if f_cedula: f_cedula.save(os.path.join(app.config['UPLOAD_FOLDER'], nuevo_user.foto_cedula))
        if f_selfie: f_selfie.save(os.path.join(app.config['UPLOAD_FOLDER'], nuevo_user.foto_selfie))
        
        db.session.add(nuevo_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('auth/registro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(Usuario, session['user_id'])
    return f"Bienvenido {user.nombre}, tu saldo es {user.saldo}"

if __name__ == '__main__':
    app.run(debug=True)
