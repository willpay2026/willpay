from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- RUTAS DE NAVEGACIÓN ---
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
    # Atrapamos los datos del registro cachuo
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    telefono = request.form.get('telefono')
    tipo = request.form.get('tipo_usuario')
    pin = request.form.get('pin')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (nombre, cedula, telefono, rol, password, saldo) 
        VALUES (%s, %s, %s, %s, %s, 0.0)
    """, (nombre, cedula, telefono, tipo, pin))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('acceso'))

# --- LÓGICA DE ACCESO ---
@app.route('/login', methods=['POST'])
def login():
    cedula = request.form.get('cedula')
    pin = request.form.get('pin')
    
    conn = get_db()
    cur = conn.cursor()
    # Buscamos por cedula o telefono para mayor comodidad del usuario
    cur.execute("SELECT * FROM users WHERE cedula = %s OR telefono = %s", (cedula, cedula))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and user['password'] == pin:
        session['user_id'] = user['id']
        session['tipo_usuario'] = user['rol']
        
        # El dueño entra al búnker, los demás al dashboard
        if user['cedula'] == '13496133' or user['rol'] == 'admin':
            return redirect(url_for('panel_ceo'))
        return redirect(url_for('dashboard'))
    return "Credenciales incorrectas"

# --- LÓGICA DE COMISIONES ---
def calcular_comision(monto, tipo_usuario):
    # Porcentajes según tu nivel de registro
    tasas = {
        'personal': 0.03,    # 3%
        'actividad': 0.02,   # 2%
        'juridico': 0.015    # 1.5%
    }
    porcentaje = tasas.get(tipo_usuario, 0.03)
    return monto * porcentaje

@app.route('/panel_ceo')
def panel_ceo():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('ceo/panel_ceo.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('user/dashboard.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
