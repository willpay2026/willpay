from flask import Flask, render_template, request, redirect, session, flash, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

DB_URL = os.environ.get('DATABASE_URL')

def query_db(query, args=(), one=False, commit=False):
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor(cursor_factory=DictCursor)
        rv = None
        cur.execute(query, args)
        if not commit:
            rv = cur.fetchone() if one else cur.fetchall()
        cur.close()
        conn.close()
        return rv
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.before_request
def inicializar_sistema():
    if not session.get('db_ready'):
        query_db("CREATE TABLE IF NOT EXISTS usuarios (id VARCHAR(50) PRIMARY KEY, nombre VARCHAR(100), cedula VARCHAR(20), actividad VARCHAR(100), saldo_bs DECIMAL(15, 2) DEFAULT 0.00);", commit=True)
        query_db("CREATE TABLE IF NOT EXISTS transacciones (id SERIAL PRIMARY KEY, usuario_id VARCHAR(50), tipo VARCHAR(20), monto DECIMAL(15, 2), referencia VARCHAR(50), estatus VARCHAR(20), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP);", commit=True)
        query_db("CREATE TABLE IF NOT EXISTS configuracion (id INT PRIMARY KEY, p_envio DECIMAL(5,2), p_retiro DECIMAL(5,2), modo_auto BOOLEAN);", commit=True)
        query_db("INSERT INTO configuracion (id, p_envio, p_retiro, modo_auto) VALUES (1, 2.5, 3.0, FALSE) ON CONFLICT DO NOTHING", commit=True)
        session['db_ready'] = True

@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        cedula = request.form.get('id', '').strip()
        u = query_db("SELECT * FROM usuarios WHERE cedula=%s", (cedula,), one=True)
        if u: session['u'] = u['id']; return redirect('/dashboard')
        return "Usuario no registrado."
    return render_template('acceso.html')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    conf = query_db("SELECT * FROM configuracion WHERE id=1", one=True)
    es_ceo = "CEO" in str(u['id'])
    auditoria = query_db("SELECT * FROM transacciones ORDER BY fecha DESC LIMIT 50") if es_ceo else []
    res = query_db("SELECT SUM(monto * (%s/100)) as total FROM transacciones WHERE tipo='ENVIO' AND estatus='COMPLETADA'", (conf['p_envio'],), one=True)
    ganancias = res['total'] if res and res['total'] else 0
    return render_template('dashboard.html', user=u, conf=conf, es_ceo=es_ceo, auditoria=auditoria, ganancias_willpay=ganancias)

@app.route('/actualizar_config', methods=['POST'])
def actualizar_config():
    p_envio = float(request.form.get('p_envio'))
    p_retiro = float(request.form.get('p_retiro'))
    modo_auto = 'modo_auto' in request.form
    query_db("UPDATE configuracion SET p_envio=%s, p_retiro=%s, modo_auto=%s WHERE id=1", (p_envio, p_retiro, modo_auto), commit=True)
    return redirect('/dashboard')

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    monto = float(request.form.get('monto'))
    ref = request.form.get('referencia')
    conf = query_db("SELECT * FROM configuracion WHERE id=1", one=True)
    estatus = 'COMPLETADA' if conf['modo_auto'] else 'PENDIENTE'
    query_db("INSERT INTO transacciones (usuario_id, tipo, monto, referencia, estatus) VALUES (%s, 'RECARGA', %s, %s, %s)", (session['u'], monto, ref, estatus), commit=True)
    if conf['modo_auto']: query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (monto, session['u']), commit=True)
    return redirect('/dashboard')

@app.route('/aprobar_pago/<int:id>')
def aprobar_pago(id):
    t = query_db("SELECT * FROM transacciones WHERE id=%s AND estatus='PENDIENTE'", (id,), one=True)
    if t:
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (t['monto'], t['usuario_id']), commit=True)
        query_db("UPDATE transacciones SET estatus='COMPLETADA' WHERE id=%s",
