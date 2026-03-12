from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- 1. CONFIGURACIÓN ESTRUCTURAL ---
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    # Parche de seguridad para conexión SSL obligatoria en Render
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- 2. EL CEREBRO DEL BÚNKER (REPARACIÓN Y CREACIÓN) ---
def inicializar_bunker():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # 🛠️ REPARACIÓN AUTOMÁTICA: Crea columnas si la tabla ya existía
        print("🔧 Asegurando integridad del búnker...")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS depositado FLOAT DEFAULT 0.0;")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telefono VARCHAR(20);")
        cur.execute("ALTER TABLE config_ceo ADD COLUMN IF NOT EXISTS modo_panico BOOLEAN DEFAULT FALSE;")
        cur.execute("ALTER TABLE config_ceo ADD COLUMN IF NOT EXISTS ganancias_legado FLOAT DEFAULT 0.0;")
        cur.execute("ALTER TABLE config_ceo ADD COLUMN IF NOT EXISTS p_retiros FLOAT DEFAULT 1.0;")
        
        # 🏗️ CREACIÓN DE TABLAS (Estructura base)
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
        print("✅ Búnker blindado y actualizado correctamente.")
    except Exception as e:
        print(f"❌ Error en la base de datos: {e}")

# Ejecutamos la limpieza antes de arrancar la web
inicializar_bunker()

# --- 3. RUTAS DE DISEÑO (TU ESTÉTICA) ---
@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

# --- 4. PANEL CEO (TU CENTRO DE MANDO) ---
@app.route('/panel_ceo')
def panel_ceo():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Traer configuración y estado de pánico
        cur.execute("SELECT * FROM config_ceo WHERE id = 1")
        config = cur.fetchone()
        
        # Calcular Capital Total y Dinero Depositado
        cur.execute("SELECT SUM(saldo) as total, SUM(depositado) as dep FROM users")
        res = cur.fetchone()
        capital = res['total'] if res and res['total'] else 0.00
        depositado = res['dep'] if res and res['dep'] else 0.00
        
        # Listado de Actividad en Vivo (10 en 10)
        cur.execute("SELECT id, nombre, rol, cedula, telefono FROM users ORDER BY id DESC LIMIT 10")
        usuarios = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('panel_ceo.html', 
                               config=config, 
                               capital=capital, 
                               depositado=depositado, 
                               usuarios=usuarios)
    except Exception as e:
        return f"Error en el panel: {e}"

# --- 5. ACCIÓN DEL BOTÓN DE PÁNICO ---
@app.route('/activar_panico', methods=['POST'])
def activar_panico():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE config_ceo SET modo_panico = NOT modo_panico WHERE id = 1")
        conn.commit()
        cur.close()
        conn.close()
    except: pass
    return redirect(url_for('panel_ceo'))

# --- 6. CARGAR SALDO (CON BLOQUEO DE EMERGENCIA) ---
@app.route('/cargar_saldo', methods=['POST'])
def cargar_saldo():
    conn = get_db()
    cur = conn.cursor()
    
    # Check Modo Pánico
    cur.execute("SELECT modo_panico FROM config_ceo WHERE id = 1")
    en_panico = cur.fetchone()['modo_panico']
    
    if en_panico:
        cur.close()
        conn.close()
        return "⚠️ SISTEMA CONGELADO - MODO PÁNICO ACTIVO"

    cedula = request.form.get('cedula')
    monto = request.form.get('monto')
    
    if cedula and monto:
        try:
            monto_f = float(monto)
            cur.execute("""
                UPDATE users 
                SET saldo = saldo + %s, depositado = depositado + %s 
                WHERE cedula = %s
            """, (monto_f, monto_f, cedula))
            conn.commit()
        except: pass
    
    cur.close()
    conn.close()
    return redirect(url_for('panel_ceo'))

# --- 7. ARRANQUE DEL SERVIDOR ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
