from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'willpay_ultra_secret_2026'

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///willpay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
    tipo = db.Column(db.String(50))
    monto = db.Column(db.Float)
    referencia = db.Column(db.String(20))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario', backref='movimientos')

with app.app_context():
    db.create_all()

# --- RUTAS DE ACCESO ---

@app.route('/')
def index():
    # CAMBIO AQUÍ: Ahora carga el Splash en lugar de saltar al login
    return render_template('common/splash.html')

@app.route('/acceso')
def login_page():
    return render_template('auth/acceso.html')

@app.route('/registro')
def registro_page():
    return render_template('auth/registro.html')

@app.route('/terminos')
def terminos():
    return render_template('common/terminos.html')

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
        return "Error: Datos incorrectos."

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    u = Usuario.query.get(session['user_id'])
    movs = Movimiento.query.filter_by(user_id=u.id).order_by(Movimiento.fecha.desc()).limit(10).all()
    return render_template('user/dashboard.html', u=u, movimientos=movs)

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    u = Usuario.query.get(session['user_id'])
    if u.cedula != '13496133': return "Acceso prohibido."
    usuarios = Usuario.query.all()
    total_red = sum(user.saldo for user in usuarios)
    retiros = Movimiento.query.filter_by(tipo="RETIRO PENDIENTE").all()
    return render_template('ceo/panel_maestro.html', usuarios=usuarios, total_red=total_red, retiros_pendientes=retiros)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)
