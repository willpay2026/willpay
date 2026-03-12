from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- 1. CONFIGURACIÓN INICIAL (LA BASE) ---
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# PEGA AQUÍ TU "EXTERNAL DATABASE URL" DE RENDER
DB_URL = "postgresql://willpay_db_user:746J7SWXHVcv07Tt16AE5diK68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# --- 2. EL CEREBRO DE AUTOMATIZACIÓN (PARA DESCANSAR) ---
def inicializar_bunker():
    try:
        conn = get_db()
        cur = conn.cursor()
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
    except Exception as e:
        print(f"Error inicializando: {e}")

# Activamos el búnker al arrancar
inicializar_bunker()

# --- 3. RUTAS DE USUARIO (LO QUE VE EL CLIENTE) ---
@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    return render_template('acceso.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

# --- 4. RUTA DEL PANEL CEO (TU CENTRO DE MANDO APARTE) ---
@app.route('/panel_ceo')
def panel_ceo():
    # Nota: Aquí puedes poner una clave o verificar que seas tú
    conn = get_db()
    cur = conn.cursor()
    
    # Datos para tus recuadros y tabla
    cur.execute("SELECT * FROM config_ceo WHERE id = 1")
    config = cur.fetchone()
    
    cur.execute("SELECT SUM(saldo) as total FROM users")
    capital = cur.fetchone()['total'] or 0.00
    
    cur.execute("SELECT id, nombre, rol, cedula FROM users ORDER BY id DESC LIMIT 10")
    usuarios = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('panel_ceo.html', config=config, capital=capital, usuarios=usuarios)

# --- 5. ACCIONES DEL CEO ---
@app.route('/cargar_saldo', methods=['POST'])
def cargar_saldo():
    cedula = request.form.get('cedula')
    monto = float(request.form.get('monto'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET saldo = saldo + %s WHERE cedula = %s", (monto, cedula))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('panel_ceo'))

# --- 6. ARRANQUE DEL SISTEMA ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
