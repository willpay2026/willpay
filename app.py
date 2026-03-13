# --- RUTA PARA REPORTAR RECARGAS ---
@app.route('/reportar_pago', methods=['POST'])
def reportar_pago():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    user_id = session['user_id']
    referencia = request.form.get('referencia')
    monto = request.form.get('monto')
    capture = request.files.get('capture') # Aquí procesarías el archivo
    
    conn = get_db()
    cur = conn.cursor()
    
    # Verificamos si la referencia ya existe (Seguridad Will-Pay)
    cur.execute("SELECT id FROM transacciones WHERE referencia = %s", (referencia,))
    if cur.fetchone():
        return "Error: Esta referencia ya fue utilizada."

    # Guardamos el reporte como "Pendiente" para que Wilfredo lo apruebe
    cur.execute("""
        INSERT INTO transacciones (emisor_id, monto, tipo, referencia, estatus) 
        VALUES (%s, %s, 'RECARGA', %s, 'PENDIENTE')
    """, (user_id, monto, referencia))
    
    conn.commit()
    cur.close()
    conn.close()
    return "Reporte enviado. En breve Wilfredo validará tu saldo."

# --- ACTUALIZACIÓN DEL DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    # Datos para el HTML
    u = {
        'id': user['id'],
        'nombre': user['nombre'],
        'saldo': user['saldo'],
        'fecha_registro': '2026-03-13' # Puedes jalarla de la DB
    }
    return render_template('user/dashboard.html', u=u)
