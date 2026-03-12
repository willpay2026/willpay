from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- 1. EL CEREBRO CON BOTÓN DE PÁNICO ---
def inicializar_bunker():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Tabla de Configuración con MODO PÁNICO
        cur.execute("""
            CREATE TABLE IF NOT EXISTS config_ceo (
                id SERIAL PRIMARY KEY,
                modo_panico BOOLEAN DEFAULT FALSE,
                auto_saldo BOOLEAN DEFAULT FALSE,
                auto_retiro BOOLEAN DEFAULT FALSE,
                p_pagos FLOAT DEFAULT 0.5,
                p_retiros FLOAT DEFAULT 1.0,
                p_personal FLOAT DEFAULT 1.0,
                p_juridica FLOAT DEFAULT 2.5,
                ganancias_legado FLOAT DEFAULT 0.0
            );
            INSERT INTO config_ceo (id) VALUES (1) ON CONFLICT (id) DO NOTHING;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100),
                cedula VARCHAR(20) UNIQUE,
                telefono VARCHAR(20),
                rol VARCHAR(20) DEFAULT 'personal',
                saldo FLOAT DEFAULT 0.0,
                depositado FLOAT DEFAULT 0.0,
                password TEXT
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Búnker con Protocolo de Pánico activado.")
    except Exception as e:
        print(f"❌ Error: {e}")

inicializar_bunker()

# --- 2. RUTAS DE DISEÑO ---
@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

# --- 3. PANEL CEO CON CONTROL DE EMERGENCIA ---
@app.route('/panel_ceo')
def panel_ceo():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM config_ceo WHERE id = 1")
        config = cur.fetchone()
        
        cur.execute("SELECT SUM(saldo) as total, SUM(depositado) as dep FROM users")
        res = cur.fetchone()
        capital = res['total'] if res and res['total'] else 0.00
        depositado = res['dep'] if res and res['dep'] else 0.00
        
        cur.execute("SELECT id, nombre, rol, cedula, telefono FROM users ORDER BY id DESC LIMIT 10")
        usuarios = cur.fetchall()
        
        cur.close()
        conn.close()
        return render_template('panel_ceo.html', config=config, capital=capital, depositado=depositado, usuarios=usuarios)
    except Exception as e:
        return f"Error: {e}"

# --- 4. LÓGICA DEL BOTÓN DE PÁNICO ---
@app.route('/activar_panico', methods=['POST'])
def activar_panico():
    try:
        conn = get_db()
        cur = conn.cursor()
        # Cambiamos el estado del pánico (Si está en False pasa a True)
        cur.execute("UPDATE config_ceo SET modo_panico = NOT modo_panico WHERE id = 1")
        conn.commit()
        cur.close()
        conn.close()
    except: pass
    return redirect(url_for('panel_ceo'))

# --- 5. CARGAR SALDO (BLOQUEADO SI HAY PÁNICO) ---
@app.route('/cargar_saldo', methods=['POST'])
def cargar_saldo():
    # Primero revisamos si el búnker está bloqueado
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT modo_panico FROM config_ceo WHERE id = 1")
    bloqueo = cur.fetchone()['modo_panico']
    
    if bloqueo:
        cur.close()
        conn.close()
        return "⚠️ SISTEMA BLOQUEADO POR EL CEO - MODO PÁNICO ACTIVO"

    cedula = request.form.get('cedula')
    monto = request.form.get('monto')
    if cedula and monto:
        cur.execute("UPDATE users SET saldo = saldo + %s, depositado = depositado + %s WHERE cedula = %s", (float(monto), float(monto), cedula))
        conn.commit()
    
    cur.close()
    conn.close()
    return redirect(url_for('panel_ceo'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
