from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- INICIALIZACIÓN ---
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026'

# CONEXIÓN AL BÚNKER EN RENDER
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# --- RUTA PRINCIPAL (Solución al Not Found) ---
@app.route('/')
def index():
    # Esto hace que al entrar a la URL se vea tu diseño de una vez
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    # Datos de prueba para que el diseño no se rompa
    user = {'saldo': '0.00'}
    movimientos = [] 
    return render_template('dashboard.html', user=user, movimientos=movimientos)

@app.route('/panel_ceo')
def panel_ceo():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT SUM(saldo) as total FROM usuarios_willpay")
        res = cur.fetchone()
        capital = res['total'] if res and res['total'] else 0.00
        cur.close()
        conn.close()
        return render_template('panel_ceo.html', capital=capital)
    except:
        return render_template('panel_ceo.html', capital=0.00)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
