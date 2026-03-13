from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy' # El legado para Wilyanny

# --- CONFIGURACIÓN DE VARIABLES CEO ---
SISTEMA_TASAS = {
    'pagos': 3.0,
    'retiros': 2.0,
    'act_econ': 1.5
}
MODO_PANICO = False

# --- CONEXIÓN A BASE DE DATOS ---
def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- MIDDLEWARE DE SEGURIDAD (PÁNICO) ---
@app.before_request
def check_mantenimiento():
    if MODO_PANICO and request.endpoint not in ['panel_ceo', 'static', 'login', 'acceso']:
        return "<h1>⚠️ SISTEMA EN MANTENIMIENTO DE EMERGENCIA</h1><p>Will-Pay está protegiendo tu capital. Volvemos pronto.</p>", 503

# --- RUTAS DE NAVEGACIÓN Y ACCESO ---
@app.route('/')
def splash():
    return render_template('auth/splash.html')

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

@app.route('/registro')
def registro():
    return render_template('auth/registro.html')

@app.route('/login', methods=['POST'])
def login():
    identificador = request.form.get('cedula') # Puede ser telf o cédula
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
        # Si es Wilfredo, va al Búnker CEO
        if user['cedula'] == '13496133':
            return redirect(url_for('panel_ceo'))
        return redirect(url_for('dashboard'))
    return "Credenciales incorrectas"

# --- PANEL DE USUARIO (DASHBOARD) ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    
    # Buscamos últimos movimientos
    cur.execute("SELECT * FROM transacciones WHERE emisor_id = %s OR receptor_id = %s ORDER BY fecha DESC LIMIT 5", 
                (user['id'], user['id']))
    movimientos = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('user/dashboard.html', u=user, movimientos=movimientos)

# --- FASE 3 Y 4: TRANSACCIONES Y BEEP ---
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

    # Registro de auditoría con correlativo WP
    ref_wp = f"WP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
