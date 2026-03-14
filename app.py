from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import qrcode
import io
import base64

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# --- CONEXIÓN A LA BASE DE DATOS ---
def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- REPARACIÓN AUTOMÁTICA Y CARGA DE DATOS (PARA QUE NO SE JODA NADA) ---
@app.route('/inyectar_datos')
def inyectar_datos():
    conn = get_db()
    cur = conn.cursor()
    try:
        # 1. Crear tabla de usuarios si no existe
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100),
                cedula VARCHAR(20) UNIQUE,
                password VARCHAR(20),
                saldo DECIMAL(12,2) DEFAULT 0.00,
                rol VARCHAR(20) DEFAULT 'CLIENTE'
            );
        """)
        # 2. Crear tabla de transacciones con TODAS las columnas necesarias
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transacciones (
                id SERIAL PRIMARY KEY,
                emisor VARCHAR(20),
                receptor VARCHAR(20),
                monto DECIMAL(12,2),
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referencia VARCHAR(20),
                estatus VARCHAR(20) DEFAULT 'EXITOSO',
                tipo VARCHAR(20) DEFAULT 'EGRESO'
            );
        """)
        # 3. REPARACIÓN: Agregar columnas faltantes si la tabla ya existía
        cur.execute("ALTER TABLE transacciones ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) DEFAULT 'EGRESO';")
        cur.execute("ALTER TABLE transacciones ADD COLUMN IF NOT EXISTS estatus VARCHAR(20) DEFAULT 'EXITOSO';")
        cur.execute("ALTER TABLE transacciones ADD COLUMN IF NOT EXISTS referencia VARCHAR(20);")
        
        # 4. Crear usuarios de prueba si no existen
        cur.execute("INSERT INTO users (nombre, cedula, password, saldo, rol) VALUES ('WILFREDO', '13496133', '1234', 1000.00, 'ADMIN') ON CONFLICT (cedula) DO NOTHING;")
        cur.execute("INSERT INTO users (nombre, cedula, password, saldo, rol) VALUES ('CLIENTE PRUEBA', '101010', '1122', 500.00, 'CLIENTE') ON CONFLICT (cedula) DO NOTHING;")
        cur.execute("INSERT INTO users (nombre, cedula, password, saldo, rol) VALUES ('WILL-PAY SERV', '202020', '3344', 0.00, 'COMERCIO') ON CONFLICT (cedula) DO NOTHING;")
        
        conn.commit()
        return "✅ Búnker Actualizado: Columnas creadas y usuarios listos. Ve al /acceso"
    except Exception as e:
        return f"Error reparando el búnker: {e}"
    finally:
        cur.close()
        conn.close()

# --- RUTAS DE ACCESO ---
@app.route('/')
def index():
    return redirect(url_for('acceso'))

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

@app.route('/login', methods=['POST'])
def login():
    cedula = request.form.get('cedula')
    pin = request.form.get('pin')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE cedula = %s AND password = %s", (cedula, pin))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        session['user_id'] = user['id']
        session['cedula'] = user['cedula']
        return redirect(url_for('dashboard'))
    return "Credenciales incorrectas."

# --- DASHBOARD (TU DISEÑO SERIO) ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    # Buscamos movimientos por cédula para que salgan ingresos y egresos
    cur.execute("""
        SELECT fecha, referencia, monto, estatus, tipo 
        FROM transacciones 
        WHERE emisor = %s OR receptor = %s 
        ORDER BY fecha DESC LIMIT 10
    """, (user['cedula'], user['cedula']))
    movimientos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('user/dashboard.html', u=user, movimientos=movimientos)

# --- PROCESAR PAGO Y GENERAR COMPROBANTE ---
@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    receptor_ced = request.form.get('cedula_receptor')
    monto = float(request.form.get('monto'))
    emisor_ced = session['cedula']
    referencia = f"WP{datetime.datetime.now().strftime('%M%S%f')[:6]}"

    conn = get_db()
    cur = conn.cursor()
    try:
        # Restar al emisor
        cur.execute("UPDATE users SET saldo = saldo - %s WHERE cedula = %s AND saldo >= %s", (monto, emisor_ced, monto))
        if cur.rowcount == 0: return "Saldo insuficiente."
        
        # Sumar al receptor
        cur.execute("UPDATE users SET saldo = saldo + %s WHERE cedula = %s", (monto, receptor_ced))
        
        # Registrar Transacción (Doble registro para el historial serio)
        cur.execute("""
            INSERT INTO transacciones (emisor, receptor, monto, referencia, tipo, estatus) 
            VALUES (%s, %s, %s, %s, 'EGRESO', 'EXITOSO')
        """, (emisor_ced, receptor_ced, monto, referencia))
        
        conn.commit()
        return redirect(url_for('comprobante', ref=referencia))
    except Exception as e:
        conn.rollback()
        return f"Error en transacción: {e}"
    finally:
        cur.close()
        conn.close()

@app.route('/comprobante/<ref>')
def comprobante(ref):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.*, u_e.nombre as emisor_nombre, u_r.nombre as receptor_nombre 
        FROM transacciones t
        LEFT JOIN users u_e ON t.emisor = u_e.cedula
        LEFT JOIN users u_r ON t.receptor = u_r.cedula
        WHERE t.referencia = %s
    """, (ref,))
    tx = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('user/comprobante.html', tx=tx)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('acceso'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
