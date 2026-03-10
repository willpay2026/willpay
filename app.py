@app.route('/panel_ceo')
def panel_ceo():
    conn = get_db()
    cur = conn.cursor()
    
    # CAPITAL Y GANANCIAS
    cur.execute("SELECT SUM(saldo) as total FROM usuarios_willpay")
    res_capital = cur.fetchone()
    capital = res_capital['total'] if res_capital['total'] else 0.00
    
    # GANANCIA ESTIMADA (Legado)
    ganancias_legado = capital * 0.015  # Un ejemplo del 1.5%

    # USUARIOS Y ACTIVIDAD (Traemos más detalles para la tabla)
    cur.execute("""
        SELECT cedula_rif, telefono, tipo_usuario, saldo, fecha_registro 
        FROM usuarios_willpay 
        ORDER BY fecha_registro DESC 
        LIMIT 10
    """)
    usuarios = cur.fetchall()

    # PAGOS QUE ESPERAN POR TU BEEP
    cur.execute("""
        SELECT m.id, u.nombre_completo, m.monto, m.referencia, m.comprobante_url 
        FROM movimientos_willpay m 
        JOIN usuarios_willpay u ON m.cedula_usuario = u.cedula_rif 
        WHERE m.estatus = 'Pendiente'
    """)
    pendientes = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('panel_ceo.html', 
                           capital=capital, 
                           ganancias=ganancias_legado, 
                           usuarios=usuarios, 
                           pendientes=pendientes)
