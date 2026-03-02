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

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre', '').upper()
    cedula = request.form.get('cedula', '').strip()
    telefono = request.form.get('telefono', '').strip()
    pin = request.form.get('pin', '').strip()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO usuarios (nombre, cedula, telefono, pin, rol, saldo_bs, saldo_wpc, saldo_usd, ganancia_neta) 
                     VALUES (%s, %s, %s, %s, 'PENDIENTE', 0.0, 0.0, 0.0, 0.0)""", 
                     (nombre, cedula, telefono, pin))
        conn.commit()
        return redirect(url_for('acceso'))
    except Exception as e:
        return f"<h1>⚠️ Error</h1><p>{e}</p><a href='/registro'>Volver</a>"
    finally:
        cur.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    dato = request.form.get('telefono_login', '').strip()
    pin = request.form.get('pin_login', '').strip()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE (cedula=%s OR telefono=%s) AND pin=%s", (dato, dato, pin))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        session['user_id'] = user['id']
        session['rol'] = user['rol'] # Guardamos el rol para seguridad
        return redirect(url_for('dashboard'))
    return "<h1>❌ Datos Incorrectos</h1><a href='/acceso'>Volver</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    
    cur.execute("SELECT * FROM recargas WHERE estado = 'PENDIENTE' ORDER BY id DESC")
    recargas_pendientes = cur.fetchall()
    
    cur.execute("SELECT * FROM usuarios WHERE rol = 'PENDIENTE' ORDER BY id DESC")
    usuarios_pendientes = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Si es Wilfredo, lo mandamos a su panel de control
    if u['cedula'] == '13496133':
        return render_template('ceo_panel.html', u=u, recargas=recargas_pendientes, usuarios=usuarios_pendientes)
    return render_template('dashboard.html', u=u)

# --- 🦅 NUEVA RUTA: PANEL MAESTRO DE WILFREDO ---
@app.route('/panel_maestro')
def panel_maestro():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    
    # Solo Wilfredo puede entrar aquí
    if u['cedula'] != '13496133':
        return "Acceso Denegado", 403
        
    cur.execute("SELECT * FROM usuarios ORDER BY nombre ASC")
    todos_los_usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('panel_maestro.html', u=u, usuarios=todos_los_usuarios)

# --- 💰 NUEVA RUTA: RECARGA MANUAL (EL PODER) ---
@app.route('/admin/recargar_manual', methods=['POST'])
def recargar_manual():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    cedula_target = request.form.get('cedula_usuario')
    monto = float(request.form.get('monto'))
    moneda = request.form.get('moneda')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Verificamos que quien opera sea Wilfredo
    cur.execute("SELECT cedula FROM usuarios WHERE id=%s", (session['user_id'],))
    admin = cur.fetchone()
    if admin['cedula'] != '13496133':
        return "No autorizado", 403

    # Buscamos al usuario destino
    cur.execute("SELECT * FROM usuarios WHERE cedula=%s", (cedula_target,))
    usuario = cur.fetchone()
    
    if usuario:
        if moneda == 'BS':
            cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE cedula = %s", (monto, cedula_target))
        else:
            cur.execute("UPDATE usuarios SET saldo_usd = saldo_usd + %s WHERE cedula = %s", (monto, cedula_target))
        
        conn.commit()
        cur.close()
        conn.close()
        return f"<h1>✅ ¡Poder Maestro!</h1><p>Asignaste {monto} {moneda} a {usuario['nombre']}.</p><a href='/panel_maestro'>Volver</a>"
    
    cur.close()
    conn.close()
    return "<h1>❌ Error</h1><p>Usuario no encontrado.</p><a href='/panel_maestro'>Volver</a>"

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    monto = request.form.get('monto')
    referencia = request.form.get('referencia')
    telf_destino = request.form.get('telf_destino', '')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO recargas (user_id, monto, referencia, telf_destino, estado) 
                     VALUES (%s, %s, %s, %s, 'PENDIENTE')""", 
                     (session['user_id'], monto, referencia, telf_destino))
        conn.commit()
        return "<h1>✅ Recarga en Verificación</h1><p>Wilfredo está revisando tu pago.</p><a href='/dashboard'>Volver</a>"
    except:
        return "<h1>⚠️ Error</h1><p>Esa referencia ya fue usada.</p><a href='/dashboard'>Volver</a>"
    finally:
        cur.close()
        conn.close()

@app.route('/aprobar_recarga/<int:id_recarga>')
def aprobar_recarga(id_recarga):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM recargas WHERE id = %s", (id_recarga,))
    r = cur.fetchone()
    if r:
        cur.execute("UPDATE recargas SET estado = 'APROBADA' WHERE id = %s", (id_recarga,))
        if r['telf_destino']:
            cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE telefono = %s", (r['monto'], r['telf_destino']))
        else:
            cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (r['monto'], r['user_id']))
        conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/instalar')
def instalar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios, recargas CASCADE")
    cur.execute("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, cedula TEXT UNIQUE, 
        telefono TEXT, pin TEXT, rol TEXT, 
        saldo_bs FLOAT DEFAULT 0.0, saldo_wpc FLOAT DEFAULT 0.0, 
        saldo_usd FLOAT DEFAULT 0.0, ganancia_neta FLOAT DEFAULT 0.0)""")
    
    cur.execute("""CREATE TABLE recargas (
        id SERIAL PRIMARY KEY, user_id INTEGER, monto FLOAT, 
        referencia TEXT UNIQUE, telf_destino TEXT, estado TEXT DEFAULT 'PENDIENTE')""")
    
    cur.execute("""INSERT INTO usuarios (nombre, cedula, telefono, pin, rol, saldo_bs, saldo_wpc, saldo_usd, ganancia_neta) 
                VALUES ('WILFREDO DONQUIZ', '13496133', '04126602555', '1234', 'CEO', 0.0, 0.0, 0.0, 0.0)""")
    
    conn.commit()
    cur.close()
    conn.close()
    return "<h1>🏛️ Will-Pay Sincronizado</h1>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
