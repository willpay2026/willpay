from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

def inicializar_bunker():
    try:
        conn = get_db()
        cur = conn.cursor()
        # Reparación de columnas para Dinero Depositado, Teléfono y Pánico
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS depositado FLOAT DEFAULT 0.0;")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telefono VARCHAR(20);")
        cur.execute("ALTER TABLE config_ceo ADD COLUMN IF NOT EXISTS modo_panico BOOLEAN DEFAULT FALSE;")
        cur.execute("ALTER TABLE config_ceo ADD COLUMN IF NOT EXISTS ganancias_legado FLOAT DEFAULT 0.0;")
        cur.execute("ALTER TABLE config_ceo ADD COLUMN IF NOT EXISTS p_retiros FLOAT DEFAULT 1.0;")
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS config_ceo (
                id SERIAL PRIMARY KEY,
                modo_panico BOOLEAN DEFAULT FALSE,
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
                depositado FLOAT DEFAULT 0.0
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

inicializar_bunker()

@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/panel_ceo')
def panel_ceo():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM config_ceo WHERE id = 1")
    config = cur.fetchone()
    cur.execute("SELECT SUM(saldo) as total, SUM(depositado) as dep FROM users")
    res = cur.fetchone()
    cur.execute("SELECT id, nombre, telefono, cedula FROM users ORDER BY id DESC LIMIT 10")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('panel_ceo.html', config=config, capital=res['total'] or 0.0, depositado=res['dep'] or 0.0, usuarios=usuarios)

@app.route('/activar_panico', methods=['POST'])
def activar_panico():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE config_ceo SET modo_panico = NOT modo_panico WHERE id = 1")
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('panel_ceo'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
