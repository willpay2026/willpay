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

# --- MODELOS ESTRATÉGICOS ---
# --- MODELO USUARIO ACTUALIZADO PARA EL LEGADO ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(100))
    saldo = db.Column(db.Float, default=0.0)
    
    tipo_usuario = db.Column(db.String(50)) 
    actividad_economica = db.Column(db.String(100)) 
    rif_juridico = db.Column(db.String(20)) 
    comision_rate = db.Column(db.Float, default=0.0) 
    
    # Datos de pago para Retiros
    banco = db.Column(db.String(50))
    telefono_pago = db.Column(db.String(20))
    cedula_pago = db.Column(db.String(20))

    # --- MANDO CEO: SUICHES DE CONTROL ---
    auto_aprobacion = db.Column(db.Boolean, default=False) # Cargas de Saldo
    auto_retiros = db.Column(db.Boolean, default=False)    # Retiros (Dices que los quieres manual, pero aquí está el suiche)
    
    # --- PUESTOS ESTRATÉGICOS: LOS 5 SOCIOS (%) ---
    socio1_rate = db.Column(db.Float, default=0.0)
    socio2_rate = db.Column(db.Float, default=0.0)
    socio3_rate = db.Column(db.Float, default=0.0)
    socio4_rate = db.Column(db.Float, default=0.0)
    socio5_rate = db.Column(db.Float, default=0.0)

class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    tipo = db.Column(db.String(100))
    monto = db.Column(db.Float)
    status = db.Column(db.String(20), default='COMPLETADO')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario', backref='movimientos')
with app.app_context():
    # db.drop_all()   # <-- ESTA ES LA QUE LIMPIA TODO LO VIEJO
    db.create_all() # <-- ESTA CREA LAS TABLAS NUEVAS

# --- RUTAS DE NAVEGACIÓN ---
@app.route('/')
def index():
    return render_template('auth/splash.html')

@app.route('/acceso')
def login_page():
    return render_template('auth/acceso.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro_page():
    if request.method == 'POST':
        try:
            tipo = request.form.get('tipo_usuario', 'PERSONAL')
            cedula_ingresada = request.form['cedula'] 
            
            comision = 0.0
            if tipo == 'TECNICO': comision = 1.5
            elif tipo == 'JURIDICO': comision = 3.0

            # LÓGICA CEO: Si es tu cédula, el rango escala a CEO automáticamente
            tipo_final = tipo
            if cedula_ingresada == '13496133':
                tipo_final = 'CEO'

            nuevo = Usuario(
                nombre=request.form['nombre'],
                cedula=cedula_ingresada,
                password=request.form['password'],
                tipo_usuario=tipo_final, 
                actividad_economica=request.form.get('actividad_economica'),
                rif_juridico=request.form.get('rif_juridico'),
                comision_rate=comision,
                banco=request.form['banco'],
                telefono_pago=request.form['telefono_pago'],
                cedula_pago=request.form['cedula_pago'],
                saldo=0.0
            )
            db.session.add(nuevo)
            db.session.commit()
            return redirect(url_for('login_page'))
        except Exception as e:
            return f"Error en registro: {str(e)}"
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
        # SI ES TU CÉDULA, AL BÚNKER DE UNA VEZ
        if user.cedula == '13496133':
            return redirect(url_for('admin_panel'))
        return redirect(url_for('dashboard'))
    
    return "Credenciales incorrectas. <a href='/acceso'>Volver</a>"
           
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    u = Usuario.query.get(session['user_id'])
    movs = Movimiento.query.filter_by(user_id=u.id).order_by(Movimiento.fecha.desc()).limit(10).all()
    return render_template('user/dashboard.html', u=u, movimientos=movs)

# --- PROCESAMIENTO DE COBRO ---
@app.route('/procesar_cobro')
def procesar_cobro():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    datos_qr = request.args.get('datos')
    u_cobrador = Usuario.query.get(session['user_id'])
    
    try:
        data = json.loads(datos_qr)
        u_pagador = Usuario.query.get(data['id'])
        monto = 10.00 

        if u_pagador.saldo >= monto:
            u_pagador.saldo -= monto
            u_cobrador.saldo += monto
            
            ultimo_mov = Movimiento.query.order_by(Movimiento.id.desc()).first()
            nuevo_id = (ultimo_mov.id + 1) if ultimo_mov else 1
            correlativo = f"WP-{nuevo_id:06d}"
            
            mov_pago = Movimiento(user_id=u_pagador.id, tipo=f"PAGO ENVIADO ({correlativo})", monto=monto)
            mov_cobro = Movimiento(user_id=u_cobrador.id, tipo=f"COBRO RECIBIDO ({correlativo})", monto=monto)
            
            db.session.add(mov_pago)
            db.session.add(mov_cobro)
            db.session.commit()
            
            return render_template('user/comprobante.html', c=correlativo, pagador=u_pagador, cobrador=u_cobrador, monto=monto, fecha=datetime.now())
        else:
            return "Saldo insuficiente."
    except Exception as e:
        return f"Error: {str(e)}"

# --- PANEL MAESTRO (EL BÚNKER) ---
@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    u = Usuario.query.get(session['user_id'])
    if not u or u.cedula != '13496133': return "Acceso prohibido."

    usuarios = Usuario.query.all()
    total_red = sum(user.saldo for user in usuarios)
    movimientos_vivos = Movimiento.query.order_by(Movimiento.id.desc()).limit(15).all()
    retiros_pendientes = Movimiento.query.filter_by(tipo="RETIRO PENDIENTE").all()

    return render_template('ceo/panel_maestro.html', 
                           u=u, 
                           usuarios=usuarios, 
                           total_red=total_red, 
                           movimientos=movimientos_vivos, 
                           retiros_pendientes=retiros_pendientes)
# ... (línea 183) retiros_pendientes=retiros_pendientes)

@app.route('/admin/usuarios_adn')
def usuarios_adn():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    u_ceo = Usuario.query.get(session['user_id'])
    if not u_ceo or u_ceo.cedula != '13496133': 
        return "ACCESO DENEGADO"

    todos_los_usuarios = Usuario.query.order_by(Usuario.nombre).all()
    return render_template('ceo/usuarios_adn.html', usuarios=todos_los_usuarios)

# ... (línea 194) return render_template('ceo/usuarios_adn.html', usuarios=todos_los_usuarios)

@app.route('/admin/update_config', methods=['POST'])
def update_config():
    if 'user_id' not in session: return jsonify({"error": "No login"}), 401
    u = Usuario.query.get(session['user_id'])
    if not u or u.cedula != '13496133': return jsonify({"error": "No CEO"}), 403

    data = request.get_json()
    field = data.get('field')
    value = data.get('value')

    mapping = {
        'socio1': 'socio1_rate', 'socio2': 'socio2_rate',
        'socio3': 'socio3_rate', 'socio4': 'socio4_rate',
        'socio5': 'socio5_rate', 'auto_cargas': 'auto_aprobacion',
        'auto_retiros': 'auto_retiros'
    }

    if field in mapping:
        setattr(u, mapping[field], value)
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    # Aquí buscamos tus datos de jefe
    u = Usuario.query.get(session['user_id'])
    
    # Seguridad: solo tú entras aquí
    if u.cedula != '13496133':
        return redirect(url_for('dashboard'))
        
    usuarios = Usuario.query.all()
    # Por ahora usamos una plantilla simple para que no te dé error
    return render_template('admin/panel.html', u=u, usuarios=usuarios)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
