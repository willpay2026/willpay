from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_legado_final_2026'
DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL, sslmode='require')

@app.route('/')
def index(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre', '').upper()
    cedula = request.form.get('cedula', '').strip()
    telefono = request.form.get('telefono', '').strip()
    rol = request.form.get('actividad', 'USUARIO')
    pin = request.form.get('pin', '').strip()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO usuarios (nombre, cedula, telefono, pin, rol, saldo_bs, saldo_wpc) 
                     VALUES (%s, %s, %s, %s, %s, 0.0, 0.0)""", 
                     (nombre, cedula, telefono, pin, rol))
        conn.commit()
        return redirect(url_for('acceso'))
    except:
        return "<h1>⚠️ Error</h1><p>Cédula ya registrada.</p><a href='/registro'>Volver</a>"
    finally:
        cur.close()
        conn.close()

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
    if u['cedula'] == '13496133':
        return render_template('ceo_panel.html', u=u)
    return render_template('dashboard.html', u=u)

@app.route('/instalar')
def instalar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios CASCADE")
    # Agregamos saldo_wpc y saldo_usd para que tu diseño no de error
    cur.execute("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, cedula TEXT UNIQUE, 
        telefono TEXT, pin TEXT, rol TEXT, 
        saldo_bs FLOAT DEFAULT 0.0, saldo_wpc FLOAT DEFAULT 0.0, saldo_usd FLOAT DEFAULT 0.0)""")
    
    cur.execute("""INSERT INTO usuarios (nombre, cedula, telefono, pin, rol, saldo_bs, saldo_wpc) 
                VALUES ('WILFREDO DONQUIZ', '13496133', '04126602555', '1234', 'CEO', 100.0, 50.0)""")
    
    for i in range(1, 6):
        cur.execute("INSERT INTO usuarios (nombre, cedula, pin, rol) VALUES (%s, %s, '0000', 'SOCIO')", 
                    (f"SOCIO RESERVADO {i}", f"SOCIO-{i}"))
    conn.commit()
    cur.close()
    conn.close()
    return "<h1>🏛️ Bóveda Sincronizada</h1><p>Entra con 13496133 y PIN 1234</p>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
