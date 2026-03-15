from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

@app.route('/')
def index():
    # Esta es la ruta principal que ahora buscará el logo correcto
    return render_template('auth/splash.html')

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        cedula = request.form.get('cedula')
        pin = request.form.get('pin')
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (nombre, cedula, password, saldo) VALUES (%s, %s, %s, 0.00)", 
                        (nombre, cedula, pin))
            conn.commit()
            return redirect(url_for('acceso'))
        except Exception as e:
            conn.rollback()
            return f"Error: {e}"
        finally:
            cur.close(); conn.close()
    return render_template('auth/registro.html')

@app.route('/login', methods=['POST'])
def login():
    cedula = request.form.get('cedula')
    pin = request.form.get('pin')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE cedula = %s AND password = %s", (cedula, pin))
    user = cur.fetchone(); cur.close(); conn.close()
    if user:
        session['user_id'] = user['id']
        session['cedula'] = user['cedula']
        return redirect(url_for('dashboard'))
    return "Credenciales incorrectas."

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.execute("SELECT * FROM transacciones WHERE emisor = %s OR receptor = %s ORDER BY fecha DESC LIMIT 10", 
                (user['cedula'], user['cedula']))
    movs = cur.fetchall(); cur.close(); conn.close()
    return render_template('user/dashboard.html', u=user, movimientos=movs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
