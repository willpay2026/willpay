from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- 1. CONSTRUCCIÓN DE LAS COLUMNAS (LA APP) ---
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# Tu URL de Render (Asegúrate de que sea la External si pruebas desde afuera)
DB_URL = "postgresql://willpay_db_user:746J7SWXHVcv07Tt16AE5diK68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# --- 2. EL CEREBRO DE AUTOMATIZACIÓN (ESTO CREA TU TABLA DE CONFIG) ---
def inicializar_bunker():
    try:
        conn = get_db()
        cur = conn.cursor()
        # Creamos la tabla de interruptores y comisiones si no existe
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
        print("✅ Búnker preparado y configurado.")
    except Exception as e:
        print(f"❌ Error al preparar búnker: {e}")

# Llamamos a la función antes de que alguien entre
inicializar_bunker()

# --- 3. TUS RUTAS DE SIEMPRE (LAS QUE DISEÑASTE) ---

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    return render_template('acceso.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

# --- 4. TU NUEVO PANEL CEO (EL CENTRO DE MANDO) ---

@app.route('/panel_ceo')
def panel_ceo():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Leemos los interruptores y porcentajes
        cur.execute("SELECT * FROM config_ceo WHERE id = 1")
        config = cur.fetchone()
        
        # Calculamos el Capital Total (Suma de todos los saldos)
        cur.execute("SELECT SUM(saldo) as total FROM users")
        resultado = cur.fetchone()
        capital = resultado['total'] if resultado and resultado['total'] else 0.00
        
        # Traemos la lista de los últimos 10 usuarios registrados
        cur.execute("SELECT id, nombre, rol, cedula FROM users ORDER BY id DESC LIMIT 10")
        usuarios = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Enviamos todas las variables al HTML para que NO de error 500
        return render_template('panel_ceo.html', 
                               config=config, 
                               capital=capital, 
                               usuarios=usuarios)
    except Exception as e:
        return f"Error en el búnker: {e}"

# --- 5. ACCIÓN: CARGAR SALDO DESDE EL PANEL ---
@app.route('/cargar_saldo', methods=['POST'])
def cargar_saldo():
    cedula = request.form.get('cedula')
    monto = float(request.form.get('m
