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
def index(): 
    return render_template('splash.html')

@app.route('/acceso')
def acceso(): 
    return render_template('acceso.html')

@app.route('/login', methods=['POST'])
def login():
    # Usamos los nombres que configuraste en acceso.html
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
    
    # Si es tu cédula, te manda al panel de control que ya tienes creado
    if u['cedula'] == '13496133':
        return render_template('ceo_panel.html', u=u)
    return render_template('dashboard.html', u=u)

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre', '').upper()
    cedula = request.form.get('cedula', '').strip()
    telefono = request.form.get('telefono', '').strip()
    pin = request.form.get('pin', '').strip()
    
    try:
        query_db("INSERT INTO usuarios (nombre, cedula, telefono, pin) VALUES (%s, %s, %s, %s)", 
                 (nombre, cedula, telefono, pin), commit=True)
        return render_template('ticket_bienvenida.html', nombre=nombre)
    except:
        return "<h1>Error: El usuario ya existe</h1><a href='/acceso'>Entrar</a>"

@app.route('/instalar')
def instalar():
    # Limpiamos y creamos la tabla con la estructura básica para que no falle
    query_db("DROP TABLE IF EXISTS usuarios CASCADE", commit=True)
    query_db("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, 
        nombre TEXT, 
        telefono TEXT UNIQUE, 
        cedula TEXT UNIQUE, 
        pin TEXT, 
        saldo_bs FLOAT DEFAULT 0.0)""", commit=True)
    
    # Creamos tu acceso de una vez
    query_db("""INSERT INTO usuarios (nombre, telefono, cedula, pin) 
        VALUES ('WILFREDO DONQUIZ', '04126602555', '13496133', '1234')""", commit=True)
    return "<h1>🏛️ Bóveda Sincronizada</h1><p>Usa 13496133 y PIN 1234 en /acceso</p>"

if __name__ == '__main__':
    app.run(debug=True)
