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

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    conf = query_db("SELECT * FROM configuracion WHERE id=1", one=True)
    
    es_ceo = "CEO" in str(u['id'])
    
    # AUDITORÍA TOTAL PARA EL CEO (Todas las columnas que pediste)
    auditoria = []
    if es_ceo:
        auditoria = query_db("SELECT * FROM transacciones ORDER BY fecha DESC LIMIT 50")
    
    # Ganancias calculadas
    res = query_db("SELECT SUM(monto * (%s/100)) as total FROM transacciones WHERE tipo='ENVIO' AND estatus='COMPLETADA'", (conf['p_envio'],), one=True)
    ganancias = res['total'] if res and res['total'] else 0

    return render_template('dashboard.html', user=u, conf=conf, es_ceo=es_ceo, auditoria=auditoria, ganancias_willpay=ganancias)

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'u' not in session: return redirect('/')
    monto = float(request.form.get('monto'))
    ref = request.form.get('referencia')
    conf = query_db("SELECT * FROM configuracion WHERE id=1", one=True)
    
    estatus = 'COMPLETADA' if conf['modo_auto'] else 'PENDIENTE'
    
    # Registrar la transacción
    query_db("INSERT INTO transacciones (usuario_id, tipo, monto, referencia, estatus) VALUES (%s, 'RECARGA', %s, %s, %s)", 
             (session['u'], monto, ref, estatus), commit=True)
    
    # Si es automático, sumar de una vez
    if conf['modo_auto']:
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (monto, session['u']), commit=True)
        
    return redirect('/dashboard')

@app.route('/aprobar_pago/<int:id>')
def aprobar_pago(id):
    t = query_db("SELECT * FROM transacciones WHERE id=%s AND estatus='PENDIENTE'", (id,), one=True)
    if t:
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (t['monto'], t['usuario_id']), commit=True)
        query_db("UPDATE transacciones SET estatus='COMPLETADA' WHERE id=%s", (id,), commit=True)
    return redirect('/dashboard')

# ... (Mantenemos las otras rutas de registro y config igual)
