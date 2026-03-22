from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import os
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'willpay_ultra_secret_2026'

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS (ADN DIGITAL) ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True) # CEO ID: 13496133
    password = db.Column(db.String(100))
    saldo = db.Column(db.Float, default=0.0)
    
    # Perfil y Ganancias (Legado Wilyanny)
    tipo_usuario = db.Column(db.String(50)) # PERSONAL, TECNICO, JURIDICO, CEO
    actividad_economica = db.Column(db.String(100)) 
    comision_rate = db.Column(db.Float, default=1.2) 
    ganancias_acumuladas = db.Column(db.Float, default=0.0) 
    
    # Datos de Pago Móvil CEO
    banco = db.Column(db.String(50), default="BANESCO")
    telefono_pago = db.Column(db.String(20), default="04126602555")
    cedula_pago = db.Column(db.String(20), default="13496133")

    # Interruptores del Búnker
    auto_aprobacion = db.Column(db.Boolean, default=False) 
    auto_retiros = db.Column(db.Boolean, default=False)    

class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    tipo = db.Column(db.String(100)) # RECARGA, PAGO, RETIRO
    monto = db.Column(db.Float)
    referencia = db.Column(db.String(50), unique=True) # Correlativo único
    motivo = db.Column(db.String(200), default="PAGO DE SERVICIO") # MOTIVO DE AUDITORÍA
    emisor_nombre = db.Column(db.String(100)) # Para el comprobante
    receptor_nombre = db.Column(db.String(100)) # Para el comprobante
    status = db.Column(db.String(20), default='PENDIENTE') 
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario', backref='movimientos')

with app.app_context():
    db.create_all()

# --- RUTAS DE ACCESO ---
@app.route('/login', methods=['POST'])
def login():
    user = Usuario.query.filter_by(cedula=request.form['cedula'], password=request.form['password']).first()
    if user:
        session['user_id'] = user.id
        return redirect(url_for('admin_panel' if user.cedula == '13496133' else 'dashboard'))
    return "Credenciales incorrectas."

# --- MOTOR DE TRANSFERENCIAS (PAGAR.HTML) ---
@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    emisor = Usuario.query.get(session['user_id'])
    ced_rec = request.form['cedula_receptor']
    monto = float(request.form['monto'])
    concepto = request.form.get('motivo', 'TRANSFERENCIA WILL-PAY') # Captura el Motivo
    
    receptor = Usuario.query.filter_by(cedula=ced_rec).first()

    if receptor and emisor.saldo >= monto and emisor.cedula != ced_rec:
        # Ejecutar movimiento de saldo
        emisor.saldo -= monto
        receptor.saldo += monto
        
        # Generar Correlativo Único WP-XXXXXXXX
        ref_auditoria = f"WP-{random.randint(1000000, 9999999)}"
        
        # Registro del Pago con todos los datos de auditoría
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
        
        # COMISIÓN CEO (El Legado) [cite: 2026-02-24, WhatsApp Image 2026-03-10 at 1

if __name__ == '__main__':
    # Render usa la variable de entorno PORT, si no existe usa el 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
