from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, psycopg2, datetime
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# Configuración de carpeta para los captures de pago
UPLOAD_FOLDER = 'static/captures'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- 1. ENTRADA Y SPLASH ---
@app.route('/')
def index():
    return render_template('auth/splash.html')

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

# --- 2. REGISTRO DE USUARIOS ---
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        cedula = request.form.get('cedula')
        pin = request.form.get('pin')
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (nombre, cedula, password, saldo) VALUES (%s, %s, %s, 0.00)", 
                        (nombre, cedula, pin))
            conn.commit()
            return redirect(url_for('acceso'))
        except Exception as e:
            conn.rollback()
            return f"Error: La cédula ya existe o hay un problema con la DB."
        finally:
            cur.close(); conn.close()
    return render_template('auth/registro.html')

# --- 3. LOGIN ---
@app.route('/login', methods=['POST'])
def login():
    cedula = request.form.get('cedula')
    pin = request.form.get('pin')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE cedula = %s AND password = %s", (cedula, pin))
    user = cur.fetchone(); cur.close(); conn.close()
    if user:
        session['user_id'] = user['id']
        session['cedula'] = user['cedula']
        session['nombre'] = user['nombre']
        return redirect(url_for('dashboard'))
    return "PIN o Cédula incorrecta."

# --- 4. DASHBOARD (EL BÚNKER) ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.execute("""
        SELECT fecha, referencia, monto, estatus, tipo FROM transacciones 
        WHERE emisor = %s OR receptor = %s ORDER BY fecha DESC LIMIT 10
    """, (user['cedula'], user['cedula']))
    movs = cur.fetchall(); cur.close(); conn.close()
    return render_template('user/dashboard.html', u=user, movimientos=movs)

# --- 5. LÓGICA DE PAGO (PAGAR CON CÁMARA) ---
@app.route('/ejecutar_pago', methods=['POST'])
def ejecutar_pago():
    if 'user_id' not in session: return jsonify({'status': 'error', 'msg': 'Sesión cerrada'})
    data = request.json
    receptor_cedula = data.get('receptor')
    monto = float(data.get('monto'))
    emisor_cedula = session['cedula']
    
    if receptor_cedula == emisor_cedula:
        return jsonify({'status': 'error', 'msg': 'No puedes pagarte a ti mismo'})

    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT saldo FROM users WHERE cedula = %s", (emisor_cedula,))
        saldo_emisor = cur.fetchone()['saldo']
        if saldo_emisor < monto:
            return jsonify({'status': 'error', 'msg': 'Saldo insuficiente'})

        cur.execute("UPDATE users SET saldo = saldo - %s WHERE cedula = %s", (monto, emisor_cedula))
        cur.execute("UPDATE users SET saldo = saldo + %s WHERE cedula = %s", (monto, receptor_cedula))
        
        ref = f"WP{datetime.datetime.now().strftime('%M%S%f')[:6].upper()}"
        cur.execute("""
            INSERT INTO transacciones (emisor, receptor, monto, referencia, estatus, tipo) 
            VALUES (%s, %s, %s, %s, 'EXITOSO', 'PAGO')
        """, (emisor_cedula, receptor_cedula, monto, ref))
        
        conn.commit()
        return jsonify({'status': 'ok', 'ref': ref})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'msg': 'Error en la red del búnker'})
    finally:
        cur.close(); conn.close()

# --- 6. NOTIFICAR RECARGA (EL CAPTURE) ---
@app.route('/notificar_pago', methods=['POST'])
def notificar_pago():
    monto = request.form.get('monto')
    ref_bancaria = request.form.get('referencia')
    file = request.files['capture']
    
    if file:
        filename = secure_filename(f"{session['cedula']}_{ref_bancaria}.png")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            INSERT INTO transacciones (emisor, receptor, monto, referencia, estatus, tipo) 
            VALUES (%s, 'SISTEMA', %s, %s, 'PENDIENTE', 'RECARGA')
        """, (session['cedula'], monto, ref_bancaria))
        conn.commit(); cur.close(); conn.close()
        
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('acceso'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
