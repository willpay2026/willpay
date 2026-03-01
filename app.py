from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny'
DB_URL = os.environ.get('DATABASE_URL')

def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=DictCursor)
    try:
        cur.execute(query, args)
        if commit:
            conn.commit()
            return None
        return cur.fetchone() if one else cur.fetchall()
    finally:
        cur.close()
        conn.close()

@app.route('/')
def index(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/login', methods=['POST'])
def login():
    # Usamos .get para evitar errores si el campo viene vacío
    dato = request.form.get('telefono_login', '').strip()
    pin = request.form.get('pin_login', '').strip()
    
    user = query_db("SELECT * FROM usuarios WHERE (telefono=%s OR cedula=%s) AND pin=%s", (dato, dato, pin), one=True)
    
    if user:
        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))
    return "<h1>❌ Datos Incorrectos</h1><a href='/acceso'>Volver</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    # Si aún no tienes el HTML del tablero8, usamos el dashboard normal para probar
    return render_template('dashboard.html', u=u)

@app.route('/instalar')
def instalar():
    query_db("DROP TABLE IF EXISTS usuarios CASCADE", commit=True)
    query_db("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, id_dna TEXT, nombre TEXT, telefono TEXT UNIQUE, 
        cedula TEXT UNIQUE, pin TEXT, actividad TEXT, saldo_bs FLOAT DEFAULT 100.0)""", commit=True)
    
    # Creamos tu usuario CEO directamente
    query_db("""INSERT INTO usuarios (id_dna, nombre, telefono, cedula, pin, actividad) 
        VALUES ('CEO-0001', 'WILFREDO DONQUIZ', '04126602555', '13496133', '1234', 'CEO')""", commit=True)
    return "<h1>🏛️ Bóveda Lista</h1><p>Entra a /acceso con 13496133 y PIN 1234</p>"

if __name__ == '__main__': app.run(debug=True)
