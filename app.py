# --- RUTA DEL PANEL CEO ---
@app.route('/panel_ceo')
def panel_ceo():
    # Solo permitimos entrar si el usuario tiene rol de 'admin' o 'dueño'
    if 'user_id' not in session:
        return redirect(url_for('acceso'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Calculamos el Capital Total en el Búnker
    cur.execute("SELECT SUM(saldo) as total FROM users")
    capital = cur.fetchone()['total'] or 0.00
    
    # Obtenemos los últimos 10 movimientos para la tabla "Actividad en Vivo"
    cur.execute("SELECT id, nombre, rol, cedula FROM users ORDER BY id DESC LIMIT 10")
    usuarios = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('panel_ceo.html', capital=capital, usuarios=usuarios)

# --- ACCIÓN: CARGAR SALDO DIRECTO ---
@app.route('/cargar_saldo', methods=['POST'])
def cargar_saldo():
    cedula_destino = request.form.get('cedula')
    monto = float(request.form.get('monto'))
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Sumamos el monto al saldo del usuario destino
        cur.execute("UPDATE users SET saldo = saldo + %s WHERE cedula = %s", (monto, cedula_destino))
        conn.commit()
        print(f"Éxito: Se cargaron {monto} a la cédula {cedula_destino}")
    except Exception as e:
        conn.rollback()
        print(f"Error en recarga: {e}")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('panel_ceo'))
