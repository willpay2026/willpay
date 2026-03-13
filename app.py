from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
# El secreto del legado para Wilyanny
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- RUTAS DE NAVEGACIÓN (INTACTAS) ---
@app.route('/')
def splash():
    return render_template('auth/splash.html')

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

@app.route('/registro')
def registro():
    return render_template('auth/registro.html')

@app.route('/terminos')
def terminos():
    return render_template('common/terminos.html')

# --- LÓGICA DE REGISTRO ---
@app.route('/crear_cuenta', methods=['POST'])
def crear_cuenta():
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    telefono = request.form.get('telefono')
    tipo = request.form.get('tipo_usuario')
    pin = request.form.get('pin')
    
    # Se guarda con saldo 0 y estatus pendiente
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (nombre, cedula, telefono, rol, password, saldo, verificado) 
        VALUES (%s, %s, %s, %s, %s, 0.0, False)
    """, (nombre, cedula, telefono, tipo, pin))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('acceso'))

# --- LÓGICA DE ACCESO (TU ENTRADA CACHUA) ---
@app.route('/login', methods=['POST'])
def login():
    cedula = request.form.get('cedula')
    pin = request.form.get('pin')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE cedula = %s OR telefono = %s", (cedula, cedula))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and user['password'] == pin:
        session['user_id'] = user['id']
        # Si eres Wilfredo, directo al Búnker
        if user['cedula'] == '13496133':
            return redirect(url_for('panel_ceo'))
        return redirect(url_for('dashboard'))
    return "Credenciales incorrectas"

# --- NUEVA RUTA: EL TICKET MÁGICO ---
@app.route('/ticket_bienvenida')
def ticket_bienvenida():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()

    # Definimos la tasa según el tipo para el ticket
    tasas = {'personal': 3, 'actividad': 2, 'juridico': 1.5}
    
    # Creamos un objeto 'u' para que el HTML lo lea fácil
    u = {
        'id': user['id'],
        'nombre': user['nombre'],
        'cedula': user['cedula'],
        'tasa': tasas.get(user['rol'], 3),
        'es_socio': True if user['rol'] == 'admin' else False
    }
    
    return render_template('user/ticket_bienvenida.html', u=u)

# --- PANELES ---
@app.route('/panel_ceo')
def panel_ceo():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('ceo/panel_ceo.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('user/dashboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
