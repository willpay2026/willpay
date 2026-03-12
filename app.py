from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    return render_template('acceso.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

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
        return render_template('panel_ceo.html', config=config, capital=res['total'] or 0.0, depositado=res['dep'] or 0.0, usuarios=usuarios)
    except Exception as e:
        return f"Error en el búnker: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
