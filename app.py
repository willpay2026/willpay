from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import os
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'willpay_ultra_secret_2026'

# --- CONFIGURACIÓN DE BASE DE DATOS (POSTGRESQL RENDER) ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS (ADN DIGITAL WILL-PAY) ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True) # CEO ID: 13496133
    password = db.Column(db.String(100))
    saldo = db.Column(db.Float, default=0.0)
    tipo_usuario = db.Column(db.String(50)) 
    actividad_economica = db.Column(db.String(100)) 
    comision_rate = db.Column(db.Float, default=1.2) 
    ganancias_acumuladas = db.Column(db.Float, default=0.0) 
    banco = db.Column(db.String(50), default="BANESCO")
    telefono_pago = db.Column(db.String(20), default="04126602555")
    cedula_pago = db.Column(db.String(20), default="13496133")
    auto_aprobacion = db.Column(db.Boolean, default=False) 
    auto_retiros = db.Column(db.Boolean, default=False)    

class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    tipo = db.Column(db.String(100)) 
    monto = db.Column(db.Float)
    referencia = db.Column(db.String(50), unique=True) # Correlativo WP-XXXXXXX
    motivo = db.Column(db.String(200), default="PAGO DE SERVICIO") # AUDITORÍA
    emisor_nombre = db.Column(db.String(100)) 
    receptor_nombre = db.Column(db.String(100)) 
    status = db.Column(db.String(20), default='PENDIENTE') 
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario', backref='movimientos')

# --- TRUCO DE RESETEO PARA POSTGRESQL (RENDER GRATIS) ---
with app.app_context():
    # Solo descomenta db.drop_all() si necesitas borrar todo y empezar de cero
    # db.drop_all() 
    db.create_all()
    print("Búnker Will-Pay: Base de Datos Sincronizada ✅")

# --- RUTAS DE ACCESO ---
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # --- ESTO CREA TU USUARIO SI NO EXISTE ---
    with app.app_context():
        ceo = Usuario.query.filter_by(cedula='13496133').first()
        if not ceo:
            nuevo_ceo = Usuario(
                nombre="Wilfredo Donquiz",
                cedula="13496133",
                password="admin", 
                saldo=100000.0,
                tipo_usuario="CEO"
            )
            db.session.add(nuevo_ceo)
            db.session.commit()
    # ------------------------------------------

    if request.method == 'POST':
        cedula = request.form.get('cedula')
        password = request.form.get('password')
        user = Usuario.query.filter_by(cedula=cedula, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return "Credenciales incorrectas."
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = Usuario.query.get(session['user_id'])
    # Pasamos el usuario al HTML para que veas tu nombre y saldo [cite: 2026-03-01]
    return render_template('dashboard.html', user=user)
    # --------------------------------------------------

    if request.method == 'POST':
        cedula = request.form.get('cedula')
        password = request.form.get('password')
        user = Usuario.query.filter_by(cedula=cedula, password=password).first()
        
        if user:
            session['user_id'] = user.id
            # Redirigimos siempre a 'dashboard' para evitar errores de ruta inexistente
            return redirect(url_for('dashboard'))
        return "Credenciales incorrectas."
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = Usuario.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

# --- MOTOR DE TRANSFERENCIAS (PAGAR.HTML) ---
@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    emisor = Usuario.query.get(session['user_id'])
    ced_rec = request.form['cedula_receptor']
    monto = float(request.form['monto'])
    concepto = request.form.get('motivo', 'TRANSFERENCIA WILL-PAY')
    
    receptor = Usuario.query.filter_by(cedula=ced_rec).first()

    if receptor and emisor.saldo >= monto and emisor.cedula != ced_rec:
        # 1. Ejecutar movimiento
        emisor.saldo -= monto
        receptor.saldo += monto
        
        # 2. Generar Correlativo Único
        ref_auditoria = f"WP-{random.randint(1000000, 9999999)}"
        
        # 3. Registro con auditoría completa
        pago = Movimiento(
            user_id=emisor.id, 
            tipo="PAGO REALIZADO", 
            monto=monto, 
            referencia=ref_auditoria,
            motivo=concepto,
            emisor_nombre=emisor.nombre,
            receptor_nombre=receptor.nombre,
            status='COMPLETADO'
        )
        
        # 4. COMISIÓN CEO (El Legado) [cite: 2026-02-24]
        ceo = Usuario.query.filter_by(cedula='13496133').first()
        if ceo:
            comision = monto * (ceo.comision_rate / 100)
            ceo.ganancias_acumuladas += comision
        
        db.session.add(pago)
        db.session.commit()
        
        return f"Pago Exitoso. Ref: {ref_auditoria}" # Aquí irá tu ticket visual
    
    return "Error: Saldo insuficiente o receptor no encontrado."

# --- INICIO DEL SERVIDOR ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
