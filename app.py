# --- PANEL DE USUARIO (DASHBOARD) ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cur.fetchone()
        
        # CAMBIO AQUÍ: Usamos 'emisor' y 'receptor' en lugar de '_id'
        cur.execute("""
            SELECT fecha, referencia, monto, estatus FROM transacciones 
            WHERE emisor = %s OR receptor = %s 
            ORDER BY fecha DESC LIMIT 5
        """, (user['id'], user['id']))
        movimientos = cur.fetchall()
    except Exception as e:
        return f"Error en Dashboard: {str(e)}"
    finally:
        cur.close()
        conn.close()
    
    return render_template('user/dashboard.html', u=user, movimientos=movimientos)

# --- RUTA DE INYECCIÓN CORREGIDA ---
@app.route('/inyectar_datos')
def inyectar_datos():
    try:
        conn = get_db()
        cur = conn.cursor()
        # Crear Tablas con los nombres que ya tienes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100),
                cedula VARCHAR(20) UNIQUE,
                telefono VARCHAR(20),
                password VARCHAR(20),
                rol VARCHAR(20) DEFAULT 'usuario',
                saldo DECIMAL(10,2) DEFAULT 500.0
            );
            CREATE TABLE IF NOT EXISTS transacciones (
                id SERIAL PRIMARY KEY,
                emisor INTEGER REFERENCES users(id),
                receptor INTEGER REFERENCES users(id),
                monto DECIMAL(10,2),
                tipo VARCHAR(50),
                referencia VARCHAR(100),
                estatus VARCHAR(20),
                fecha TIMESTAMP DEFAULT NOW()
            );
        """)
        # Metemos los usuarios de prueba
        cur.execute("""
            INSERT INTO users (nombre, cedula, telefono, password, rol, saldo)
            VALUES 
            ('Cliente Prueba', '101010', '04120000001', '1122', 'usuario', 500.00),
            ('Comercio Prueba', '202020', '04120000002', '3344', 'usuario', 0.00)
            ON CONFLICT (cedula) DO NOTHING;
        """)
        conn.commit()
        cur.close()
        conn.close()
        return "<h1>✅ Búnker Actualizado</h1><p>Nombres de columnas corregidos. ¡A probar!</p>"
    except Exception as e:
        return f"<h1>❌ Error</h1><p>{str(e)}</p>"
