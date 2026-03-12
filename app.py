from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- 1. CONFIGURACIÓN ESTRUCTURAL ---
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    # Usa la variable de entorno de Render para máxima seguridad
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- 2. EL CEREBRO DEL BÚNKER (CREACIÓN DE TABLAS ACTUALIZADAS) ---
def inicializar_bunker():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Tabla de Configuración con los campos de tu captura móvil
        cur.execute("""
            CREATE TABLE IF NOT EXISTS config_ceo (
                id SERIAL PRIMARY KEY,
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

        # Tabla de Usuarios con Teléfono y Dinero Depositado
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
        print("✅ Búnker actualizado y listo para Will-Pay.")
    except Exception as e:
        print(f"❌ Error en el búnker: {e}")

# Arrancamos las tablas antes de cualquier petición
inicializar_bunker()

# --- 3. RUTAS DE DISEÑO (ESTÉTICA INTACTA) ---
@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    return render_template('acceso.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

# --- 4. PANEL CEO (EL MOTOR DE TUS CAPTURAS) ---
@app.route('/panel_ceo')
def panel_ceo():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # 1. Traer Configuración y Ganancias para Wilyanny
        cur.execute("SELECT * FROM config_ceo WHERE id = 1")
        config = cur.fetchone()
        
        # 2. Calcular Capital en Búnker y Dinero Depositado
        cur.execute("SELECT SUM(saldo) as total, SUM(depositado) as dep FROM users")
        res_totales = cur.fetchone()
        capital = res_totales['total'] if res_totales and res_totales['total'] else 0.00
        depositado = res_totales['dep'] if res_totales and res_totales['dep'] else 0.00
        
        # 3. Lista de Actividad en Vivo (10 en 10)
        cur.execute("SELECT id, nombre, rol, cedula, telefono FROM users ORDER BY id DESC LIMIT 10")
        usuarios = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Enviamos todas las variables al HTML
        return render_template('panel_ceo.html', 
                               config=config, 
                               capital=capital, 
                               depositado=depositado,
                               usuarios=usuarios)
    except Exception as e:
        return f"Error en el búnker: {e}"

# --- 5. ACCIONES DEL PANEL ---
@app.route('/cargar_saldo', methods=['POST'])
def cargar_saldo():
    cedula = request.form.get('cedula')
    monto = request.form.get('monto')
    if cedula and monto:
        try:
            monto_f = float(monto)
            conn = get_db()
            cur = conn.cursor()
            # Actualizamos saldo y el histórico de depositado
            cur.execute("""
                UPDATE users 
                SET saldo = saldo + %s, depositado = depositado + %s 
                WHERE cedula = %s
            """, (monto_f, monto_f, cedula))
            conn.commit()
            cur.close()
            conn.close()
        except: pass
    return redirect(url_for('panel_ceo'))

# --- 6. LANZAMIENTO ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
