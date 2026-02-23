# ... (todo igual arriba) ...

@app.route('/procesar_pago/<emisor>/<monto>/<receptor>/<pin>')
def procesar_pago(emisor, monto, receptor, pin):
    users = obtener_usuarios()
    m = float(monto)
    if emisor in users and users[emisor]['PIN'] == pin and float(users[emisor]['Saldo_Bs']) >= m:
        
        # --- AQUÍ ESTÁ TU ESTRATEGIA DE GANANCIA ---
        comision = m * 0.01  # El 1% para Will
        pago_final = m - comision
        
        # Descontar todo al pasajero
        users[emisor]['Saldo_Bs'] = str(round(float(users[emisor]['Saldo_Bs']) - m, 2))
        
        # Darle su parte al chofer (el 99%)
        users[receptor]['Saldo_Bs'] = str(round(float(users[receptor]['Saldo_Bs']) + pago_final, 2))
        
        # ¡MANDAR TU 1% AL ADMIN!
        if 'admin' in users:
            users['admin']['Saldo_Bs'] = str(round(float(users['admin']['Saldo_Bs']) + comision, 2))
        
        # Guardar cambios en el archivo
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            writer.writeheader()
            for u in users.values(): writer.writerow(u)
            
        registrar_movimiento(emisor, receptor, m, f"Pago Pasaje (Comisión: {comision})")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"})

# ... (el resto del código igual) ...
