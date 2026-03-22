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
    cedula = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(100))
    saldo = db.Column(db.Float, default=0.0)
    
    # Perfil y Ganancias
    tipo_usuario = db.Column(db.String(50)) # PERSONAL, TECNICO, JURIDICO, CEO
    actividad_economica = db.Column(db.String(100)) 
    comision_rate = db.Column(db.Float, default=0.0) # Tasa de la actividad
    ganancias_acumuladas = db.Column(db.Float, default=0.0) # El Neto Ganancias
    
    # Datos de Pago Móvil Wilfredo
    banco = db.Column(db.String(50))
    telefono_pago = db.Column(db.String(20))
    cedula_pago = db.Column(db.String(20))

    # Interruptores del Búnker
    auto_aprobacion = db.Column(db.Boolean, default=False) 
    auto_retiros = db.Column(db.Boolean, default=False)    
    
    # Tasas de los 5 Socios Reservados
    socio1_rate = db.Column(db.Float, default=0.0)
    socio2_rate = db.Column(db.Float, default=0.0)
    socio3_rate = db.Column(db.Float, default=0.0)
    socio4_rate = db.Column(db.Float, default=0.0)
    socio5_rate = db.Column(db.Float, default=0.0)

class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    tipo = db.Column(db.String(100)) # PAGO, RECARGA, RETIRO
    monto = db.Column(db.Float)
    referencia = db.Column(db.String(50), unique=True) # Bloqueo de duplicados
    status = db.Column(db.String(20), default='PENDIENTE') 
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario', backref='movimientos')

with app.app_context():
    db.create_all()

# --- LÓGICA DE NAVEGACIÓN ---
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
            ced_ing = request.form['cedula']
            tipo = request.form.get('tipo_usuario', 'PERSONAL')
            
            # Configuración de Tasas por Actividad Económica
            comision = 1.2
            if tipo == 'TECNICO': comision = 1.8
            elif tipo == 'JURIDICO': comision = 3.0

            tipo_final = 'CEO' if ced_ing == '13496133' else tipo

            nuevo = Usuario(
                nombre=request.form['nombre'].upper(),
                cedula=ced_ing,
                password=request.form['password'],
                tipo_usuario=tipo_final,
                actividad_economica=request.form.get('actividad_economica', 'Comercio General'),
                comision_rate=comision,
                banco=request.form['banco'],
                telefono_pago=request.form['telefono_pago'],
                cedula_pago=request.form['cedula_pago']
            )
            db.session.add(nuevo)
            db.session.commit()
            return redirect(url_for('login_page'))
        except Exception as e:
            return f"Error: {str(e)}"
    return render_template('auth/registro.html')

@app.route('/login', methods=['POST'])
def login():
    user = Usuario.query.filter_by(cedula=request.form['cedula'], password=request.form['password']).first()
    if user:
        session['user_id'] = user.id
        return redirect(url_for('admin_panel' if user.tipo_usuario == 'CEO' else 'dashboard'))
    return "Error de acceso."

# --- EL BÚNKER (TU RECUADRO DEL PODER) ---
@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    jefe = Usuario.query.get(session['user_id'])
    if not jefe or jefe.tipo_usuario != 'CEO': return redirect(url_for('dashboard'))
    
    # Cálculos para los recuadros de poder
    total_red = db.session.query(func.sum(Usuario.saldo)).scalar() or 0.0
    usuarios_red = Usuario.query.filter(Usuario.tipo_usuario != 'CEO').all()
    movs = Movimiento.query.order_by(Movimiento.fecha.desc()).limit(15).all()
    
    # Dinero en transacción (Pendientes)
    en_transaccion = db.session.query(func.sum(Movimiento.monto)).filter_by(status='PENDIENTE').scalar() or 0.0

    return render_template('ceo/panel_maestro.html', 
                           u=jefe, 
                           usuarios=usuarios_red, 
                           total_red=total_red, 
                           movimientos=movs,
                           en_transaccion=en_transaccion)

# --- SISTEMA DE APROBACIÓN MANUAL ---
@app.route('/admin/aprobar/<int:mov_id>')
def aprobar_movimiento(mov_id):
    if 'user_id' not in session: return redirect(url_for('login_page'))
    jefe = Usuario.query.get(session['user_id'])
    mov = Movimiento.
