from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_ultra_secret_2026_legado_wilyanny'

# --- CARPETAS DE AUDITORÍA ---
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
    estatus = db.Column(db.String(20), default='PENDIENTE') # Para que tú los apruebes

# Crear estructura
with app.app_context():
    db.create_all()

# --- RUTAS DE LA SECUENCIA ---

@app.route('/')
def index():
    return render_template('auth/splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        pin = request.form.get('password')
        user = Usuario.query.filter_by(cedula=cedula, password=pin).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return "Acceso denegado. Revisa tus credenciales."
    return render_template('auth/acceso.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        cedula_ingresada = request.form.get('cedula')
        
        # Verificar si ya existe
        if Usuario.query.filter_by(cedula=cedula_ingresada).first():
            return "Esta cédula ya tiene un expediente abierto."

        # Procesar Archivos KYC
        f_cedula = request.files.get('foto_cedula')
        f_selfie = request.files.get('foto_selfie')
        
        # Nombres de archivo únicos basados en la cédula
        nombre_foto_c = secure_filename(f"KYC_C_{cedula_ingresada}.png")
        nombre_foto_s = secure_filename(f"KYC_S_{cedula_ingresada}.png")

        # Guardar físicamente
        if f_cedula: f_cedula.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_foto_c))
        if f_selfie: f_selfie.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_foto_s))

        # Crear el nuevo Usuario con TODOS los datos del formulario legal
        nuevo_usuario = Usuario(
            nombre=request.form.get('nombre'),
            cedula=cedula_ingresada,
            telefono=request.form.get('telefono'),
            tipo_usuario=request.form.get('tipo_usuario'),
            password=request.form.get('password'),
            banco=request.form.get('banco'),
            telefono_pago=request.form.get('telefono_pago'),
            cedula_titular=request.form.get('cedula_titular'),
            foto_cedula=nombre_foto_c,
            foto_selfie=nombre_foto_s
        )

        db.session.add(nuevo_usuario)
        db.session.commit()
        
        # Después del registro, directo al Login
        return redirect(url_for('login'))

    return render_template('auth/registro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(Usuario, session['user_id'])
    return render_template('user/dashboard.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
