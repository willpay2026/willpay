from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import random
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_ultra_secret_2026'

# --- CONFIGURACIÓN DE CARPETA DE AUDITORÍA ---
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- CONFIGURACIÓN DE BASE DE DATOS ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELO DE USUARIO LEGAL ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True)
    telefono = db.Column(db.String(20))
    password = db.Column(db.String(100)) # PIN de 6 dígitos
    saldo = db.Column(db.Float, default=0.0)
    tipo_usuario = db.Column(db.String(50))
    
    # DATOS PAGO MÓVIL
    banco = db.Column(db.String(100))
    telefono_pago = db.Column(db.String(20))
    cedula_titular = db.Column(db.String(20))
    
    # EXPEDIENTE VISUAL
    foto_cedula = db.Column(db.String(200))
    foto_selfie = db.Column(db.String(200))
    
    comision_rate = db.Column(db.Float, default=1.2)
    ganancias_acumuladas = db.Column(db.Float, default=0.0)

with app.app_context():
    db.create_all()

# --- RUTAS ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Auto-creación del CEO Wilfredo [cite: 2026-03-01]
    if not Usuario.query.filter_by(cedula='13496133').first():
        db.session.add(Usuario(nombre="Wilfredo Donquiz", cedula="13496133", password="admin", tipo_usuario="CEO", saldo=100.0))
        db.session.commit()

    if request.method == 'POST':
        user = Usuario.query.filter_by(cedula=request.form['cedula'], password=request.form['password']).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return "Credenciales incorrectas."
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Guardar fotos físicamente
        f_cedula = request.files.get('foto_cedula')
        f_selfie = request.files.get('foto_selfie')
        
        name_cedula = secure_filename(f"{request.form['cedula']}_ID.jpg") if f_cedula else None
        name_selfie = secure_filename(f"{request.form['cedula']}_SELFIE.jpg") if f_selfie else None
        
        if f_cedula: f_cedula.save(os.path.join(app.config['UPLOAD_FOLDER'], name_cedula))
        if f_selfie: f_selfie.save(os.path.join(app.config['UPLOAD_FOLDER'], name_selfie))

        nuevo = Usuario(
            nombre=request.form['nombre'],
            cedula=request.form['cedula'],
            telefono=request.form['telefono'],
            password=request.form['password'],
            tipo_usuario=request.form['tipo_usuario'],
            banco=request.form['banco'],
            telefono_pago=request.form['telefono_pago'],
            cedula_titular=request.form['cedula_titular'],
            foto_cedula=name_cedula,
            foto_selfie=name_selfie
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = Usuario.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
