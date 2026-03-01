from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os
from psycopg2.extras import DictCursor

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
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    
    # 🦅 OJO DE ÁGUILA: Tú ves las recargas pendientes para aprobar
    cur.execute("SELECT * FROM recargas WHERE estado = 'PENDIENTE' ORDER BY id DESC")
    recargas_pendientes = cur.fetchall()
    
    cur.close()
    conn.close()
    if u['cedula'] == '13496133':
        return render_template('ceo_panel.html', u=u, recargas=recargas_pendientes)
    return render_template('dashboard.html', u=u)

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    user_id = session.get('user_id')
    monto = request.form.get('monto')
    referencia = request.form.get('referencia') # Para evitar repetidos
    telf_destino = request.form.get('telf_destino') # Recarga a familiar
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Validamos que la referencia no se haya usado antes (Ojo de Águila)
        cur.execute("INSERT INTO recargas (user_id, monto, referencia, telf_destino, estatus) VALUES (%s, %s, %s, %s, 'PENDIENTE')",
                    (user_id, monto, referencia, telf_destino))
        conn.commit()
        return "<h1>✅ Enviado</h1><p>Wilfredo verificará tu pago.</p><a href='/dashboard'>Volver</a>"
    except:
        return "<h1>⚠️ Error</h1><p>Esa referencia ya fue usada o es inválida.</p><a href='/dashboard'>Volver</a>"
    finally:
        cur.close()
        conn.close()

@app.route('/instalar')
def instalar():
    conn = get_db_connection()
    cur = conn.cursor()
    # Creamos la tabla de usuarios y la nueva de RECARGAS
    cur.execute("DROP TABLE IF EXISTS usuarios, recargas CASCADE")
    cur.execute("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, cedula TEXT UNIQUE, 
        telefono TEXT, pin TEXT, rol TEXT, 
        saldo_bs FLOAT DEFAULT 0.0, saldo_wpc FLOAT DEFAULT 0.0, 
        saldo_usd FLOAT DEFAULT 0.0, ganancia_neta FLOAT DEFAULT 0.0)""")
    
    cur.execute("""CREATE TABLE recargas (
        id SERIAL PRIMARY KEY, user_id INTEGER, monto FLOAT, 
        referencia TEXT UNIQUE, telf_destino TEXT, estatus TEXT)""")
    
    cur.execute("""INSERT INTO usuarios (nombre, cedula, telefono, pin, rol, saldo_bs, saldo_wpc, saldo_usd, ganancia_neta) 
                VALUES ('WILFREDO DONQUIZ', '13496133', '04126602555', '1234', 'CEO', 100.0, 50.0, 10.0, 5.0)""")
    conn.commit()
    cur.close()
    conn.close()
    return "<h1>🏛️ Sistema Blindado</h1><p>Tablas de Usuarios y Recargas listas.</p>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

