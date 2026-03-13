from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
# Llave secreta para la seguridad del legado de Wilyanny
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- RUTAS DE ACCESO ---
@app.route('/')
def splash():
    return render_template('auth/splash.html')

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

@app.route('/registro')
def registro():
    return render_template('auth/registro.html')

# --- RUTAS DE USUARIO ---
@app.route('/dashboard')
def dashboard():
    return render_template('user/dashboard.html')

# --- RUTAS DEL CEO (Wilfredo) ---
@app.route('/panel_ceo')
def panel_ceo():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM config_ceo WHERE id = 1")
        config = cur.fetchone()
        cur.execute("SELECT SUM(saldo) as total, SUM(depositado) as dep FROM users")
        res = cur.fetchone()
        cur.execute("SELECT id, nombre, telefono, rol, cedula FROM users ORDER BY id DESC LIMIT 10")
        usuarios = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('ceo/panel_ceo.html', 
                               config=config, 
                               capital=res['total'] or 0.0, 
                               depositado=res['dep'] or 0.0, 
                               usuarios=usuarios)
    except Exception as e:
        return f"Error en el búnker de Will-Pay: {e}"

@app.route('/boveda')
def boveda():
    return render_template('ceo/boveda.html')

# --- RUTAS COMUNES ---
@app.route('/recibo')
def recibo():
    return render_template('common/recibo.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
