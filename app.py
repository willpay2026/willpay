from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import psycopg2, os
from psycopg2.extras import DictCursor
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'willpay_legado_estable_2026'
DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL, sslmode='require')

@app.route('/')
def index(): 
    return render_template('splash.html')

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        pin = request.form.get('pin')
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT * FROM usuarios WHERE cedula=%s AND pin=%s", (cedula, pin))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['nombre'] = user['nombre']
            return redirect(url_for('dashboard'))
        else:
            return "<h1>❌ Error</h1><p>Datos incorrectos. <a href='/acceso'>Volver</a></p>"
    return render_template('acceso.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    # Historial simplificado
    cur.execute("""
        SELECT p.*, u2.nombre as receptor_n 
        FROM pagos p 
        JOIN usuarios u2 ON p.receptor_id = u2.id 
        WHERE p.emisor_id = %s ORDER BY p.fecha DESC LIMIT 10
    """, (session['user_id'],))
    movimientos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', u=u, movimientos=movimientos)

@app.route('/ejecutar_pago_qr', methods=['POST'])
def ejecutar_pago_qr():
    if 'user_id' not in session: return jsonify({"status": "error"})
    datos = request.get_json()
    receptor_id = datos.get('receptor_id')
    monto = float(datos.get('monto'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id = %s", (monto, session['user_id']))
    cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (monto, receptor_id))
    cur.execute("INSERT INTO pagos (emisor_id, receptor_id, monto, moneda) VALUES (%s, %s, %s, 'BS') RETURNING id", 
                 (session['user_id'], receptor_id, monto))
    pago_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok", "pago_id": pago_id})

@app.route('/comprobante/<int:id_pago>')
def comprobante(id_pago):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("""
        SELECT p.*, u1.nombre as emisor, u2.nombre as receptor 
        FROM pagos p 
        JOIN usuarios u1 ON p.emisor_id = u1.id 
        JOIN usuarios u2 ON p.receptor_id = u2.id 
        WHERE p.id = %s
    """, (id_pago,))
    pago = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('recibo.html', pago=pago)

@app.route('/instalar')
def instalar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios, pagos CASCADE")
    cur.execute("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, cedula TEXT UNIQUE, pin TEXT, 
        saldo_bs FLOAT DEFAULT 1000.0, saldo_usd FLOAT DEFAULT 0.0)""")
    cur.execute("""CREATE TABLE pagos (
        id SERIAL PRIMARY KEY, emisor_id INTEGER, receptor_id INTEGER, 
        monto FLOAT, moneda TEXT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("INSERT INTO usuarios (nombre, cedula, pin) VALUES ('WILFREDO DONQUIZ', '13496133', '1234')")
    conn.commit()
    cur.close()
    conn.close()
    return "SISTEMA SINCRONIZADO"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
