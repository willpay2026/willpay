@app.before_request
def inicializar_sistema():
    if not session.get('db_ready'):
        # TABLA DE USUARIOS: El ADN del Sistema
        query_db("""CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY, 
            id_dna VARCHAR(50) UNIQUE,
            nombre VARCHAR(100), 
            telefono VARCHAR(20) UNIQUE, 
            cedula VARCHAR(50),
            pin VARCHAR(6), 
            tipo_usuario VARCHAR(50), 
            saldo_bs DECIMAL(15, 2) DEFAULT 0.00,
            saldo_wpc DECIMAL(15, 2) DEFAULT 0.00,
            saldo_usd DECIMAL(15, 2) DEFAULT 0.00,
            es_socio BOOLEAN DEFAULT FALSE,
            es_ceo BOOLEAN DEFAULT FALSE
        );""", commit=True)

        # TABLA DE TRANSACCIONES: Transparencia SUDEBAN
        query_db("""CREATE TABLE IF NOT EXISTS transacciones (
            id SERIAL PRIMARY KEY, 
            usuario_id INT, 
            tipo VARCHAR(20), 
            monto DECIMAL(15, 2), 
            moneda VARCHAR(10) DEFAULT 'BS',
            referencia VARCHAR(50) UNIQUE, 
            capture_path VARCHAR(255),
            estatus VARCHAR(20) DEFAULT 'PENDIENTE', 
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""", commit=True)
        session['db_ready'] = True
