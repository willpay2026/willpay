# --- RUTA DEL PANEL CEO ---
@app.route('/panel_ceo')
def panel_ceo():
    if 'user_id' not in session:
        return redirect(url_for('acceso'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Obtenemos la configuración de automatización (los interruptores)
    cur.execute("SELECT * FROM config_ceo WHERE id = 1")
    config = cur.fetchone()
    
    # 2. Calculamos el Capital Total en el Búnker
    cur.execute("SELECT SUM(saldo) as total FROM users")
    resultado_capital = cur.fetchone()
    capital = resultado_capital['total'] if resultado_capital['total'] else 0.00
    
    # 3. Obtenemos los últimos 10 usuarios para la tabla
    cur.execute("SELECT id, nombre, rol, cedula FROM users ORDER BY id DESC LIMIT 10")
    usuarios = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Enviamos 'config', 'capital' y 'usuarios' al HTML
    return render_template('panel_ceo.html', config=config, capital=capital, usuarios=usuarios)

# --- NUEVA ACCIÓN: CAMBIAR INTERRUPTORES ---
@app.route('/actualizar_config', methods=['POST'])
def actualizar_config():
    # Detectamos si los interruptores están ON u OFF
    auto_saldo = True if request.form.get('auto_saldo') == 'on' else False
    auto_retiro = True if request.form.get('auto_retiro') == 'on' else False
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE config_ceo 
        SET auto_saldo = %s, auto_retiro = %s 
        WHERE id = 1
    """, (auto_saldo, auto_retiro))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('panel_ceo'))
