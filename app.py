from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny' # El legado para tu hija
DB_URL = os.environ.get('DATABASE_URL')

# --- MOTOR DE BASE DE DATOS ---
def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=DictCursor)
    try:
        cur.execute(query, args)
        if commit:
            conn.commit()
            return None
        return cur.fetchone() if one else cur.fetchall()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# --- RUTAS DE FLUJO ---
@app.route('/')
def index(): 
    return render_template('splash.html') # El splash con el logo dorado

@app.route('/acceso')
def acceso(): 
    return render_template('acceso.html') # Acceso seguro al panel

@app.route('/registro')
def registro(): 
    return render_template('registro.html') # Registro KYC con las nuevas categorías

# --- PROCESAMIENTO KYC Y GENERACIÓN DE DNA ---
@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre').upper()
    cedula = request.form.get('cedula').strip()
    telefono = request.form.get('telefono').strip()
    actividad = request.form.get('actividad')
    nombre_linea = request.form.get('nombre_linea') or "PARTICULAR"
    pin = request.form.get('pin')

    # Generación de ID DNA único
    id_dna = f"WP-{cedula[-4:]}-{actividad[:3].upper()}"

    try:
        query_db("""
            INSERT INTO usuarios 
            (nombre, cedula, telefono, actividad, nombre_linea, pin, id_dna, saldo_bs, estatus_kyc)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0.0, 'ACTIVO / AUDITADO')
        """, (nombre, cedula, telefono, actividad, nombre_linea, pin, id_dna), commit=True)
        
        user = query_db("SELECT id FROM usuarios WHERE cedula=%s", (cedula,), one=True)
        return redirect(url_for('ver_certificado', user_id=user['id']))
    except Exception as e:
        return f"Error en registro: {str(e)} <a href='/registro'>Reintentar</a>"

# --- VISTAS DE DOCUMENTACIÓN ---
@app.route('/certificado/<int:user_id>')
def ver_certificado(user_id):
    user = query_db("SELECT * FROM usuarios WHERE id=%s", (user_id,), one=True)
    return render_template('certificado.html', user=user) # Tu certificado premium

@app.route('/expediente/<int:user_id>')
def ver_expediente(user_id):
    if 'user_id' not in session: return redirect(url_for('acceso'))
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (user_id,), one=True)
    historial = query_db("SELECT * FROM movimientos WHERE usuario_id=%s ORDER BY fecha DESC", (user_id,))
    return render_template('expediente.html', u=u, historial=historial) # Expediente digital

# --- DASHBOARD Y TABLERO MAESTRO ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    # Tus datos de Banesco para las recargas
    mis_datos = {"banco": "BANESCO", "pago_movil": "04126602555", "cedula": "13496133"}
    
    # Si eres el CEO (Wilfredo), cargamos el Tablero 8
    if u['id_dna'] == "CEO-0001-FOUNDER" or u['cedula'] == "13496133":
        usuarios_vivos = query_db("SELECT * FROM usuarios ORDER BY id DESC LIMIT 5")
        return render_template('tablero8.html', u=u, m=mis_datos, usuarios=usuarios_vivos)
    
    return render_template('dashboard.html', u=u, m=mis_datos)

# --- SISTEMA DE INSTALACIÓN (LIMPIEZA CASCADE) ---
@app.route('/instalar')
def instalar():
    try:
        # CASCADE elimina las dependencias que daban error
        query_db("DROP TABLE IF EXISTS movimientos CASCADE", commit=True)
        query_db("DROP TABLE IF EXISTS usuarios CASCADE", commit=True)

        # Tabla de Usuarios completa
        query_db("""
            CREATE TABLE usuarios (
                id SERIAL PRIMARY KEY,
                id_dna TEXT UNIQUE,
                nombre TEXT,
                telefono TEXT UNIQUE,
                cedula TEXT UNIQUE,
                pin TEXT,
                actividad TEXT,
                nombre_linea TEXT,
                saldo_bs FLOAT DEFAULT 0.0,
                saldo_usd FLOAT DEFAULT 0.0,
                saldo_wpc FLOAT DEFAULT 0.0,
                sw_pagos BOOLEAN DEFAULT TRUE,
                sw_legado BOOLEAN DEFAULT TRUE,
                estatus_kyc TEXT DEFAULT 'ACTIVO',
                banco TEXT DEFAULT 'WILL-PAY BANK'
            )
        """, commit=True)

        # Tabla de Movimientos para el Expediente
        query_db("""
            CREATE TABLE movimientos (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
                tipo TEXT,
                monto FLOAT,
                referencia TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, commit=True)

        # Insertamos tu perfil de CEO por defecto para que no pierdas acceso
        query_db("""
            INSERT INTO usuarios (id_dna, nombre, telefono, cedula, pin, actividad, saldo_bs)
            VALUES ('CEO-0001-FOUNDER', 'WILFREDO DONQUIZ', '04126602555', '13496133', '1234', 'CEO', 100000.0)
        """, commit=True)

        return "<h1>🏛️ Bóveda Will-Pay V3 Reiniciada con ÉXITO</h1><p>Ve a /acceso e ingresa como CEO o crea un nuevo usuario en /registro</p>"
    except Exception as e:
        return f"<h1>Error Crítico:</h1><p>{str(e)}</p>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('acceso'))

if __name__ == '__main__':
    app.run(debug=True)
