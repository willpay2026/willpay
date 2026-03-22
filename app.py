from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
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
    
    tipo_usuario = db.Column(db.String(50)) 
    actividad_economica = db.Column(db.String(100)) 
    rif_juridico = db.Column(db.String(20)) 
    comision_rate = db.Column(db.Float, default=0.0) 
    
    banco = db.Column(db.String(50))
    telefono_pago = db.Column(db.String(20))
    cedula_pago = db.Column(db.String(20))

    auto_aprobacion = db.Column(db.Boolean, default=False) 
    auto_retiros = db.Column(db.Boolean, default=False)    
    
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
    db.create_all()

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

            tipo_final = 'CEO' if cedula_ingresada == '13496133' else tipo

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

@app.route('/login', methods=['POST'])
def login():
    cedula = request.form['cedula']
    password = request.form['password']
    user = Usuario.query.filter_by(cedula=cedula, password=password).first()
    
    if user:
        session['user_id'] = user.id
        if user.cedula == '13496133':
            return redirect(url_for('admin_panel'))
        return redirect(url_for('dashboard'))
    return "Credenciales incorrectas. <a href='/acceso'>Volver</a>"

# --- MUNDO USUARIO (LA BÓVEDA) ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    cliente = Usuario.query.get(session['user_id'])
    # Si el CEO entra aquí por error, lo mandamos a su sitio
    if cliente.cedula == '13496133': return redirect(url_for('admin_panel'))
    
    movs = Movimiento.query.filter_by(user_id=cliente.id).order_by(Movimiento.fecha.desc()).limit(10).all()
    return render_template('user/dashboard.html', cliente=cliente, movimientos=movs)

# --- MUNDO CEO (EL BÚNKER) ---
@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    jefe = Usuario.query.get(session['user_id'])
    
    if not jefe or jefe.cedula != '13496133':
        return redirect(url_for('dashboard'))
        
    usuarios_red = Usuario.query.all()
    total_red = db.session.query(func.sum(Usuario.saldo)).scalar() or 0.0
    movimientos_vivos = Movimiento.query.order_by(Movimiento.fecha.desc()).limit(20).all()
    retiros_pendientes = Movimiento.query.filter_by(status='PENDIENTE', tipo='RETIRO').all()

    return render_template('ceo/panel_ceo.html', 
                           jefe=jefe, 
                           usuarios=usuarios_red, 
                           total_red=total_red, 
                           movimientos=movimientos_vivos, 
                           retiros_pendientes=retiros_pendientes)

@app.route('/admin/usuarios_adn')
def usuarios_adn():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    jefe = Usuario.query.get(session['user_id'])
    if not jefe or jefe.cedula != '13496133': return "ACCESO DENEGADO"

    todos_los_usuarios = Usuario.query.order_by(Usuario.nombre).all()
    return render_template('ceo/usuarios_adn.html', jefe=jefe, usuarios=todos_los_usuarios)

@app.route('/admin/update_config', methods=['POST'])
def update_config():
    if 'user_id' not in session: return jsonify({"error": "No login"}), 401
    jefe = Usuario.query.get(session['user_id'])
    if not jefe or jefe.cedula != '13496133': return jsonify({"error": "No CEO"}), 403

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
        setattr(jefe, mapping[field], value)
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
