from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import datetime

# --- LÓGICA DE TRANSACCIÓN ---
@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    if 'user_id' not in session: return jsonify({'success': False, 'message': 'Sesión expirada'})
    
    data = request.get_json()
    monto = float(data['monto'])
    emisor_id = session['user_id']
    
    conn = get_db()
    cur = conn.cursor()
    
    # VALIDACIÓN BÚNKER: ¿Tiene plata?
    cur.execute("SELECT saldo FROM users WHERE id = %s", (emisor_id,))
    user = cur.fetchone()
    
    if user['saldo'] < monto:
        return jsonify({'success': False, 'message': 'Saldo insuficiente para esta transacción'})

    # EJECUCIÓN: Descontar al emisor y registrar (aquí usarías el receptor real del QR)
    cur.execute("UPDATE users SET saldo = saldo - %s WHERE id = %s", (monto, emisor_id))
    
    # AUDITORÍA: Crear el correlativo WP-XXXX
    ref = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    cur.execute("""
        INSERT INTO transacciones (emisor_id, monto, tipo, referencia, estatus) 
        VALUES (%s, %s, 'PAGO_QR', %s, 'EXITOSO') RETURNING id
    """, (emisor_id, monto, ref))
    
    t_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'success': True, 't_id': t_id})

# --- REPORTE DE RECARGA (Pago Móvil Wilfredo) ---
@app.route('/reportar_pago', methods=['POST'])
def reportar_pago():
    ref = request.form.get('referencia')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Chequeo si la referencia ya se usó antes
    cur.execute("SELECT id FROM transacciones WHERE referencia = %s", (ref,))
    if cur.fetchone():
        return "Error: Esta referencia de pago ya fue procesada anteriormente."
    
    # Si es nueva, se guarda para que Wilfredo la apruebe en el búnker
    cur.execute("INSERT INTO transacciones (emisor_id, referencia, estatus) VALUES (%s, %s, 'PENDIENTE')", (session['user_id'], ref))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))
