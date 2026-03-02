from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os
from psycopg2.extras import DictCursor
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'willpay_legado_final_2026'
DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL, sslmode='require')

@app.route('/')
def index(): return render_template('splash.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('dashboard.html', u=u)

# --- 🦅 PANEL MAESTRO CON AUDITORÍA ---
@app.route('/panel_maestro')
def panel_maestro():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    
    # Solo Wilfredo (CEO) entra aquí
    if u['cedula'] != '13496133': 
        return "Acceso Denegado", 403
    
    # Traemos todos los usuarios y todos los pagos para auditoría
    cur.execute("SELECT * FROM usuarios ORDER BY id DESC")
    usuarios = cur.fetchall()
    
    cur.execute("SELECT * FROM pagos ORDER BY id DESC")
    pagos = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('panel_maestro.html', u=u, usuarios=usuarios, pagos=pagos)

@app.route('/admin/recargar_manual', methods=['POST'])
def recargar_manual():
    cedula = request.form.get('cedula_usuario')
    monto = float(request.form.get('monto'))
    moneda = request.form.get('moneda')
    conn = get_db_connection()
    cur = conn.cursor()
    if moneda == 'BS':
        cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE cedula = %s", (monto, cedula))
    else:
        cur.execute("UPDATE usuarios SET saldo_usd = saldo_usd + %s WHERE cedula = %s", (monto, cedula))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('panel_maestro'))

# --- 🛠️ RUTA DE ANULACIÓN (SÓLO CEO) ---
@app.route('/admin/anular_pago/<int:id_pago>')
def anular_pago(id_pago):
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    cur.execute("SELECT cedula FROM usuarios WHERE id=%s", (session['user_id'],))
    admin = cur.fetchone()
    if admin['cedula'] != '13496133': return "No autorizado", 403

    cur.execute("SELECT * FROM pagos WHERE id = %s", (id_pago,))
    pago = cur.fetchone()

    if pago and pago['moneda'] != 'ANULADO':
        # Reversión de saldo
        cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (pago['monto'], pago['emisor_id']))
        cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id = %s", (pago['monto'], pago['receptor_id']))
        # Marcamos como ANULADO en el historial
        cur.execute("UPDATE pagos SET moneda = 'ANULADO' WHERE id = %s", (id_pago,))
        conn.commit()
    
    cur.close()
    conn.close()
    return redirect(url_for('panel_maestro'))

@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    monto = float(request.form.get('monto'))
    receptor_id = request.form.get('receptor_id')
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
        return redirect(url_for('comprobante', id_pago=pago_id))
    return "Saldo Insuficiente"

@app.route('/comprobante/<int:id_pago>')
def comprobante(id_pago):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM pagos WHERE id = %s", (id_pago,))
    pago = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('recibo.html', pago=pago)

@app.route('/instalar')
def instalar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios, recargas, pagos CASCADE")
    cur.execute("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, cedula TEXT UNIQUE, telefono TEXT, pin TEXT, rol TEXT, 
        saldo_bs FLOAT DEFAULT 0.0, saldo_usd FLOAT DEFAULT 0.0)""")
    cur.execute("""CREATE TABLE pagos (
        id SERIAL PRIMARY KEY, emisor_id INTEGER, receptor_id INTEGER, monto FLOAT, 
        moneda TEXT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("INSERT INTO usuarios (nombre, cedula, pin, rol) VALUES ('WILFREDO', '13496133', '1234', 'CEO')")
    conn.commit()
    cur.close()
    conn.close()
    return "Sistema Sincronizado"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
