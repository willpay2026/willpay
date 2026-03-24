from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_ultra_secret_2026_legado_wilyanny'

# --- CONFIGURACIÓN DE CARPETAS PARA FOTOS ---
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- CONFIGURACIÓN DE BASE DE DATOS (POSTGRES PARA RENDER / SQLITE LOCAL) ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DE USUARIO WilDON V2 ---
class Usuario(db.Model):
    __tablename__ = 'usuario_v2'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True)
    telefono = db.Column(db.String(20))
    password = db.Column(db.String(100)) 
    saldo = db.Column(db.Float, default=0.0)
    tipo_usuario = db.Column(db.String(50), default='CLIENTE') # CEO, SOCIO, CLIENTE
    
    # Datos de Pago Móvil para Top-ups
    banco = db.Column(db.String(100))
    telefono_pago = db.Column(db.String(20))
    cedula_titular = db.Column(db.String(20))
    
    # Seguridad y Verificación
    foto_cedula = db.Column(db.String(200))
    foto_selfie = db.Column(db.String(200))
    estatus = db.Column(db.String(20), default='PENDIENTE') # PENDIENTE, ACTIVO, BLOQUEADO

    # Configuración de Comisiones (Tu legado)
    comision_rate = db.Column(db.Float, default=1.2)
    auto_aprobacion = db.Column(db.Boolean, default=False)

# Crear Estructura al Iniciar
with app.app_context():
    db.create_all()
    # Tu usuario principal (CEO)
    if not Usuario.query.filter_by(cedula='13496133').first():
        admin = Usuario(
            nombre="Wilfredo Donquiz", 
            cedula="13496133", 
            password="admin", 
            tipo_usuario="CEO", 
            saldo=500.0,
            estatus='ACTIVO'
        )
        db.session.add(admin)
        db.session.commit()

# --- RUTAS DE LA SECUENCIA WilDON ---

@app.route('/')
def index():
    # SECUENCIA 1: Splash Screen
    return render_template('auth/splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # SECUENCIA 2: Acceso
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        pin = request.form.get('password')
        user = Usuario.query.filter_by(cedula=cedula, password=pin).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('admin_panel' if user.tipo_usuario == 'CEO' else 'dashboard'))
        return "Error: Cédula o PIN incorrectos."
    return render_template('auth/acceso.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    # SECUENCIA 3: Registro con Fotos
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        if Usuario.query.filter_by(cedula=cedula).first():
            return "Error: La cédula ya está registrada."

        f_cedula = request.files.get('foto_cedula')
        f_selfie = request.files.get('foto_selfie')
        
        nombre_c = secure_filename(f"{cedula}_cedula.png")
        nombre_s = secure_filename(f"{cedula}_selfie.png")

        nuevo = Usuario(
            nombre=request.form.get('nombre'),
            cedula=cedula,
            telefono=request.form.get('telefono'),
            password=request.form.get('password'),
            foto_cedula=nombre_c,
            foto_selfie=nombre_s
        )
        
        f_cedula.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_c))
        f_selfie.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_s))
        
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('auth/registro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(Usuario, session['user_id'])
    return render_template('user/dashboard.html', user=user)

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session: return redirect(url_for('login'))
    jefe = db.session.get(Usuario, session['user_id'])
    if jefe.tipo_usuario != 'CEO': return redirect(url_for('dashboard'))
    usuarios = Usuario.query.all()
    return render_template('ceo/panel_ceo.html', jefe=jefe, usuarios=usuarios)

if __name__ == '__main__':
    app.run(debug=True)
