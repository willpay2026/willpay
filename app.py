from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy' #

# --- CONFIGURACIÓN GLOBAL DEL CEO ---
# Se inicializan con tus valores por defecto
SISTEMA_TASAS = {
    'pagos': 3.0,
    'retiros': 2.0,
    'act_econ': 1.5
}
MODO_PANICO = False #

# --- CONEXIÓN A LA BASE DE DATOS ---
def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- PROTECCIÓN DE SEGURIDAD (BOTÓN DE PÁNICO) ---
@app.before_request
def check_mantenimiento():
    # Si el pánico está activo, nadie pasa excepto para el panel de control o login
    rutas_libres = ['panel_ceo', 'static', 'login', 'acceso', 'panico_toggle']
    if MODO_PANICO and request.endpoint not in rutas_libres:
        return "<h1>⚠️ MANTENIMIENTO DE EMERGENCIA ACTIVADO</h1><p>Will-Pay está protegiendo el búnker. Reintenta en unos minutos.</p>", 503

# --- RUTAS DE ACCESO (SPLASH Y LOGIN) ---
@app.route('/')
def splash():
    return render_template('auth/splash.html') #

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html') #

@app.route('/login', methods=['POST'])
def login():
    identificador = request.form.get('cedula') # Soporta Cédula o Telf
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
        # Acceso directo para Wilfredo
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
    
    # Historial para la tabla de "Últimos Movimientos"
    cur.execute("""
        SELECT * FROM transacciones 
        WHERE emisor_id = %s OR receptor_id = %s 
        ORDER BY fecha DESC LIMIT 5
    """, (user['id'], user['id']))
    movimientos = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('user/dashboard.html', u=user, movimientos=movimientos)

# --- MOTOR DE TRANSACCIONES (PAGO QR / BEEP) ---
@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    if 'user_id' not in session: return jsonify({'success': False})
    
    data = request.get_json()
    monto = float(data['monto'])
    emisor_id = session['user_id']
    
    conn = get_db()
    cur = conn.cursor()
    
    # Validación Búnker: Saldo Real
    cur.execute("SELECT saldo FROM users WHERE id = %s", (emisor_id,))
    emisor = cur.fetchone()
    
    if emisor['saldo'] < monto:
        return jsonify({'success': False, 'message': 'Saldo insuficiente'})

    # Generación de Correlativo WP para Auditoría
    ref_wp = f"WP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Ejecución de doble asiento
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

# --- TICKETS DE AUDITORÍA ---
@app.route('/comprobante/<int:t_id>')
def comprobante(t_id):
    if 'user_id' not in session: return redirect(url_for('acceso'))
    # Jala los datos de la transacción para el ticket blanco
    return render_template('user/comprobante.html', t_id=t_id)

@app.route('/ticket_bienvenida')
def ticket_bienvenida():
    return render_template('user/ticket_bienvenida.html') #

# --- PANEL CEO (TABLERO DEFINITIVO WILFREDO) ---
@app.route('/panel_ceo')
def panel_ceo():
    if 'user_id' not in session or session.get('user_rol') != 'admin':
        return "Acceso denegado: Solo el CEO tiene acceso aquí.", 403
    
    conn = get_db()
    cur = conn.cursor()
    # Ver pagos por aprobar
    cur.execute("SELECT * FROM transacciones WHERE estatus = 'PENDIENTE' ORDER BY fecha DESC")
    pendientes = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('ceo/panel_ceo.html', tasas=SISTEMA_TASAS, pendientes=pendientes, panico=MODO_PANICO)

@app.route('/panico_toggle', methods=['POST'])
def panico_toggle():
    global MODO_PANICO
    MODO_PANICO = not MODO_PANICO #
    return jsonify({'status': MODO_PANICO})

@app.route('/actualizar_tasa', methods=['POST'])
def actualizar_tasa():
    data = request.get_json()
    SISTEMA_TASAS[data['tipo']] = float(data['valor']) #
    return jsonify({'success': True})

# --- RECARGAS (DATOS PAGO MÓVIL) ---
@app.route('/reportar_pago', methods=['POST'])
def reportar_pago():
    ref = request.form.get('referencia')
    monto = request.form.get('monto')
    user_id = session['user_id']
    
    conn = get_db()
    cur = conn.cursor()
    # Verificar que no se repita la referencia
    cur.execute("SELECT id FROM transacciones WHERE referencia = %s", (ref,))
    if cur.fetchone():
        return "Error: Esta referencia ya fue utilizada anteriormente."
        
    cur.execute("""
        INSERT INTO transacciones (emisor_id, monto, referencia, estatus, tipo, fecha) 
        VALUES (%s, %s, %s, 'PENDIENTE', 'RECARGA', NOW())
    """, (user_id, monto, ref))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('acceso'))

if __name__ == '__main__':
    # Configuración para Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
