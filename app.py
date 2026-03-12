from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# CONEXIÓN AUTOMÁTICA (Busca la variable que configuraste en Render)
def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# INICIALIZADOR DE TABLAS
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
        print("✅ Búnker conectado y listo.")
    except Exception as e:
        print(f"❌ Error: {e}")

inicializar_bunker()

# RUTAS DE DISEÑO
@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

# PANEL CEO
@app.route('/panel_ceo')
def panel_ceo():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM config_ceo WHERE id = 1")
        config = cur.fetchone()
        cur.execute("SELECT SUM(saldo) as total FROM users")
        res = cur.fetchone()
        capital = res['total'] if res and res['total'] else 0.00
        cur.execute("SELECT id, nombre, rol, cedula FROM users ORDER BY id DESC LIMIT 10")
        usuarios = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('panel_ceo.html', config=config, capital=capital, usuarios=usuarios)
    except Exception as e:
        return f"Error: {e}"

@app.route('/cargar_saldo', methods=['POST'])
def cargar_saldo():
    cedula = request.form.get('cedula')
    monto = request.form.get('monto')
    if cedula and monto:
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("UPDATE users SET saldo = saldo + %s WHERE cedula = %s", (float(monto), cedula))
            conn.commit()
            cur.close()
            conn.close()
        except: pass
    return redirect(url_for('panel_ceo'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
