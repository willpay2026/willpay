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
        # Registramos con estatus 'PENDIENTE' para que tú lo apruebes
        cur.execute("""INSERT INTO usuarios (nombre, cedula, telefono, pin, rol, saldo_bs, saldo_wpc, saldo_usd, ganancia_neta) 
                     VALUES (%s, %s, %s, %s, 'PENDIENTE', 0.0, 0.0, 0.0, 0.0)""", 
                     (nombre, cedula, telefono, pin))
        conn.commit()
        return redirect(url_for('acceso'))
    except Exception as e:
        return f"<h1>⚠️ Error</h1><p>{e}</p><a href='/registro'>Volver</a>"
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
    
    # Mostramos los últimos registros para que los apruebes en 'ACTIVIDAD EN VIVO'
    cur.execute("SELECT * FROM usuarios WHERE rol = 'PENDIENTE' ORDER BY id DESC LIMIT 5")
    usuarios_pendientes = cur.fetchall()
    
    cur.close()
    conn.close()
    if u['cedula'] == '13496133':
        return render_template('ceo_panel.html', u=u, usuarios=usuarios_pendientes)
    return render_template('dashboard.html', u=u)

@app.route('/aprobar_socio/<int:id>')
def aprobar_socio(id):
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor()
    # Al aprobar, le damos rango de SOCIO y un bono de bienvenida de 10 Bs
    cur.execute("UPDATE usuarios SET rol = 'SOCIO', saldo_bs = 10.0 WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/instalar')
def instalar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios CASCADE")
    cur.execute("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, cedula TEXT UNIQUE, 
        telefono TEXT, pin TEXT, rol TEXT, 
        saldo_bs FLOAT DEFAULT 0.0, 
        saldo_wpc FLOAT DEFAULT 0.0, 
        saldo_usd FLOAT DEFAULT 0.0,
        ganancia_neta FLOAT DEFAULT 0.0)""")
    
    cur.execute("""INSERT INTO usuarios (nombre, cedula, telefono, pin, rol, saldo_bs, saldo_wpc, saldo_usd, ganancia_neta) 
                VALUES ('WILFREDO DONQUIZ', '13496133', '04126602555', '1234', 'CEO', 100.0, 50.0, 10.0, 5.0)""")
    
    # Reservamos los 5 espacios para partners futuros
    for i in range(1, 6):
        cur.execute("INSERT INTO usuarios (nombre, cedula, pin, rol) VALUES (%s, %s, '0000', 'SOCIO_RESERVADO')", 
                    (f"SOCIO RESERVADO {i}", f"PARTNER-{i}"))
    conn.commit()
    cur.close()
    conn.close()
    return "<h1>🏛️ Bóveda Sincronizada</h1><p>Wilfredo, entra ahora a /acceso</p>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
