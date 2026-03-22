from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import os
from datetime import datetime

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
    
    # Perfil y Ganancias (Tu Legado para Wilyanny)
    tipo_usuario = db.Column(db.String(50)) # PERSONAL, TECNICO, JURIDICO, CEO
    actividad_economica = db.Column(db.String(100)) 
    comision_rate = db.Column(db.Float, default=0.0)
    ganancias_acumuladas = db.Column(db.Float, default=0.0)
    
    # Datos de Pago Móvil (Banesco Wilfredo)
    banco = db.Column(db.String(50))
    telefono_pago = db.Column(db.String(20))
    cedula_pago = db.Column(db.String(20))

    # Interruptores del Búnker de Control
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
    referencia = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), default='PENDIENTE') # PENDIENTE, COMPLETADO, RECHAZADO
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
            ced_ing = request.form['cedula']
            tipo = request.form.get('tipo_usuario', 'PERSONAL')
            
            # Tasas por actividad económica
            comision = 1.2
            if tipo == 'TECNICO': comision = 1.8
            elif tipo == 'JURIDICO': comision = 3.0

            # Identificación del Fundador Wilfredo
            tipo_final = 'CEO' if ced_ing == '13496133' else tipo

            nuevo = Usuario(
                nombre=request.form['nombre'].upper(),
                cedula=ced_ing,
                password=request.form['password'],
                tipo_usuario=tipo_final,
                actividad_economica=request.form.get('actividad_economica', 'General'),
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
    user = Usuario.query.filter_by(cedula=request.form['cedula'], password=request.form['password']).first()
    if user:
        session['user_id'] = user.id
        if user.tipo_usuario == 'CEO':
            return redirect(url_for('admin_panel'))
        return redirect(url_for('dashboard'))
    return "Credenciales incorrectas. <a href='/acceso'>Volver</a>"

# --- MUNDO USUARIO ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    cliente = Usuario.query.get(session['user_id'])
    movs = Movimiento.query.filter_by(user_id=cliente.id).order_by(Movimiento.fecha.desc()).limit(10).all()
    return render_template('user/dashboard.html', cliente=cliente, movimientos=movs)

# --- EL BÚNKER DEL PODER (MUNDO CEO) ---
@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    jefe = Usuario.query.get(session['user_id'])
    
    if not jefe or jefe.tipo_usuario != 'CEO':
        return redirect(url_for('dashboard'))
        
    usuarios_red = Usuario.query.filter(Usuario.tipo_usuario != 'CEO').all()
    # Capital total en el sistema
    total_red = db.session.query(func.sum(Usuario.saldo)).scalar() or 0.0
    # Últimos movimientos para el feed en vivo
    movs_vivos = Movimiento.query.order_by(Movimiento.fecha.desc()).limit(10).all()
    
    return render_template('ceo/panel_maestro.html', 
                           u=jefe, 
                           usuarios=usuarios_red, 
                           total_red=total_red, 
                           movimientos=movs_vivos)

# --- ACCIONES DEL BÚNKER (APROBAR/RECHAZAR) ---
@app.route('/admin/aprobar/<int:mov_id>')
def aprobar_movimiento(mov_id):
    if 'user_id' not in session: return redirect(url_for('login_page'))
    jefe = Usuario.query.get(session['user_id'])
    if not jefe or jefe.tipo_usuario != 'CEO': return "DENEGADO"

    mov = Movimiento.query.get(mov_id)
    if mov and mov.status == 'PENDIENTE':
        user_rec = Usuario.query.get(mov.user_id)
        user_rec.saldo += mov.monto
        mov.status = 'COMPLETADO'
        
        # El sistema suma tu margen operativo al legado
        jefe.ganancias_acumuladas += (mov.monto * 0.01) 
        db.session.commit()
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/rechazar/<int:mov_id>')
def rechazar_movimiento(mov_id):
    if 'user_id' not in session: return redirect(url_for('login_page'))
    jefe = Usuario.query.get(session['user_id'])
    if not jefe or jefe.tipo_usuario != 'CEO': return "DENEGADO"

    mov = Movimiento.query.get(mov_id)
    if mov:
        mov.status = 'RECHAZADO'
        db.session.commit()
    return redirect(url_for('admin_panel'))

# --- RECARGAS Y SEGURIDAD DE REFERENCIA ---
@app.route('/procesar_recarga', methods=['POST'])
def procesar_recarga():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    monto = float(request.form['monto'])
    ref = request.form.get('referencia', f"REF-{random.randint(1000,9999)}")
    
    # Comprobar si la captura/referencia ya se usó
    existe = Movimiento.query.filter_by(referencia=ref).first()
    if existe:
        return "Error: Esta referencia ya fue procesada anteriormente."

    nueva_recarga = Movimiento(
        user_id=session['user_id'],
        tipo='RECARGA',
        monto=monto,
        referencia=ref,
        status='PENDIENTE'
    )
    
    db.session.add(nueva_recarga)
    db.session.commit()
    
    # Chequeo de Auto-Aprobación en el Búnker
    jefe = Usuario.query.filter_by(tipo_usuario='CEO').first()
    if jefe and jefe.auto_aprobacion:
        confirmar_pago_directo(nueva_recarga.id)
        
    return redirect(url_for('dashboard'))

def confirmar_pago_directo(mov_id):
    mov = Movimiento.query.get(mov_id)
    if mov:
        user = Usuario.query.get(mov.user_id)
        user.saldo += mov.monto
        mov.status = 'COMPLETADO'
        db.session.commit()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
