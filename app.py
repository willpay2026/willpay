from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
# El legado de Wilyanny Donquiz blindado
app.secret_key = 'willpay_2026_reinicio_maestro'
DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL, sslmode='require')

# --- RUTAS DE NAVEGACIÓN (TU DISEÑO ORIGINAL) ---
@app.route('/')
def index(): 
    return render_template('splash.html')

@app.route('/acceso')
def acceso(): 
    return render_template('acceso.html')

@app.route('/login', methods=['POST'])
def login():
    # Usamos los campos exactos de tu acceso.html
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
    return "<h1>❌ Acceso Incorrecto</h1><a href='/acceso'>Volver a intentar</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    cur.close()
    conn.close()
    
    # Si eres tú, entras al panel de CEO para ver tu comisión
    if u['cedula'] == '13496133':
        return render_template('ceo_panel.html', u=u)
    return render_template('dashboard.html', u=u)

# --- EL REINICIO MAESTRO (BORRÓN Y CUENTA NUEVA) ---
@app.route('/instalar')
def instalar():
    conn = get_db_connection()
    cur = conn.cursor()
    # Limpiamos todo para que no haya errores de la 8va vez
    cur.execute("DROP TABLE IF EXISTS usuarios CASCADE")
    cur.execute("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, cedula TEXT UNIQUE, 
        telefono TEXT, pin TEXT, saldo_bs FLOAT DEFAULT 0.0, 
        rol TEXT DEFAULT 'SOCIO')""")
    
    # 1. Te insertamos a ti como CEO (Wilfredo Donquiz)
    cur.execute("""INSERT INTO usuarios (nombre, cedula, telefono, pin, rol, saldo_bs) 
                VALUES ('WILFREDO DONQUIZ', '13496133', '04126602555', '1234', 'CEO', 1000.0)""")
    
    # 2. Reservamos los 5 espacios para futuros socios
    for i in range(1, 6):
        cur.execute("""INSERT INTO usuarios (nombre, cedula, pin, rol) 
                    VALUES (%s, %s, '0000', 'SOCIO_RESERVADO')""", 
                    (f"SOCIO FUTURO {i}", f"RES-00{i}"))
    
    conn.commit()
    cur.close()
    conn.close()
    return "<h1>🏛️ Bóveda Reiniciada Exitosamente</h1><p>Wilfredo, ya eres el CEO. Entra con tu cédula y PIN 1234.</p>"

if __name__ == '__main__':
    # PARCHE CRÍTICO PARA RENDER (Evita el error de puerto)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
