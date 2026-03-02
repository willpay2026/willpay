from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import psycopg2, os
from psycopg2.extras import DictCursor
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'willpay_legado_final_2026_donquiz'
DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL, sslmode='require')

# --- RUTAS DE ACCESO ---
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
            return "<h1>❌ Datos incorrectos</h1><p><a href='/acceso'>Volver a intentar</a></p>"
    return render_template('acceso.html')

# --- DASHBOARD DEL USUARIO ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Datos del usuario
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    
    # Historial de Movimientos Cruzado [cite: 2026-03-02]
    cur.execute("""
        SELECT p.*, 
               u_emisor.nombre as nombre_emisor, 
               u_receptor.nombre as nombre_receptor
        FROM pagos p
        JOIN usuarios u_emisor ON p.emisor_id = u_emisor.id
        JOIN usuarios u_receptor ON p.receptor_id = u_receptor.id
        WHERE (p.emisor_id = %s OR p.receptor_id = %s)
        ORDER BY p.fecha DESC LIMIT 15
    """, (session['user_id'], session['user_id']))
    movimientos = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('dashboard.html', u=u, movimientos=movimientos)

# --- PANEL MAESTRO (CEO WILFREDO) ---
@app.route('/panel_maestro')
def panel_maestro():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    
    # Seguridad de Cédula Wilfredo [cite: 2026-03-01]
    if u['cedula'] != '13496133': return "<h1>Acceso Denegado</h1>", 403
    
    cur.execute("SELECT * FROM usuarios ORDER BY id DESC")
    usuarios = cur.fetchall()
    cur.execute("""
        SELECT p.*, u1.nombre as emisor, u2.nombre as receptor 
        FROM pagos p 
        JOIN usuarios u1 ON p.emisor_id = u1.id 
        JOIN usuarios u2 ON p.receptor_id = u2.id 
        ORDER BY p.id DESC
    """)
    pagos = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('panel_maestro.html', u=u, usuarios=usuarios, pagos=pagos)

# --- SISTEMA DE PAGOS QR ---
@app.route('/ejecutar_pago_qr', methods=['POST'])
def ejecutar_pago_qr():
    if 'user_id' not in session: return jsonify({"status": "error"})
    datos = request.get_json()
    receptor_id = datos.get('receptor_id')
    monto = float(datos.get('monto'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT saldo_bs FROM usuarios WHERE id=%s", (session['user_id'],))
    emisor = cur.fetchone()
    
    if emisor['saldo_bs'] >= monto:
        cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id = %s", (monto, session['user_id']))
        cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (monto, receptor_id))
        cur.execute("INSERT INTO pagos (emisor_id, receptor_id, monto, moneda) VALUES (%s, %s, %s, 'BS') RETURNING id", 
                     (session['user_id'], receptor_id, monto))
        pago_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "pago_id": pago_id})
    return jsonify({"status": "error", "msg": "Saldo insuficiente"})

@app.route('/admin/recargar_manual', methods=['POST'])
def recargar_manual():
    cedula = request.form.get('cedula_usuario')
    monto = float(request.form.get('monto'))
    moneda = request.form.get('moneda')
    conn = get_db_connection()
    cur = conn.cursor()
    columna = "saldo_bs" if moneda == "BS" else "saldo_usd"
    cur.execute(f"UPDATE usuarios SET {columna} = {columna} + %s WHERE cedula = %s", (monto, cedula))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('panel_maestro'))

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
        saldo_bs FLOAT DEFAULT 0.0, saldo_usd FLOAT DEFAULT 0.0, rol TEXT DEFAULT 'SOCIO')""")
    cur.execute("""CREATE TABLE pagos (
        id SERIAL PRIMARY KEY, emisor_id INTEGER, receptor_id INTEGER, 
        monto FLOAT, moneda TEXT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    # [cite: 2026-03-01]
    cur.execute("INSERT INTO usuarios (nombre, cedula, pin, rol, saldo_bs) VALUES ('WILFREDO DONQUIZ', '13496133', '1234', 'CEO', 1000.0)")
    conn.commit()
    cur.close()
    conn.close()
    return "SISTEMA SINCRONIZADO EXITOSAMENTE"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('acceso'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
