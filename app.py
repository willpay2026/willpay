from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# --- CONFIGURACIÓN GLOBAL DEL CEO ---
SISTEMA_TASAS = {
    'pagos': 3.0,
    'retiros': 2.0,
    'act_econ': 1.5
}
MODO_PANICO = False 

# --- CONEXIÓN A LA BASE DE DATOS ---
def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- PROTECCIÓN DE SEGURIDAD (BOTÓN DE PÁNICO) ---
@app.before_request
def check_mantenimiento():
    rutas_libres = ['panel_ceo', 'static', 'login', 'acceso', 'panico_toggle', 'registro', 'crear_cuenta']
    if MODO_PANICO and request.endpoint not in rutas_libres:
        return "<h1>⚠️ MANTENIMIENTO DE EMERGENCIA ACTIVADO</h1><p>Will-Pay está protegiendo el búnker. Reintenta en unos minutos.</p>", 503

# --- RUTAS DE ACCESO ---
@app.route('/')
def splash():
    return render_template('auth/splash.html')

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

# --- ESTA ES LA RUTA QUE FALTABA ---
@app.route('/registro')
def registro():
    return render_template('auth/registro.html')

@app.route('/crear_cuenta', methods=['POST'])
def crear_cuenta():
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    telefono = request.form.get('telefono')
    tipo = request.form.get('tipo_usuario')
    pin = request.form.get('pin')
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (nombre, cedula, telefono, rol, password, saldo) 
            VALUES (%s, %s, %s, %s, %s, 0.0)
        """, (nombre, cedula, telefono, tipo, pin))
        conn.commit()
        exito = True
    except:
        conn.rollback()
        exito = False
    cur.close()
    conn.close()
    
    if exito:
        return redirect(url_for('acceso'))
    return "Error al crear la cuenta. Posiblemente la cédula o teléfono ya existen."

@app.route('/login', methods=['POST'])
def login():
    identificador = request.form.get('cedula')
    pin = request.form.get('pin')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE cedula = %s OR telefono = %s", (identificador, identificador))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and user['password'] == pin:
        session['user_id'] = user['id']
        session['user_rol'] = user['rol']
        if user['cedula'] == '13496133':
            return redirect(url_for('panel_ceo'))
        return redirect(url_for('dashboard'))
    return "Error: Credenciales no coinciden en el búnker."

# --- PANEL DE USUARIO (DASHBOARD) ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    
    cur.execute("""
        SELECT * FROM transacciones 
        WHERE emisor_id = %s OR receptor_id = %s 
        ORDER BY fecha DESC LIMIT 5
    """, (user['id'], user['id']))
    movimientos = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('user/dashboard.html', u=user, movimientos=movimientos)

# --- MOTOR DE TRANSACCIONES ---
@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    if 'user_id' not in session: return jsonify({'success': False})
    
    data = request.get_json()
    monto = float(data['monto'])
    emisor_id = session['user_id']
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT saldo FROM users WHERE id = %s", (emisor_id,))
    emisor = cur.fetchone()
    
    if emisor['saldo'] < monto:
        return jsonify({'success': False, 'message': 'Saldo insuficiente'})

    ref_wp = f"WP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    cur.execute("UPDATE users SET saldo = saldo - %s WHERE id = %s", (monto, emisor_id))
    cur.execute("""
        INSERT INTO transacciones (emisor_id, monto, tipo, referencia, estatus, fecha) 
        VALUES (%s, %s, 'PAGO_QR', %s, 'EXITOSO', NOW()) RETURNING id
    """, (emisor_id, monto, ref_wp))
    
    t_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'success': True, 't_id': t_id})

# --- TICKETS Y PANEL CEO ---
@app.route('/comprobante/<int:t_id>')
def comprobante(t_id):
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('user/comprobante.html', t_id=t_id)

@app.route('/panel_ceo')
def panel_ceo():
    if 'user_id' not in session or session.get('user_rol') != 'admin':
        return "Acceso den
