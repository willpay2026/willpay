from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny_ultra_secret'

# --- CONFIGURACIÓN DE CARPETAS PARA AUDITORÍA KYC ---
UPLOAD_FOLDER = 'static/uploads/kyc'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- BASE DE DATOS WilDON V2 ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DE USUARIO EXPANDIDO (KYC) ---
class Usuario(db.Model):
    __tablename__ = 'usuario_v2'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True)
    telefono = db.Column(db.String(20))
    password = db.Column(db.String(100)) 
    saldo = db.Column(db.Float, default=0.0)
    tipo_usuario = db.Column(db.String(100)) # Personal o Comercio
    
    # Datos para Retiro (Pago Móvil)
    banco = db.Column(db.String(100))
    telefono_pago = db.Column(db.String(20))
    cedula_titular = db.Column(db.String(20))
    
    # Archivos de Auditoría Visual
    foto_cedula = db.Column(db.String(200))
    foto_selfie = db.Column(db.String(200))
    estatus = db.Column(db.String(20), default='PENDIENTE')

with app.app_context():
    db.create_all()

# --- LA SECUENCIA WilDON ---

@app.route('/')
def index():
    # PASO 1: SPLASH
    return render_template('auth/splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # PASO 2: ACCESO
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        pin = request.form.get('password')
        user = Usuario.query.filter_by(cedula=cedula, password=pin).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return "ERROR: Credenciales incorrectas."
    return render_template('auth/acceso.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    # PASO 3: REGISTRO LEGAL (KYC)
    if request.method == 'POST':
        cedula_id = request.form.get('cedula')
        
        # Guardar Fotos
        f_cedula = request.files.get('foto_cedula')
        f_selfie = request.files.get('foto_selfie')
        
        nombre_c = secure_filename(f"KYC_C_{cedula_id}.png")
        nombre_s = secure_filename(f"KYC_S_{cedula_id}.png")

        if f_cedula: f_cedula.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_c))
        if f_selfie: f_selfie.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_s))

        nuevo = Usuario(
            nombre=request.form.get('nombre'),
            cedula=cedula_id,
            telefono=request.form.get('telefono'),
            tipo_usuario=request.form.get('tipo_usuario'),
            password=request.form.get('password'),
            banco=request.form.get('banco'),
            telefono_pago=request.form.get('telefono_pago'),
            cedula_titular=request.form.get('cedula_titular'),
            foto_cedula=nombre_c,
            foto_selfie=nombre_s
        )
        db.session.add(nuevo)
        db.session.commit()
        # Al terminar, manda al usuario al login para entrar
        return redirect(url_for('login'))
    return render_template('auth/registro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(Usuario, session['user_id'])
    return f"Bienvenido {user.nombre} - Tu expediente está: {user.estatus}"

if __name__ == '__main__':
    app.run(debug=True)
