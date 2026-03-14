from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, psycopg2, datetime, qrcode, io, base64
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

@app.route('/')
def splash():
    return render_template('auth/splash.html')

@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

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
    return "Credenciales incorrectas."

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.execute("""
        SELECT fecha, referencia, monto, estatus, tipo FROM transacciones 
        WHERE emisor = %s OR receptor = %s ORDER BY fecha DESC LIMIT 5
    """, (user['cedula'], user['cedula']))
    movimientos = cur.fetchall(); cur.close(); conn.close()
    return render_template('user/dashboard.html', u=user, movimientos=movimientos)

# --- ALMA DE LA PLATAFORMA: PAGAR Y COBRAR ---

@app.route('/cobrar')
def cobrar():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('user/cobrar.html', cedula=session['cedula'])

@app.route('/generar_qr', methods=['POST'])
def generar_qr():
    monto = request.json.get('monto')
    datos = f"{session['cedula']}|{monto}"
    img = qrcode.make(datos)
    buf = io.BytesIO()
    img.save(buf)
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return jsonify({'qr': qr_b64})

@app.route('/pagar')
def pagar():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('user/pagar.html')

@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    data = request.json
    receptor = data.get('receptor')
    monto = float(data.get('monto'))
    emisor = session['cedula']
    ref = f"WP{datetime.datetime.now().strftime('%M%S%f')[:6]}"
    
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET saldo = saldo - %s WHERE cedula = %s AND saldo >= %s", (monto, emisor, monto))
        if cur.rowcount == 0: return jsonify({'status': 'error', 'msg': 'Saldo insuficiente'})
        cur.execute("UPDATE users SET saldo = saldo + %s WHERE cedula = %s", (monto, receptor))
        cur.execute("INSERT INTO transacciones (emisor, receptor, monto, referencia, tipo) VALUES (%s, %s, %s, %s, 'PAGO')", (emisor, receptor, monto, ref))
        conn.commit()
        return jsonify({'status': 'ok', 'ref': ref})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'msg': str(e)})
    finally:
        cur.close(); conn.close()

@app.route('/comprobante/<ref>')
def comprobante(ref):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM transacciones WHERE referencia = %s", (ref,))
    tx = cur.fetchone(); cur.close(); conn.close()
    return render_template('user/comprobante.html', tx=tx)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
