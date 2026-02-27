from flask import Flask, render_template, request, redirect, session, os, datetime
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny'

DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

def query_db(query, args=(), one=False, commit=False):
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(query, args)
        rv = (cur.fetchone() if one else cur.fetchall()) if not commit else None
        cur.close()
        conn.close()
        return rv
    except Exception as e:
        print(f"Error DB: {e}")
        return None

@app.route('/enviar_pago', methods=['POST'])
def enviar_pago():
    if 'u' not in session: return redirect('/')
    emisor_id = session['u']
    receptor_cedula = request.form.get('receptor_id')
    monto = float(request.form.get('monto'))
    
    # 1. Buscar emisor y receptor
    emi = query_db("SELECT * FROM usuarios WHERE id=%s", (emisor_id,), one=True)
    rec = query_db("SELECT * FROM usuarios WHERE cedula=%s", (receptor_cedula,), one=True)
    
    if emi and rec and emi['saldo_bs'] >= monto:
        # 2. Generar Correlativo Legal
        serial = f"WP-TR-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 3. Mover la plata
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id = %s", (monto, emisor_id), commit=True)
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (monto, rec['id']), commit=True)
        
        # 4. Registrar en Auditoría
        query_db("""INSERT INTO transacciones (usuario_id, tipo, monto, referencia, estatus) 
                    VALUES (%s, 'ENVIO', %s, %s, 'COMPLETADA')""", 
                 (emisor_id, monto, serial), commit=True)
        
        # Guardar datos para el recibo en la sesión temporal
        session['ultimo_recibo'] = {
            'serial': serial, 'monto': monto,
            'emi_nom': emi['nombre'], 'emi_act': emi['actividad'],
            'rec_nom': rec['nombre'], 'rec_act': rec['actividad'],
            'fecha': datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        return redirect('/dashboard?pago=exito')
    
    return "Error: Saldo insuficiente o usuario no existe."
