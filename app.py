from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'willpay_ultra_secret_2026'

# CONFIGURACIÓN DE BASE DE DATOS
# En Render, esto leerá automáticamente tu base de datos de PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE DATOS ---

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20), unique=True) # ID 13496133 es el CEO
    password = db.Column(db.String(100))
    saldo = db.Column(db.Float, default=0.0)
    # CAMPOS BANCARIOS (NUEVOS)
    banco = db.Column(db.String(50))
    telefono_pago = db.Column(db.String(20))
    cedula_pago = db.Column(db.String(20))

class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    tipo = db.Column(db.String(50)) # PAGO, COBRO, RECARGA, RETIRO
    monto = db.Column(db.Float)
    referencia = db.Column(db.String(20))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    # Relación para que el CEO vea quién pide el retiro
    usuario = db.relationship('Usuario', backref='movimientos')

# --- INICIALIZACIÓN ---
with app.app_context():
    # db.drop_all() # <--- DESCOMENTA SOLO SI QUIERES REINICIAR TODO
    db.create_all()

# --- RUTAS DE ACCESO (templates/auth) ---

@app.route('/')
def index():
    return redirect(url_for('login_page'))

@app.route('/acceso')
def login_page():
    return render_template('auth/acceso.html')

@app.route('/registro')
def registro_page():
    return render_template('auth/registro.html')

@app.route('/login', methods=['POST'])
def login():
    cedula = request.form['cedula']
    password = request.form['password']
    user = Usuario.query.filter_by(cedula=cedula, password=password).first()
    if user:
        session['user_id'] = user.id
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
        return "Error: Cédula ya registrada o datos incompletos."

# --- RUTAS DE USUARIO (templates/user) ---

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    u = Usuario.query.get(session['user_id'])
    movs = Movimiento.query.filter_by(user_id=u.id).order_by(Movimiento.fecha.desc()).limit(10).all()
    return render_template('user/dashboard.html', u=u, movimientos=movs)

@app.route('/ejecutar_pago', methods=['POST'])
def ejecutar_pago():
    data = request.json
    emisor_cedula = data.get('emisor')
    monto = float(data.get('monto'))
    receptor_id = session.get('user_id')
    
    emisor = Usuario.query.filter_by(cedula=emisor_cedula).first()
    receptor = Usuario.query.get(receptor_id)
    
    if emisor and emisor.saldo >= monto:
        ref = f"WP-{random.randint(100000, 999999)}"
        emisor.saldo -= monto
        receptor.saldo += monto
        m1 = Movimiento(user_id=emisor.id, tipo="PAGO ENVIADO", monto=monto, referencia=ref)
        m2 = Movimiento(user_id=receptor.id, tipo="PAGO RECIBIDO", monto=monto, referencia=ref)
        db.session.add(m1)
        db.session.add(m2)
        db.session.commit()
        return jsonify({'status': 'ok', 'referencia': ref})
    return jsonify({'status': 'error', 'msg': 'Saldo insuficiente'})

@app.route('/solicitar_retiro', methods=['POST'])
def solicitar_retiro():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    u = Usuario.query.get(session['user_id'])
    monto = float(request.form['monto'])
    if u.saldo >= monto:
        ref = f"RET-{random.randint(1000, 9999)}"
        u.saldo -= monto
        mov = Movimiento(user_id=u.id, tipo="RETIRO PENDIENTE", monto=monto, referencia=ref)
        db.session.add(mov)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return "Saldo insuficiente."

# --- RUTAS DE CONTROL (templates/ceo) ---

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    u = Usuario.query.get(session['user_id'])
    # SOLO TÚ (WILFREDO) PUEDES ENTRAR
    if u.cedula != '13496133': return "Acceso prohibido."
    
    usuarios = Usuario.query.all()
    total_red = sum(user.saldo for user in usuarios)
    retiros = Movimiento.query.filter_by(tipo="RETIRO PENDIENTE").all()
    return render_template('ceo/panel_maestro.html', usuarios=usuarios, total_red=total_red, retiros_pendientes=retiros)

@app.route('/confirmar_pago_ceo', methods=['POST'])
def confirmar_pago_ceo():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    mov_id = request.form.get('mov_id')
    movimiento = Movimiento.query.get(mov_id)
    if movimiento:
        movimiento.tipo = "RETIRO COMPLETADO"
        db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)
