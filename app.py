from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_ultra_secret_2026'

# --- CONFIGURACIÓN DE AUDITORÍA VISUAL ---
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- BASE DE DATOS ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DE USUARIO (EL LEGADO) ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True)
    telefono = db.Column(db.String(20))
    password = db.Column(db.String(100)) # PIN de 6 dígitos
    saldo = db.Column(db.Float, default=0.0)
    tipo_usuario = db.Column(db.String(50)) # Perfil Económico
    
    # Datos Pago Móvil
    banco = db.Column(db.String(100))
    telefono_pago = db.Column(db.String(20))
    cedula_titular = db.Column(db.String(20))
    
    # Expediente Visual
    foto_cedula = db.Column(db.String(200))
    foto_selfie = db.Column(db.String(200))
    
    comision_rate = db.Column(db.Float, default=1.2)
    ganancias_acumuladas = db.Column(db.Float, default=0.0)

with app.app_context():
    db.create_all()

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
def index():
    # 1. SPLASH SCREEN (3 segundos de carga)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Asegurar que Wilfredo (CEO) siempre exista
    ceo = Usuario.query.filter_by(cedula='13496133').first()
    if not ceo:
        nuevo_ceo = Usuario(
            nombre="Wilfredo Donquiz", 
            cedula="13496133", 
            password="admin", 
            tipo_usuario="CEO", 
            saldo=100.0
        )
        db.session.add(nuevo_ceo)
        db.session.commit()

    if request.method == 'POST':
        cedula = request.form.get('cedula')
        password = request.form.get('password')
        user = Usuario.query.filter_by(cedula=cedula, password=password).first()
        
        if user:
            session['user_id'] = user.id
            # 2. REDIRECCIÓN SEGÚN RANGO
            if user.cedula == '13496133':
                return redirect(url_for('admin_panel')) # Panel CEO
            return redirect(url_for('dashboard')) # Dashboard Cliente
        
        return "PIN o Cédula incorrectos."
    
    # 3. ACCESO AL PANEL
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # 1. Obtener archivos y datos
        f_cedula = request.files.get('foto_cedula')
        f_selfie = request.files.get('foto_selfie')
        cedula_num = request.form.get('cedula') # Usamos .get para evitar errores
        
        # 2. Generar nombres seguros (AQUÍ ESTABA EL ERROR)
        name_cedula = secure_filename(f"{cedula_num}_ID.jpg") if f_cedula else None
        name_selfie = secure_filename(f"{cedula_num}_SELFIE.jpg") if f_selfie else None
        
        # 3. Guardar físicamente en la carpeta uploads
        if f_cedula and name_cedula:
            f_cedula.save(os.path.join(app.config['UPLOAD_FOLDER'], name_cedula))
        if f_selfie and name_selfie:
            f_selfie.save(os.path.join(app.config['UPLOAD_FOLDER'], name_selfie))

        # 4. Crear el expediente en la base de datos
        nuevo = Usuario(
            nombre=request.form.get('nombre'),
            cedula=cedula_num,
            telefono=request.form.get('telefono'),
            password=request.form.get('password'),
            tipo_usuario=request.form.get('tipo_usuario'),
            banco=request.form.get('banco'),
            telefono_pago=request.form.get('telefono_pago'),
            cedula_titular=request.form.get('cedula_titular'),
            foto_cedula=name_cedula,
            foto_selfie=name_selfie
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('registro.html')
