from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import psycopg2, os
from psycopg2.extras import DictCursor
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'willpay_legado_final_2026'
DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL, sslmode='require')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Datos del usuario y sus saldos [cite: 2026-03-01]
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    
    # Historial de Pagos (Egresos e Ingresos) [cite: 2026-03-02]
    cur.execute("""
        SELECT p.*, u.nombre as contraparte 
        FROM pagos p 
        JOIN usuarios u ON (p.receptor_id = u.id OR p.emisor_id = u.id)
        WHERE (p.emisor_id = %s OR p.receptor_id = %s) AND u.id != %s
        ORDER BY p.fecha DESC LIMIT 15
    """, (session['user_id'], session['user_id'], session['user_id']))
    movimientos = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('dashboard.html', u=u, movimientos=movimientos)

@app.route('/ejecutar_pago_qr', methods=['POST'])
def ejecutar_pago_qr():
    if 'user_id' not in session: return jsonify({"status": "error", "msg": "Sesión expirada"})
    
    datos = request.get_json()
    receptor_id = datos.get('receptor_id')
    monto = float(datos.get('monto'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Validar saldo del emisor [cite: 2026-03-02]
    cur.execute("SELECT saldo_bs FROM usuarios WHERE id=%s", (session['user_id'],))
    emisor = cur.fetchone()
    
    if emisor['saldo_bs'] >= monto:
        # Transacción de saldo
        cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id = %s", (monto, session['user_id']))
        cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (monto, receptor_id))
        
        # Registro Correlativo WP-TX [cite: 2026-03-02]
        cur.execute("INSERT INTO pagos (emisor_id, receptor_id, monto, moneda) VALUES (%s, %s, %s, 'BS') RETURNING id", 
                     (session['user_id'], receptor_id, monto))
        pago_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "pago_id": pago_id})
    
    return jsonify({"status": "error", "msg": "Saldo insuficiente"})
