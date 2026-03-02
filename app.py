import hashlib
from datetime import datetime
# (Mantener importaciones previas de Flask y Psycopg2)

# --- ALGORITMO DE ESTABILIDAD Y MINERÍA ---
def registrar_mineria_trazable(emisor_id, receptor_id, monto, moneda):
    # Crea el ADN de la operación (Trazabilidad pura)
    bloque_datos = f"{emisor_id}-{receptor_id}-{monto}-{moneda}-{datetime.now()}"
    hash_operacion = hashlib.sha256(bloque_datos.encode()).hexdigest()
    return hash_operacion

@app.route('/operacion_global', methods=['POST'])
def operacion_global():
    if 'user_id' not in session: return jsonify({"status": "error"})
    
    d = request.get_json()
    tipo = d.get('tipo') # PAGAR o COBRAR
    moneda = d.get('moneda') # BS, USD, WPC
    monto = float(d.get('monto'))
    destino_id = d.get('destino_id')
    
    hash_id = registrar_mineria_trazable(session['user_id'], destino_id, monto, moneda)
    
    conn = get_db_connection()
    cur = conn.cursor()
    col = f"saldo_{moneda.lower()}"

    try:
        # Lógica de Moneda Estable: El WPC se mina con cada uso de red
        if tipo == 'PAGAR':
            # Cobro de comisión de red para el fondo de reserva del CEO
            comision = monto * 0.015
            total_cargo = monto + comision
            
            cur.execute(f"UPDATE usuarios SET {col} = {col} - %s WHERE id = %s", (total_cargo, session['user_id']))
            cur.execute(f"UPDATE usuarios SET {col} = {col} + %s WHERE id = %s", (monto, destino_id))
            
            # Acreditar Ganancia al CEO
            cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE rol = 'CEO'", (comision,))
            
            # MINERÍA ORGÁNICA: Emisión de Will-Pay Coin (WPC)
            cur.execute("UPDATE usuarios SET saldo_wpc = saldo_wpc + 0.05 WHERE id = %s", (session['user_id'],))
        
        # Guardar en Historial con Hash de Trazabilidad
        cur.execute("""INSERT INTO pagos (emisor_id, receptor_id, monto, moneda, hash_trazabilidad) 
                       VALUES (%s, %s, %s, %s, %s)""", 
                    (session['user_id'], destino_id, monto, moneda, hash_id))
        
        conn.commit()
        return jsonify({"status": "Éxito", "trazabilidad": hash_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "Error", "
