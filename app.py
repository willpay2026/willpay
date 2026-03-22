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

# --- CONFIGURACIÓN DE BASE DE DATOS ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DE USUARIO (CON ADN CEO INTEGRADO) ---
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
    
    # Parámetros del Búnker
    comision_rate = db.Column(db.Float, default=1.2)
    socio1_rate = db.Column(db.Float, default=1.0)
    socio2_rate = db.Column(db.Float, default=1.0)
    socio3_rate = db.Column(db.Float, default=1.0)
    auto_aprobacion = db.Column(db.Boolean, default=False)
    auto_retiros = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
def index():
    return render_template('auth/splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Creación del CEO si no existe
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

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        f_cedula = request.files.get('foto_cedula')
        f_selfie = request.files.get('foto_selfie')
        cedula_num = request.form.get('cedula')
        
        name_cedula = secure_filename(f"{cedula_num}_ID.jpg") if f_cedula else None
        name_selfie = secure_filename(f"{cedula_num}_SELFIE.jpg") if f_selfie else None
        
        if f_cedula and name_cedula:
            f_cedula.save(os.path.join(app.config['UPLOAD_FOLDER'], name_cedula))
        if f_selfie and name_selfie:
            f_selfie.save(os.path.join(app.config['UPLOAD_FOLDER'], name_selfie))

        nuevo = Usuario(
            nombre=request.form.get('nombre'),
            cedula=cedula_num,
            telefono=request.form.get('telefono'),
            password=request.form.get('password'),
            tipo_usuario=request.form.get('tipo_usuario'),
            foto_cedula=name_cedula,
            foto_selfie=name_selfie
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('auth/registro.html')

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session: return redirect(url_for('login'))
    jefe = db.session.get(Usuario, session['user_id'])
    if not jefe or jefe.cedula != '13496133': return redirect(url_for('dashboard'))
    
    usuarios = Usuario.query.all()
    total_red = sum(u.saldo for u in usuarios)
    
    # Movimientos vacíos por ahora para evitar error en el for del HTML
    return render_template('ceo/panel_ceo.html', 
                           jefe=jefe, 
                           usuarios=usuarios, 
                           total_red=total_red, 
                           movimientos=[])

@app.route('/admin/update_config', methods=['POST'])
def update_config():
    if 'user_id' not in session: return jsonify({'status': 'denied'}), 403
    data = request.json
    jefe = Usuario.query.filter_by(cedula='13496133').first()
    
    field = data.get('field')
    value = data.get('value')

    if field == 'socio1': jefe.socio1_rate = value
    elif field == 'socio2': jefe.socio2_rate = value
    elif field == 'socio3': jefe.socio3_rate = value
    elif field == 'auto_cargas': jefe.auto_aprobacion = value
    elif field == 'auto_retiros': jefe.auto_retiros = value

    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(Usuario, session['user_id'])
    return render_template('user/dashboard.html', user=user)

@app.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
