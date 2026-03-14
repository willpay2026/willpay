from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, psycopg2, datetime
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

@app.route('/')
def index():
    return redirect(url_for('acceso'))

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

@app.route('/login', methods=['POST'])
def login():
    cedula = request.form.get('cedula')
    pin = request.form.get('pin')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE cedula = %s AND password = %s", (cedula, pin))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        session['user_id'] = user['id']
        session['cedula'] = user['cedula']
        session['nombre'] = user['nombre']
        return redirect(url_for('dashboard'))
    return "Error de acceso"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.execute("""
        SELECT fecha, referencia, monto, estatus, tipo FROM transacciones 
        WHERE emisor = %s OR receptor = %s ORDER BY fecha DESC LIMIT 10
    """, (user['cedula'], user['cedula']))
    movimientos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('user/dashboard.html', u=user, movimientos=movimientos)

@app.route('/comprobante/<ref>')
def comprobante(ref):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transacciones WHERE referencia = %s", (ref,))
    tx = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('user/comprobante.html', tx=tx)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
