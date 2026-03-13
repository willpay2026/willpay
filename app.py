from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime

# 1. DEFINICIÓN DE LA APP (ESTO ES LO QUE FALTA)
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# --- CONFIGURACIÓN GLOBAL DEL CEO ---
SISTEMA_TASAS = {
    'pagos': 3.0,
    'retiros': 2.0,
    'act_econ': 1.5
}
MODO_PANICO = False 

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

@app.before_request
def check_mantenimiento():
    rutas_libres = ['panel_ceo', 'static', 'login', 'acceso', 'registro', 'crear_cuenta', 'inyectar_datos']
    if MODO_PANICO and request.endpoint not in rutas_libres:
        return "<h1>⚠️ MANTENIMIENTO DE EMERGENCIA ACTIVADO</h1><p>Will-Pay está protegiendo el búnker.</p>", 503

# --- RUTAS DE ACCESO ---
@app.route('/')
def splash():
    return render_template('auth/splash.html')

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

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
    finally:
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
    try:
        cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cur.fetchone()
        
        cur.execute("""
            SELECT fecha, referencia, monto, estatus FROM transacciones 
            WHERE emisor = %s OR receptor = %s 
            ORDER BY fecha DESC LIMIT 5
        """, (user['id'], user['id']))
        movimientos = cur.fetchall()
    except Exception as e:
        return f"Error en Dashboard: {str(e)}"
    finally:
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
        cur.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Saldo insuficiente'})

    ref_wp = f"WP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    cur.execute("UPDATE users SET saldo = saldo - %s WHERE id = %s", (monto, emisor_id))
    cur.execute("""
        INSERT INTO transacciones (emisor, monto, tipo, referencia, estatus, fecha) 
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
        return "Acceso denegado: Solo el CEO tiene acceso aquí.", 403
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transacciones WHERE estatus = 'PENDIENTE' ORDER BY fecha DESC")
    pendientes = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('ceo/panel_ceo.html', tasas=SISTEMA_TASAS, pendientes=pendientes, panico=MODO_PANICO)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('acceso'))

# --- RUTA DE EMERGENCIA PARA CARGAR DATOS ---
@app.route('/inyectar_datos')
def inyectar_datos():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100),
                cedula VARCHAR(20) UNIQUE,
                telefono VARCHAR(20),
                password VARCHAR(20),
                rol VARCHAR(20) DEFAULT 'usuario',
                saldo DECIMAL(10,2) DEFAULT 0.0
            );
            CREATE TABLE IF NOT EXISTS transacciones (
                id SERIAL PRIMARY KEY,
                emisor INTEGER REFERENCES users(id),
                receptor INTEGER REFERENCES users(id),
                monto DECIMAL(10,2),
                tipo VARCHAR(50),
                referencia VARCHAR(100),
                estatus VARCHAR(20),
                fecha TIMESTAMP DEFAULT NOW()
            );
        """)
        cur.execute("""
            INSERT INTO users (nombre, cedula, telefono, password, rol, saldo)
            VALUES 
            ('Cliente Prueba', '101010', '04120000001', '1122', 'usuario', 500.00),
            ('Comercio Prueba', '202020', '04120000002', '3344', 'usuario', 0.00)
            ON CONFLICT (cedula) DO NOTHING;
        """)
        conn.commit()
        cur.close()
        conn.close()
        return "<h1>✅ Búnker Actualizado</h1><p>Tablas creadas y usuarios listos con nombres correctos.</p>"
    except Exception as e:
        return f"<h1>❌ Error</h1><p>{str(e)}</p>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
