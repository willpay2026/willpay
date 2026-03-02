from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import psycopg2, os
from psycopg2.extras import DictCursor
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'willpay_exchange_adn_2026'
DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL, sslmode='require')

# --- LÓGICA DE MINERÍA Y TRANSACCIONES ---
@app.route('/transferir', methods=['POST'])
def transferir():
    if 'user_id' not in session: return jsonify({"status": "error", "msg": "Sesión expirada"})
    
    datos = request.get_json()
    moneda = datos.get('moneda') # BS, USD, o WPC
    monto = float(datos.get('monto'))
    receptor_id = datos.get('receptor_id')
    
    # Algoritmo de Minería Orgánica: Regala 0.05 WPC por cada movimiento
    recompensa_wpc = 0.05 
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Verificar saldo en la moneda elegida
    col_saldo = f"saldo_{moneda.lower()}"
    cur.execute(f"SELECT {col_saldo} FROM usuarios WHERE id = %s", (session['user_id'],))
    saldo_actual = cur.fetchone()[0]
    
    if saldo_actual < monto:
        return jsonify({"status": "error", "msg": "Saldo insuficiente"})

    # EJECUCIÓN ATÓMICA
    try:
        # 1. Descontar al emisor
        cur.execute(f"UPDATE usuarios SET {col_saldo} = {col_saldo} - %s WHERE id = %s", (monto, session['user_id']))
        # 2. Sumar al receptor
        cur.execute(f"UPDATE usuarios SET {col_saldo} = {col_saldo} + %s WHERE id = %s", (monto, receptor_id))
        # 3. MINERÍA: Acreditar Will-Pay Coin al emisor por actividad
        cur.execute("UPDATE usuarios SET saldo_wpc = saldo_wpc + %s WHERE id = %s", (recompensa_wpc, session['user_id']))
        # 4. Registrar en historial
        cur.execute("INSERT INTO pagos (emisor_id, receptor_id, monto, moneda) VALUES (%s, %s, %s, %s)", 
                    (session['user_id'], receptor_id, monto, moneda))
        
        conn.commit()
        return jsonify({"status": "ok", "msg": f"Enviado! +{recompensa_wpc} WPC Minados"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "msg": str(e)})
    finally:
        cur.close()
        conn.close()

# --- INSTALACIÓN DE LA NUEVA ECONOMÍA ---
@app.route('/instalar')
def instalar_exchange():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios, pagos, configuracion CASCADE")
    # Tabla de Usuarios con Multibilletera
    cur.execute("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, cedula TEXT UNIQUE, telefono TEXT, 
        pin TEXT, rol TEXT, status TEXT DEFAULT 'ACTIVO',
        saldo_bs FLOAT DEFAULT 0.0, saldo_usd FLOAT DEFAULT 0.0, saldo_wpc FLOAT DEFAULT 0.0,
        foto_path TEXT)""")
    # Tabla de Configuración de Moneda (Valor del WPC)
    cur.execute("CREATE TABLE configuracion (clave TEXT PRIMARY KEY, valor FLOAT)")
    cur.execute("INSERT INTO configuracion (clave, valor) VALUES ('VALOR_WPC_BS', 25.50)")
    # Crear al Dueño (CEO)
    cur.execute("""INSERT INTO usuarios (nombre, cedula, pin, rol, saldo_bs, saldo_wpc) 
                   VALUES ('WILFREDO DONQUIZ', '13496133', '1234', 'CEO', 5000.0, 100.0)""")
    conn.commit()
    cur.close()
    conn.close()
    return "SISTEMA EXCHANGE SINCRONIZADO"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
