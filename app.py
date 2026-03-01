from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny' # El legado de Wilyanny
DB_URL = os.environ.get('DATABASE_URL')

# --- CONEXIÓN A LA BÓVEDA ---
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

# --- RUTAS DE ENTRADA ---
@app.route('/')
def index(): 
    return render_template('splash.html') # El splash inicial

@app.route('/acceso')
def acceso(): 
    return render_template('acceso.html') # Tu acceso corregido

# --- LOGIN BLINDADO (Usa 13496133 y 1234) ---
@app.route('/login', methods=['POST'])
def login():
    # Buscamos 'telefono_login' y 'pin_login' que DEBEN estar en el acceso.html
    dato = request.form.get('telefono_login', '').strip()
    pin = request.form.get('pin_login', '').strip()
    
    user = query_db("SELECT * FROM usuarios WHERE (telefono=%s OR cedula=%s) AND pin=%s", (dato, dato, pin), one=True)
    
    if user:
        session['user_id'] = user['id']
        # Si eres tú, entras al CEO PANEL directamente
        if user['cedula'] == '13496133':
            return redirect(url_for('dashboard'))
        return redirect(url_for('dashboard'))
    return "<h1>❌ DATOS INCORRECTOS</h1><p>Verifica que en acceso.html los campos se llamen 'telefono_login' y 'pin_login'.</p><a href='/acceso'>REINTENTAR</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    
    # Redirección según tu lista de archivos
    if u['cedula'] == '13496133':
        return render_template('ceo_panel.html', u=u)
    return render_template('dashboard.html', u=u)

@app.route('/registro')
def registro():
    return render_template('registro.html') # Registro KYC

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre', '').upper()
    cedula = request.form.get('cedula', '').strip()
    telefono = request.form.get('telefono', '').strip()
    pin = request.form.get('pin', '').strip()
    
    try:
        query_db("INSERT INTO usuarios (nombre, cedula, telefono, pin) VALUES (%s, %s, %s, %s)", 
                 (nombre, cedula, telefono, pin), commit=True)
        return render_template('ticket_bienvenida.html', nombre=nombre) # Tu ticket
    except:
        return "<h1>ERROR: EL USUARIO YA EXISTE</h1><a href='/acceso'>ENTRAR</a>"

# --- INSTALACIÓN Y LIMPIEZA ---
@app.route('/instalar')
def instalar():
    query_db("DROP TABLE IF EXISTS usuarios CASCADE", commit=True)
    query_db("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, 
        nombre TEXT, 
        telefono TEXT UNIQUE, 
        cedula TEXT UNIQUE, 
        pin TEXT, 
        saldo_bs FLOAT DEFAULT 0.0)""", commit=True)
    
    # Creamos tu perfil CEO para que entres de una
    query_db("""INSERT INTO usuarios (nombre, telefono, cedula, pin) 
        VALUES ('WILFREDO DONQUIZ', '04126602555', '13496133', '1234')""", commit=True)
    return "<h1>🏛️ BÓVEDA SINCRONIZADA</h1><p>Ahora ve a /acceso y pon 13496133 y PIN 1234</p>"

if __name__ == '__main__':
    app.run(debug=True)
