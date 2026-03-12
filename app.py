from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- 1. CONSTRUCCIÓN DE LAS COLUMNAS (LA APP) ---
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# URL DE RENDER CORREGIDA CON SSL (Para evitar el error de SSL/TLS required)
DB_URL = "postgresql://willpay_db_user:746J7SWXHVcv07Tt16AE5diK68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

def get_db():
    # Usamos la URL con sslmode=require para que Render no nos rebote
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

# Llamamos a la función antes de que arranque la app
inicializar_bunker()

# --- 3. TUS RUTAS DE SIEMPRE (LAS QUE DISEÑ
