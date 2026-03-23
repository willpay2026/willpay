from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_ultra_secret_2026'

# --- CONFIGURACIÓN DE ARCHIVOS ---
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- CONFIGURACIÓN DE BASE DE DATOS ---
# Usamos DATABASE_URL de Render
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DE USUARIO (CON TODOS LOS CAMPOS NUEVOS) ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True)
    telefono = db.Column(db.String(20))
    password = db.Column(db.String(100)) 
    saldo = db.Column(db.Float, default=0.0)
    tipo_usuario = db.Column(db.String(50))
    banco = db.Column(db.String(100))
    telefono_pago = db.Column(db.String(20))
    cedula_titular = db.Column(db.String(20))
    foto_cedula = db.Column(db.String(200))
    foto_selfie = db.Column(db.String(200))
    
    # Estos son los campos que causan el error
    comision_rate = db.Column(db.Float, default=1.2)
    socio1_rate = db.Column(db.Float, default=1.0)
    socio2_rate = db.Column(db.Float, default=1.0)
    socio3_rate = db.Column(db.Float, default=1.0)
    auto_aprobacion = db.Column(db.Boolean, default=False)
    auto_retiros = db.Column(db.Boolean, default=False)

# --- RUTAS ---

@app.route('/')
def index():
    return render_template('auth/splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # RE-CREACIÓN DEL CEO (Si no existe tras el reset)
    if not Usuario.query.filter_by(cedula='13496133').first():
        db.session.add(Usuario(
            nombre="Wilfredo Donquiz", 
            cedula="13496133", 
            password="admin", 
            tipo_usuario="CEO", 
            saldo=0.0
        ))
        db.session.commit()

    if request.method == 'POST':
        cedula = request.form.get('cedula')
        password = request.form.get('password')
        user = Usuario.query.filter_by(cedula=cedula, password=password).first()
        
        if user:
            session['user_id'] = user.id
            if user.cedula == '13496133':
                return redirect(url_for('admin_panel'))
            return redirect(url_for('dashboard'))
        return "PIN o Cédula incorrectos."
    
    return render_template('auth/acceso.html')

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session: return redirect(url_for('login'))
    jefe = db.session.get(Usuario, session['user_id'])
    if not jefe or jefe.cedula != '13496133': return redirect(url_for('dashboard'))
    
    usuarios = Usuario.query.all()
    total_red = sum(u.saldo for u in usuarios)
    return render_template('ceo/panel_ceo.html', jefe=jefe, usuarios=usuarios, total_red=total_red, movimientos=[])

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(Usuario, session['user_id'])
    return render_template('user/dashboard.html', user=user)

# --- INICIO DEL SISTEMA CON RESET FORZADO ---
if __name__ == '__main__':
    with app.app_context():
        # ESTO ES LO QUE ARREGLA EL ERROR:
        db.drop_all() 
        db.create_all()
        print("🔥 BASE DE DATOS RESETEADA: COLUMNAS NUEVAS LISTAS 🔥")
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
