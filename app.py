from flask import Flask, render_template, request, redirect, session, flash, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

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
        # Tablas Base
        query_db("CREATE TABLE IF NOT EXISTS usuarios (id VARCHAR(50) PRIMARY KEY, nombre VARCHAR(100), cedula VARCHAR(20), actividad VARCHAR(100), saldo_bs DECIMAL(15, 2) DEFAULT 0.00);", commit=True)
        query_db("CREATE TABLE IF NOT EXISTS transacciones (id SERIAL PRIMARY KEY, usuario_id VARCHAR(50), tipo VARCHAR(20), monto DECIMAL(15, 2), referencia VARCHAR(50), estatus VARCHAR(20), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP);", commit=True)
        query_db("CREATE TABLE IF NOT EXISTS configuracion (id INT PRIMARY KEY, p_envio DECIMAL(5,2), p_retiro DECIMAL(5,2), modo_auto BOOLEAN);", commit=True)
        
        # Migración: Columnas para la Minería y Multimoneda
        try:
            query_db("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS saldo_wpc DECIMAL(15, 2) DEFAULT 0.00;", commit=True)
            query_db("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS saldo_usd DECIMAL(15, 2) DEFAULT 0.00;", commit=True)
            query_db("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS puntos_mineria INT DEFAULT 0;", commit=True)
            query_db("ALTER TABLE configuracion ADD COLUMN IF NOT EXISTS tasa_wpc DECIMAL(15, 2) DEFAULT 15.50;", commit=True)
        except: pass

        query_db("INSERT INTO configuracion (id, p_envio, p_retiro, modo_auto, tasa_wpc) VALUES (1, 2.5, 3.0, FALSE, 15.50) ON CONFLICT DO NOTHING", commit=True)
        session['db_ready'] = True

@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        cedula = request.form.get('id', '').strip()
        u = query_db("SELECT * FROM usuarios WHERE cedula=%s", (cedula,), one=True)
        if u: 
            session['u'] = u['id']
            return redirect(url_for('dashboard'))
        flash("Usuario no registrado.")
    return render_template('acceso.html')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    if not u: return redirect('/logout')
    
    conf = query_db("SELECT * FROM configuracion WHERE id=1", one=True)
    es_ceo = "CEO" in str(u['id']).upper()
    
    auditoria = query_db("SELECT * FROM transacciones ORDER BY fecha DESC LIMIT 50") if es_ceo else []
    
    return render_template('dashboard.html', user=u, conf=conf, es_ceo=es_ceo, auditoria=auditoria)

@app.route('/minar', methods=['POST'])
def minar():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    
    nueva_energia = u['puntos_mineria'] + 10
    
    if nueva_energia >= 100:
        query_db("UPDATE usuarios SET puntos_mineria=0, saldo_wpc = saldo_wpc + 1 WHERE id=%s", (session['u'],), commit=True)
        flash("¡BRUTAL! Has minado 1 Will-Pay Coin (₩).")
    else:
        query_db("UPDATE usuarios SET puntos_mineria=%s WHERE id=%s", (nueva_energia, session['u']), commit=True)
        flash(f"Energía de minería aumentada al {nueva_energia}%")
        
    return redirect('/dashboard')

@app.route('/convertir', methods=['POST'])
def convertir():
    monto_usd = float(request.form.get('monto_usd', 0))
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    conf = query_db("SELECT * FROM configuracion WHERE id=1", one=True)
    
    costo_wpc = monto_usd * float(conf['tasa_wpc'])
    
    if u['saldo_wpc'] >= costo_wpc:
        query_db("UPDATE usuarios SET saldo_wpc = saldo_wpc - %s, saldo_usd = saldo_usd + %s WHERE id=%s", (costo_wpc, monto_usd, session['u']), commit=True)
        flash(f"Cambio exitoso: +${monto_usd} USD")
    else:
        flash("No tienes suficientes WPC para esta conversión.")
        
    return redirect('/dashboard')

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    monto = float(request.form.get('monto'))
    ref = request.form.get('referencia')
    query_db("INSERT INTO transacciones (usuario_id, tipo, monto, referencia, estatus) VALUES (%s, 'RECARGA', %s, %s, 'PENDIENTE')", (session['u'], monto, ref), commit=True)
    flash("Recarga notificada. Esperando aprobación del Founder.")
    return redirect('/dashboard')

@app.route('/aprobar_pago/<int:id>')
def aprobar_pago(id):
    t = query_db("SELECT * FROM transacciones WHERE id=%s AND estatus='PENDIENTE'", (id,), one=True)
    if t:
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (t['monto'], t['usuario_id']), commit=True)
        query_db("UPDATE transacciones SET estatus='COMPLETADA' WHERE id=%s", (id,), commit=True)
    return redirect('/dashboard')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    n, c, a = request.form.get('nombre'), request.form.get('cedula'), request.form.get('actividad')
    corr = "CEO-0001-FOUNDER" if "WILFREDO" in n.upper() else f"US-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
    s_bs = 5000.0 if "CEO" in corr else 0.0
    query_db("INSERT INTO usuarios (id, nombre, cedula, actividad, saldo_bs, saldo_wpc, saldo_usd) VALUES (%s,%s,%s,%s,%s, 0, 0)", (corr, n, c, a, s_bs), commit=True)
    session['u'] = corr
    return redirect('/dashboard')

@app.route('/logout')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

