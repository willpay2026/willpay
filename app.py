from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny'
DB_URL = os.environ.get('DATABASE_URL')

def query_db(query, args=(), one=False, commit=False):
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(query, args)
        if commit:
            conn.commit()
            res = None
        else:
            res = cur.fetchone() if one else cur.fetchall()
        cur.close()
        conn.close()
        return res
    except Exception as e:
        return str(e)

@app.route('/')
def index(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/login', methods=['POST'])
def login():
    dato = request.form.get('telefono_login', '').strip()
    pin = request.form.get('pin_login', '').strip()
    # Buscamos al usuario
    user = query_db("SELECT * FROM usuarios WHERE (telefono=%s OR cedula=%s) AND pin=%s", (dato, dato, pin), one=True)
    
    if isinstance(user, str): return f"Error de DB: {user}" # Si la DB falla, nos avisa
    
    if user:
        session['user_id'] = user['id']
        session['nombre'] = user['nombre']
        return redirect(url_for('dashboard'))
    return "<h1>❌ Datos Incorrectos</h1><a href='/acceso'>Volver</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    # Buscamos tus datos para el panel
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    # Si eres Wilfredo, te manda a tu panel de jefe
    if u['cedula'] == '13496133':
        return render_template('ceo_panel.html', u=u)
    return render_template('dashboard.html', u=u)

@app.route('/instalar')
def instalar():
    # Creamos la tabla desde cero
    query_db("DROP TABLE IF EXISTS usuarios CASCADE", commit=True)
    query_db("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, telefono TEXT UNIQUE, 
        cedula TEXT UNIQUE, pin TEXT, saldo_bs FLOAT DEFAULT 0.0)""", commit=True)
    # Te insertamos como CEO
    query_db("INSERT INTO usuarios (nombre, telefono, cedula, pin) VALUES ('WILFREDO', '04126602555', '13496133', '1234')", commit=True)
    return "<h1>🏛️ BOVEDA LISTA</h1><p>Ve a /acceso y usa 13496133 y 1234</p>"

if __name__ == '__main__':
    app.run(debug=True)
