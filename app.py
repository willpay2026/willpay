import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'willpay_legado_2026' # Llave para las sesiones de usuario

# 1. Conexión a la Base de Datos en Render
def get_db_connection():
    # Usa la variable de entorno de Render para mayor seguridad
    db_url = os.environ.get('DATABASE_URL') or "postgres://postgres:tu_password_aqui@localhost:5432/willpay_db"
    conn = psycopg2.connect(db_url)
    return conn

# 2. Inicialización del Sistema (Crea las tablas si no existen)
def inicializar_sistema():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id VARCHAR(20) PRIMARY KEY,
            nombre VARCHAR(100),
            telefono VARCHAR(20),
            actividad VARCHAR(50),
            nombre_linea VARCHAR(100),
            foto_cedula VARCHAR(255),
            saldo DECIMAL(12,2) DEFAULT 0.00,
            rol VARCHAR(20) DEFAULT 'USUARIO'
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Asegurar que las tablas existan al arrancar
try:
    inicializar_sistema()
except:
    pass

# 3. RUTAS DEL SISTEMA
@app.route('/')
def home():
    return redirect(url_for('acceso'))

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        cedula = request.form.get('id')
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT nombre, rol FROM usuarios WHERE id = %s", (cedula,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            session['user_id'] = cedula
            session['user_name'] = user[0]
            return redirect(url_for('dashboard'))
        return "Usuario no encontrado. Por favor regístrese."
    return render_template('acceso.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    telefono = request.form.get('telefono')
    actividad = request.form.get('actividad')
    nombre_linea = request.form.get('nombre_linea', 'N/A')
    
    # Manejo de imagen (Auditoría Visual)
    foto = request.files.get('foto_cedula')
    nombre_foto = "sin_foto.jpg"
    if foto:
        nombre_foto = f"cedula_{cedula}.jpg"
        # Asegúrate de tener la carpeta static/uploads creada
        foto.save(os.path.join('static/uploads', nombre_foto))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Lógica del Legado: Wilfredo es el CEO
        saldo_inicial = 5000.00 if "Wilfredo" in nombre else 10.00
        rol = "CEO-FOUNDER" if "Wilfredo" in nombre else "USUARIO"

        cur.execute("""
            INSERT INTO usuarios (id, nombre, telefono, actividad, nombre_linea, foto_cedula, saldo, rol)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (cedula, nombre, telefono, actividad, nombre_linea, nombre_foto, saldo_inicial, rol))
        conn.commit()
        return render_template('ticket_bienvenida.html', nombre=nombre, id=cedula, saldo=saldo_inicial)
    except Exception as e:
        conn.rollback()
        return f"Error: {e}"
    finally:
        cur.close()
        conn.close()

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('acceso'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE id = %s", (session['user_id'],))
    user_data = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', user=user_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('acceso'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
