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
    cedula = db.Column(db.String(20), unique=True) # Tu ID 13496133 es el CEO [cite: 2026-03-01]
    password = db.Column(db.String(100))
    saldo = db.Column(db.Float, default=0.0)
    
    # Perfil y Ganancias (Legado Wilyanny) [cite: 2026-02-24]
    tipo_usuario = db.Column(db.String(50)) # PERSONAL, TECNICO, JURIDICO, CEO
    actividad_economica = db.Column(db.String(100)) 
    comision_rate = db.Column(db.Float, default=1.2) # % según actividad
    ganancias_acumuladas = db.Column(db.Float, default=0.0) # Neto Ganancias
    
    # Datos de Pago Móvil CEO [cite: 2026-03-01]
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
    referencia = db.Column(db.String(50), unique=True) # Anti-duplicados [cite: 2026-03-01]
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
        # Si eres tú, vas al Búnker Maestro
        return redirect(url_for('admin_panel' if user.cedula == '13496133' else 'dashboard'))
    return "Credenciales incorrectas."

# --- MUNDO USUARIO (BÓVEDA) ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    cliente = Usuario.query.get(session['user_id'])
    movs = Movimiento.query.filter_by(user_id=cliente.id).order_by(Movimiento.fecha.desc()).limit(10).all()
    return render_template('user/dashboard.html', cliente=cliente, movimientos=movs)

# --- MOTOR DE TRANSFERENCIAS (PAGAR.HTML) ---
@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    emisor = Usuario.query.get(session['user_id'])
    ced_rec = request.form['cedula_receptor']
    monto = float(request.form['monto'])
    receptor = Usuario.query.filter_by(cedula=ced_rec).first()

    if receptor and emisor.saldo >= monto and emisor.cedula != ced_rec:
        emisor.saldo -= monto
        receptor.saldo += monto
        
        # Registro del Pago
        pago = Movimiento(user_id=emisor.id, tipo=f"PAGO A {receptor.nombre}", monto=monto, 
                         referencia=f"WP-{random.randint(1000,9999)}", status='COMPLETADO')
        
        # COMISIÓN CEO (Tu legado crece con cada pago)
        jefe = Usuario.query.filter_by(cedula='13496133').first()
        if jefe:
            jefe.ganancias_acumuladas += (monto * (emisor.comision_rate / 100))
        
        db.session.add(pago)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return "Error: Saldo insuficiente o receptor no existe."

# --- EL BÚNKER DEL PODER (MUNDO CEO) ---
@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session or Usuario.query.get(session['user_id']).cedula != '13496133':
        return redirect(url_for('dashboard'))
    
    jefe = Usuario.query.get(session['user_id'])
    total_red = db.session.query(func.sum(Usuario.saldo)).scalar() or 0.0 # Capital Total
    en_transaccion = db.session.query(func.sum(Movimiento.monto)).filter_by(status='PENDIENTE').scalar() or 0.0
    movs = Movimiento.query.order_by(Movimiento.fecha.desc()).limit(10).all()
    
    return render_template('ceo/panel_maestro.html', u=jefe, total_red=total_red, 
                           en_transaccion=en_transaccion, neto_ganancias=jefe.ganancias_acumuladas, movimientos=movs)

# --- ACCIONES DEL CEO (APROBAR/RECHAZAR RECARGAS) ---
@app.route('/admin/aprobar/<int:mov_id>')
def aprobar_movimiento(mov_id):
    jefe = Usuario.query.filter_by(cedula='13496133').first()
    mov = Movimiento.query.get(mov_id)
    if mov and mov.status == 'PENDIENTE':
        user_rec = Usuario.query.get(mov.user_id)
        user_rec.saldo += mov.monto # Carga de saldo real [cite: 2026-03-01]
        mov.status = 'COMPLETADO'
        db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/procesar_recarga', methods=['POST'])
def procesar_recarga():
    monto = float(request.form['monto'])
    ref = request.form['referencia']
    
    if Movimiento.query.filter_by(referencia=ref).first(): # Bloqueo de duplicados [cite: 2026-03-01]
        return "Error: Referencia ya utilizada."

    nueva = Movimiento(user_id=session['user_id'], tipo='RECARGA', monto=monto, referencia=ref)
    db.session.add(nueva)
    db.session.commit()
    
    # Si tienes el switch de Auto-Aprobación ON
    jefe = Usuario.query.filter_by(cedula='13496133').first()
    if jefe and jefe.auto_aprobacion:
        return redirect(url_for('aprobar_movimiento', mov_id=nueva.id))
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
