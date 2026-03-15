from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, psycopg2, datetime
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

UPLOAD_FOLDER = 'static/captures'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

@app.route('/')
def index():
    return render_template('auth/splash.html')

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        cedula = request.form.get('cedula')
        pin = request.form.get('pin')
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (nombre, cedula, password, saldo) VALUES (%s, %s, %s, 0.00)", (nombre, cedula, pin))
            conn.commit()
            return redirect(url_for('acceso'))
        except Exception as e:
            conn.rollback()
            return f"Error: La cédula ya existe."
        finally:
            cur.close(); conn.close()
    return render_template('auth/registro.html')

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

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.execute("SELECT fecha, referencia, monto, estatus, tipo FROM transacciones WHERE emisor = %s OR receptor = %s ORDER BY fecha DESC LIMIT 10", (user['cedula'], user['cedula']))
    movs = cur.fetchall(); cur.close(); conn.close()
    return render_template('user/dashboard.html', u=user, movimientos=movs)

@app.route('/ejecutar_pago', methods=['POST'])
def ejecutar_pago():
    if 'user_id' not in session: return jsonify({'status': 'error', 'msg': 'Sesión cerrada'})
    data = request.json
    emisor_cedula = data.get('emisor') # El que mostró el QR
    monto = float(data.get('monto'))
    receptor_cedula = session['cedula'] # Tú (el que escanea) recibes
    
    if receptor_cedula == emisor_cedula:
        return jsonify({'status': 'error', 'msg': 'No puedes cobrarte a ti mismo'})

    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT saldo FROM users WHERE cedula = %s", (emisor_cedula,))
        fila = cur.fetchone()
        if not fila or fila['saldo'] < monto:
            return jsonify({'status': 'error', 'msg': 'Saldo insuficiente en la cuenta de origen'})

        cur.execute("UPDATE users SET saldo = saldo - %s WHERE cedula = %s", (monto, emisor_cedula))
        cur.execute("UPDATE users SET saldo = saldo + %s WHERE cedula = %s", (monto, receptor_cedula))
        
        ref = f"WP{datetime.datetime.now().strftime('%M%S%f')[:6].upper()}"
        cur.execute("INSERT INTO transacciones (emisor, receptor, monto, referencia, estatus, tipo) VALUES (%s, %s, %s, %s, 'EXITOSO', 'TRANSFERENCIA')", (emisor_cedula, receptor_cedula, monto, ref))
        conn.commit()
        return jsonify({'status': 'ok', 'ref': ref})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'msg': str(e)})
    finally:
        cur.close(); conn.close()

@app.route('/notificar_pago', methods=['POST'])
def notificar_pago():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    monto = request.form.get('monto')
    ref_bancaria = request.form.get('referencia')
    file = request.files['capture']
    if file:
        filename = secure_filename(f"{session['cedula']}_{ref_bancaria}.png")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn = get_db(); cur = conn.cursor()
        cur.execute("INSERT INTO transacciones (emisor, receptor, monto, referencia, estatus, tipo) VALUES (%s, 'SISTEMA', %s, %s, 'PENDIENTE', 'RECARGA')", (session['cedula'], monto, ref_bancaria))
        conn.commit(); cur.close(); conn.close()
    return redirect(url_for('dashboard'))

# --- PANEL CEO PARA WILFREDO ---
@app.route('/admin_panel')
def admin_panel():
    if session.get('cedula') != '13496133': return "Acceso Denegado"
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM transacciones WHERE estatus = 'PENDIENTE'")
    pendientes = cur.fetchall(); cur.close(); conn.close()
    return render_template('admin/panel.html', pendientes=pendientes)

@app.route('/aprobar/<int:t_id>')
def aprobar(t_id):
    if session.get('cedula') != '13496133': return "Error"
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT emisor, monto FROM transacciones WHERE id = %s", (t_id,))
    t = cur.fetchone()
    cur.execute("UPDATE users SET saldo = saldo + %s WHERE cedula = %s", (t['monto'], t['emisor']))
    cur.execute("UPDATE transacciones SET estatus = 'EXITOSO' WHERE id = %s", (t_id,))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('acceso'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
