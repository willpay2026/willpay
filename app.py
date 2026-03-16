from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import json
import random

app = Flask(__name__)
app.secret_key = 'willpay_ultra_secret_2026'

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(100))
    saldo = db.Column(db.Float, default=0.0)
    banco = db.Column(db.String(50))
    telefono_pago = db.Column(db.String(20))
    cedula_pago = db.Column(db.String(20))

class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    tipo = db.Column(db.String(100))
    monto = db.Column(db.Float)
    status = db.Column(db.String(20), default='COMPLETADO')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario', backref='movimientos')

with app.app_context():
    db.create_all()

# --- RUTAS DE NAVEGACIÓN ---
@app.route('/')
def index():
    return render_template('auth/splash.html')

@app.route('/acceso')
def login_page():
    return render_template('auth/acceso.html')

@app.route('/registro')
def registro_page():
    return render_template('auth/registro.html')

@app.route('/terminos')
def terminos():
    return render_template('auth/terminos.html')

# --- LÓGICA DE USUARIO ---
@app.route('/login', methods=['POST'])
def login():
    cedula = request.form['cedula']
    password = request.form['password']
    user = Usuario.query.filter_by(cedula=cedula, password=password).first()
    if user:
        session['user_id'] = user.id
        session['cedula'] = user.cedula # Guardamos cedula para validaciones admin
        return redirect(url_for('dashboard'))
    return "Credenciales incorrectas. <a href='/acceso'>Volver</a>"

@app.route('/register', methods=['POST'])
def register():
    try:
        nuevo = Usuario(
            nombre=request.form['nombre'],
            cedula=request.form['cedula'],
            password=request.form['password'],
            banco=request.form['banco'],
            telefono_pago=request.form['telefono_pago'],
            cedula_pago=request.form['cedula_pago'],
            saldo=0.0
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('login_page'))
    except:
        return "Error: Datos incorrectos o usuario ya existe."

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    u = Usuario.query.get(session['user_id'])
    movs = Movimiento.query.filter_by(user_id=u.id).order_by(Movimiento.fecha.desc()).limit(10).all()
    return render_template('user/dashboard.html', u=u, movimientos=movs)

# --- CORAZÓN DE WILL-PAY: COBRO AUTOMÁTICO ---
@app.route('/procesar_cobro')
def procesar_cobro():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    datos_qr = request.args.get('datos')
    u_cobrador = Usuario.query.get(session['user_id'])
    
    try:
        data = json.loads(datos_qr)
        u_pagador = Usuario.query.get(data['id'])
        
        # MONTO DE PRUEBA (Fijo para verificar el flujo)
        monto = 10.00 

        if u_pagador.saldo >= monto:
            # RESTA Y SUMA
            u_pagador.saldo -= monto
            u_cobrador.saldo += monto
            
            # GENERAR CORRELATIVO WP-XXXXXX
            ultimo_mov = Movimiento.query.order_by(Movimiento.id.desc()).first()
            nuevo_id = (ultimo_mov.id + 1) if ultimo_mov else 1
            correlativo = f"WP-{nuevo_id:06d}"
            
            # REGISTRAR MOVIMIENTO (Pagador)
            mov_pago = Movimiento(
                user_id=u_pagador.id,
                tipo=f"PAGO ENVIADO A {u_cobrador.nombre} ({correlativo})",
                monto=monto,
                status='COMPLETADO'
            )
            # REGISTRAR MOVIMIENTO (Cobrador)
            mov_cobro = Movimiento(
                user_id=u_cobrador.id,
                tipo=f"COBRO RECIBIDO DE {u_pagador.nombre} ({correlativo})",
                monto=monto,
                status='COMPLETADO'
            )
            
            db.session.add(mov_pago)
            db.session.add(mov_cobro)
            db.session.commit()
            
            # MOSTRAR COMPROBANTE (Ubicado en templates/user/comprobante.html)
            return render_template('user/comprobante.html', 
                                 c=correlativo, 
                                 pagador=u_pagador, 
                                 cobrador=u_cobrador, 
                                 monto=monto,
                                 fecha=datetime.now())
        else:
            return "Saldo insuficiente en la cuenta del pagador."
    except Exception as e:
        return f"Error en lectura de ADN: {str(e)}"

# --- PANEL MAESTRO ---
@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    u = Usuario.query.get(session['user_id'])
    if u.cedula != '13496133': return "Acceso prohibido."

    usuarios = Usuario.query.all()
    total_red = sum(user.saldo for user in usuarios)
    movimientos_vivos = Movimiento.query.order_by(Movimiento.id.desc()).limit(15).all()
    retiros_pendientes = Movimiento.query.filter_by(tipo="RETIRO PENDIENTE").all()

    return render_template('ceo/panel_maestro.html', 
                           u=u, usuarios=usuarios, total_red=total_red, 
                           movimientos=movimientos_vivos, retiros_pendientes=retiros_pendientes)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
