from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
# Protegiendo el legado de Wilyanny
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- INICIO (SPLASH) ---
@app.route('/')
def splash():
    return render_template('auth/splash.html')

# --- ACCESO (DISEÑO DE WILFREDO) ---
@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

# --- LÓGICA DE LOGIN (LO QUE HACÍA FALTA) ---
@app.route('/login', methods=['POST'])
def login():
    cedula = request.form.get('cedula')
    pin = request.form.get('pin')
    
    conn = get_db()
    cur = conn.cursor()
    # Buscamos al usuario por cédula
    cur.execute("SELECT * FROM users WHERE cedula = %s", (cedula,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and user['password'] == pin: # Aquí comparamos con tu campo de la BD
        session['user_id'] = user['id']
        session['rol'] = user['rol']
        
        # Si es el jefe (Wilfredo), va al panel CEO, si no, al dashboard
        if user['rol'] == 'admin' or user['cedula'] == '13496133':
            return redirect(url_for('panel_ceo'))
        else:
            return redirect(url_for('dashboard'))
    else:
        return "Cédula o PIN incorrecto. Intenta de nuevo."

# --- REGISTRO ---
@app.route('/registro')
def registro():
    return render_template('auth/registro.html')

# --- PANELES ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('user/dashboard.html')

@app.route('/panel_ceo')
def panel_ceo():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT SUM(saldo) as total FROM users")
        res = cur.fetchone()
        cur.close()
        conn.close()
        return render_template('ceo/panel_ceo.html', capital=res['total'] or 0.0)
    except Exception as e:
        return f"Error en el búnker: {e}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
