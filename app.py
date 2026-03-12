from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- 1. PRIMERO: CREAR LA APP ---
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# --- 2. SEGUNDO: CONEXIÓN AL BÚNKER ---
# Usando tu URL externa que vi en la captura
DB_URL = "postgresql://willpay_db_user:746J7SWXHVcv07Tt16AE5diK68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# --- 3. TERCERO: INICIALIZAR TABLAS AUTOMÁTICAMENTE ---
def inicializar_bunker():
    try:
        conn = get_db()
        cur = conn.cursor()
        # Creamos la tabla de automatización para que puedas descansar
        cur.execute("""
            CREATE TABLE IF NOT EXISTS config_ceo (
                id SERIAL PRIMARY KEY,
                auto_saldo BOOLEAN DEFAULT FALSE,
                auto_retiro BOOLEAN DEFAULT FALSE,
                p_pagos FLOAT DEFAULT 0.5,
                p_personal FLOAT DEFAULT 1.0,
                p_juridica FLOAT DEFAULT 2.5
            );
            INSERT INTO config_ceo (id, auto_saldo, auto_retiro) 
            VALUES (1, FALSE, FALSE) 
            ON CONFLICT (id) DO NOTHING;
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Búnker preparado y listo.")
    except Exception as e:
        print(f"❌ Error al preparar: {e}")

# Llamamos a la función
inicializar_bunker()

# --- 4. CUARTO: LAS RUTAS (EL MAPA) ---

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    return render_template('acceso.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/panel_ceo')
def panel_ceo():
    conn = get_db()
    cur = conn.cursor()
    # Leemos la configuración de los interruptores
    cur.execute("SELECT * FROM config_ceo WHERE id = 1")
    config = cur.fetchone()
    # Calculamos el capital total
    cur.execute("SELECT SUM(saldo) as total FROM users")
    capital = cur.fetchone()['total'] or 0.00
    # Obtenemos los últimos 10 usuarios
    cur.execute("SELECT id, nombre, rol, cedula FROM users ORDER BY id DESC LIMIT 10")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('panel_ceo.html', config=config, capital=capital, usuarios=usuarios)

# --- 5. QUINTO: ARRANQUE ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
