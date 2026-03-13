from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime

# 1. INICIO DEL SISTEMA
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# --- CONFIGURACIÓN DEL CEO ---
SISTEMA_TASAS = {'pagos': 3.0, 'retiros': 2.0, 'act_econ': 1.5}
MODO_PANICO = False 

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- RUTAS DE ACCESO ---
@app.route('/')
def splash():
    return render_template('auth/splash.html')

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

@app.route('/login', methods=['POST'])
def login():
    identificador = request.form.get('cedula')
    pin = request.form.get('pin')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE cedula = %s", (identificador,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and user['password'] == pin:
        session['user_id'] = user['id']
        session['user_rol'] = user['rol']
        if user['cedula'] == '13496133':
            return redirect(url_for('panel_ceo'))
        return redirect(url_for('dashboard'))
    return "Error: Credenciales no coinciden."

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
            WHERE emisor::text = %s::text OR receptor::text = %s::text 
            ORDER BY fecha DESC LIMIT 5
        """, (str(user['id']), str(user['id'])))
        movimientos = cur.fetchall()
    except Exception as e:
        return f"Error en Dashboard: {str(e)}"
    finally:
        cur.close()
        conn.close()
    
    return render_template('user/dashboard.html', u=user, movimientos=movimientos)

# --- MOTOR DE PAGOS ---
@app.route('/pagar')
def pagar():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('user/pagar.html')

@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    monto = float(request.form.get('monto'))
    receptor_cedula = request.form.get('cedula_receptor')
    emisor_id = session['user_id']
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT saldo FROM users WHERE id = %s", (emisor_id,))
        emisor = cur.fetchone()
        
        if emisor['saldo'] < monto:
            return "<h1>❌ Saldo Insuficiente</h1><a href='/dashboard'>Volver</a>"

        cur.execute("SELECT id FROM users WHERE cedula = %s", (receptor_cedula,))
        receptor = cur.fetchone()
        
        if not receptor:
            return "<h1>❌ Receptor no encontrado</h1><a href='/dashboard'>Volver</a>"

        ref_wp = f"WP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cur.execute("UPDATE users SET saldo = saldo - %s WHERE id = %s", (monto, emisor_id))
        cur.execute("UPDATE users SET saldo = saldo + %s WHERE id = %s", (monto, receptor['id']))
        cur.execute("""
            INSERT INTO transacciones (emisor, receptor, monto, tipo, referencia, estatus, fecha) 
            VALUES (%s, %s, %s, 'PAGO_MOVIL', %s, 'EXITOSO', NOW())
        """, (str(emisor_id), str(receptor['id']), monto, ref_wp))
        
        conn.commit()
        return redirect(url_for('dashboard'))
    except Exception as e:
        conn.rollback()
        return f"Error en transacción: {str(e)}"
    finally:
        cur.close()
        conn.close()

# --- PANEL CEO ---
@app.route('/panel_ceo')
def panel_ceo():
    if 'user_id' not in session or session.get('user_rol') != 'admin':
        return "Acceso denegado", 403
    return "<h1>Bienvenido CEO Wilfredo</h1><p>Panel en construcción.</p>"

# --- RUTA DE INYECCIÓN DE EMERGENCIA ---
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
                emisor VARCHAR(50),
                receptor VARCHAR(50),
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
        return "<h1>✅ Búnker Actualizado</h1><p>Tablas listas para transferencias.</p>"
    except Exception as e:
        return f"<h1>❌ Error</h1><p>{str(e)}</p>"

# --- CIERRE DEL MOTOR ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
