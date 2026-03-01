from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
# El secreto del legado para Wilyanny
app.secret_key = 'willpay_2026_original'
DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL, sslmode='require')

# --- RUTAS DE NAVEGACIÓN (TU DISEÑO) ---
@app.route('/')
def index(): 
    return render_template('splash.html')

@app.route('/acceso')
def acceso(): 
    return render_template('acceso.html')

@app.route('/registro')
def registro(): 
    return render_template('registro.html')

# --- PROCESO DE REGISTRO (SIN ERRORES 404) ---
@app.route('/procesar_register', methods=['POST'])
def procesar_register():
    nombre = request.form.get('nombre', '').upper()
    cedula = request.form.get('cedula', '').strip()
    telefono = request.form.get('telefono', '').strip()
    pin = request.form.get('pin', '').strip()[:4]
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO usuarios (nombre, cedula, telefono, pin, saldo_bs) 
                     VALUES (%s, %s, %s, %s, 0.0)""", 
                     (nombre, cedula, telefono, pin))
        conn.commit()
        return redirect(url_for('acceso'))
    except:
        return "<h1>⚠️ Error</h1><p>Cédula ya registrada.</p><a href='/registro'>Volver</a>"
    finally:
        cur.close()
        conn.close()

# --- LOGIN ---
@app.route('/login', methods=['POST'])
def login():
    dato = request.form.get('telefono_login', '').strip()
    pin = request.form.get('pin_login', '').strip()
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE (cedula=%s OR telefono=%s) AND pin=%s", (dato, dato, pin))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))
    return "<h1>❌ Datos Incorrectos</h1><a href='/acceso'>Volver</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    cur.close()
    conn.close()
    
    if u['cedula'] == '13496133': # Tu panel de CEO
        return render_template('ceo_panel.html', u=u)
    return render_template('dashboard.html', u=u)

# --- INSTALACIÓN LIMPIEZA ---
@app.route('/instalar')
def instalar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios CASCADE")
    cur.execute("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, cedula TEXT UNIQUE, 
        telefono TEXT, pin TEXT, saldo_bs FLOAT DEFAULT 0.0)""")
    # Te creamos de una vez para que no sufras con el registro
    cur.execute("INSERT INTO usuarios (nombre, cedula, pin, saldo_bs) VALUES ('WILFREDO DONQUIZ', '13496133', '1234', 100.0)")
    conn.commit()
    cur.close()
    conn.close()
    return "<h1>🏛️ Bóveda Lista</h1><p>Entra con 13496133 y PIN 1234</p>"

if __name__ == '__main__':
    # Puerto dinámico para Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
