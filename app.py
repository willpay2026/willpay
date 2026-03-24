from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny'

# --- CONFIGURACIÓN DE RUTAS Y DB ---
UPLOAD_FOLDER = 'static/uploads/kyc'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO KYC ---
class Usuario(db.Model):
    __tablename__ = 'usuario_v2'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True)
    telefono = db.Column(db.String(20))
    password = db.Column(db.String(100)) 
    tipo_usuario = db.Column(db.String(100))
    banco = db.Column(db.String(100))
    telefono_pago = db.Column(db.String(20))
    cedula_titular = db.Column(db.String(20))
    foto_cedula = db.Column(db.String(200))
    foto_selfie = db.Column(db.String(200))
    saldo = db.Column(db.Float, default=0.0)

with app.app_context():
    db.create_all()

# --- LA SECUENCIA DE ACERO ---

@app.route('/')
def index():
    # PASO 1: Lanza el Splash
    return render_template('auth/splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # PASO 2: Acceso (Viene del Splash o del Registro)
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        pin = request.form.get('password')
        user = Usuario.query.filter_by(cedula=cedula, password=pin).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return "ERROR: Credenciales no encontradas."
    return render_template('auth/acceso.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    # PASO 3: Registro KYC
    if request.method == 'POST':
        # (Aquí va toda la lógica de guardado que ya tenemos)
        # Al finalizar el registro, mandamos al LOGIN
        return redirect(url_for('login'))
    return render_template('auth/registro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    return "BIENVENIDO A TU BILLETERA WILL-PAY"

if __name__ == '__main__':
    app.run(debug=True)
