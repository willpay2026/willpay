import hashlib

# --- LÓGICA DE MONEDA ESTABLE Y TRAZABILIDAD ---
def generar_trazabilidad(emisor_id, receptor_id, monto, moneda):
    # Crea un hash único para que la minería sea auditable (ADN de la transacción)
    bloque = f"{emisor_id}-{receptor_id}-{monto}-{moneda}-{datetime.now()}"
    return hashlib.sha256(bloque.encode()).hexdigest()

@app.route('/procesar_operacion', methods=['POST'])
def procesar_operacion():
    if 'user_id' not in session: return jsonify({"status": "error"})
    
    datos = request.get_json()
    tipo = datos.get('tipo') # 'PAGO' o 'COBRO'
    moneda = datos.get('moneda') # 'BS', 'USD', 'WPC'
    monto = float(datos.get('monto'))
    otra_parte_id = datos.get('otra_parte_id')
    
    trazabilidad = generar_trazabilidad(session['user_id'], otra_parte_id, monto, moneda)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Si es PAGO, descuenta al usuario. Si es COBRO, le suma tras validar.
    col = f"saldo_{moneda.lower()}"
    
    if tipo == 'PAGO':
        # Aplicar comisión de red (1.5%) para estabilidad del fondo
        comision = monto * 0.015
        total = monto + comision
        cur.execute(f"UPDATE usuarios SET {col} = {col} - %s WHERE id = %s", (total, session['user_id']))
        cur.execute(f"UPDATE usuarios SET {col} = {col} + %s WHERE id = %s", (monto, otra_parte_id))
        # MINERÍA: Emite moneda estable WPC como incentivo de red
        cur.execute("UPDATE usuarios SET saldo_wpc = saldo_wpc + 0.05 WHERE id = %s", (session['user_id'],))
    
    # Registrar la huella digital de la operación para auditoría CEO
    cur.execute("""INSERT INTO pagos (emisor_id, receptor_id, monto, moneda, hash_trazabilidad) 
                   VALUES (%s, %s, %s, %s, %s)""", 
                (session['user_id'], otra_parte_id, monto, moneda, trazabilidad))
    
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "Operación Segura", "hash": trazabilidad})
