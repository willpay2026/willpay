from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- INICIALIZACIÓN (Mecánica de arranque) ---
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026'

# CONEXIÓN AL BÚNKER (POSTGRES)
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# --- RUTAS ---

@app.route('/')
def index():
    # Elimina el error 404 mandando directo al Dashboard
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    # Datos para que el diseño cargue con saldo 0.00
    user = {'saldo': '0.00'}
    return render_template('dashboard.html', user=user)

@app.route('/panel_ceo')
def panel_ceo():
    try:
        conn = get_db()
        cur = conn.cursor()
        # Capital Total para el panel de Wilfredo
        cur.execute("SELECT SUM(saldo) as total FROM usuarios_willpay")
        res = cur.fetchone()
        capital = res['total'] if res and res['total'] else 0.00
        cur.close()
        conn.close()
        return render_template('panel_ceo.html', capital=capital)
    except:
        return render_template('panel_ceo.html', capital=0.00)

# --- CIERRE MAESTRO DE PUERTO ---
if __name__ == '__main__':
    # Captura el puerto de Render o usa el 10000 por defecto
    port = int(os.environ.get("PORT", 10000))
    # '0.0.0.0' abre el búnker al internet
    app.run(host='0.0.0.0', port=port)
