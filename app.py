from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime

# 1. INICIO DEL SISTEMA (Primero definimos la app)
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
        
        # Corregido: 'emisor' y 'receptor' para que coincida con tu DB
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
        # Crear Tablas con nombres definitivos
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
        # Insertar usuarios de prueba
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
        return "<h1>✅ Búnker Listo</h1><p>Tablas y usuarios cargados. Ya puedes entrar.</p>"
    except Exception as e:
        return f"<h1>❌ Error</h1><p>{str(e)}</p>"

# --- CIERRE DEL MOTOR ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
