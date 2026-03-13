from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
# Necesitarás instalar esta librería: pip install qrcode[pil]
import qrcode
import io
import base64

# 1. INICIO DEL SISTEMA
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- RUTAS DE ACCESO ---
@app.route('/acceso')
def acceso():
    return render_template('auth/acceso.html')

@app.route('/login', methods=['POST'])
def login():
    identificador = request.form.get('cedula')
    pin = request.form.get('pin')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE cedula = %s", (identificador,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and user['password'] == pin:
        session['user_id'] = user['id']
        session['user_rol'] = user['rol']
        return redirect(url_for('dashboard'))
    return "Error: Credenciales no coinciden."

# --- PANEL DE USUARIO DEFINITIVO (Fusionado con tu Diseño) ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cur.fetchone()
        
        # Historial para "Movimientos Recientes" (Serio como tu diseño)
        cur.execute("""
            SELECT fecha, referencia, monto, estatus, tipo FROM transacciones 
            WHERE emisor::text = %s::text OR receptor::text = %s::text 
            ORDER BY fecha DESC LIMIT 5
        """, (str(user['id']), str(user['id'])))
        movimientos = cur.fetchall()
    except Exception as e:
        return f"Error en Dashboard: {str(e)}"
    finally:
        cur.close()
        conn.close()
    
    return render_template('user/dashboard.html', u=user, movimientos=movimientos)

# --- MOTOR DE PAGOS QR DINÁMICO (Foto 1) ---
@app.route('/generar_qr_pago', methods=['POST'])
def generar_qr_pago():
    if 'user_id' not in session: return jsonify({'status': 'error'})
    
    monto = request.form.get('monto')
    emisor_id = session['user_id']
    
    # Datos que irán dentro del QR: emisor_id y monto
    datos_qr = f"{emisor_id}|{monto}"
    
    # Generar la imagen del QR en memoria
    img = qrcode.make(datos_qr)
    buf = io.BytesIO()
    img.save(buf)
    image_stream = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return jsonify({'status': 'ok', 'qr_image': image_stream})

# --- PROCESAR PAGO DESDE CÁMARA (Foto 1 interactuando) ---
@app.route('/procesar_pago_qr', methods=['POST'])
def procesar_pago_qr():
    # ... (Aquí va la lógica que ya teníamos para restar de uno y sumar a otro, 
    # pero recibiendo los datos que la cámara escaneó) ...
    # Al finalizar con éxito, debe retornar el ID de la transacción para el comprobante.
    transaccion_id = "WP-12345" # Ejemplo
    return jsonify({'status': 'ok', 'tx_id': transaccion_id})

# --- SISTEMA DE RECARGAS (Foto 2) ---
@app.route('/recargar')
def recargar():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('user/recargar.html')

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    # ... (Lógica para registrar la solicitud de recarga en la DB 
    # con los datos del pago móvil de la Foto 2) ...
    return redirect(url_for('dashboard'))

# --- GENERADOR DE COMPROBANTES DE AUDITORÍA (Foto 3 y 4) ---
@app.route('/comprobante/<tx_id>')
def comprobante(tx_id):
    if 'user_id' not in session: return redirect(url_for('acceso'))
    
    conn = get_db()
    cur = conn.cursor()
    # Buscar todos los datos de la transacción y de los usuarios involucrados 
    # para que sea serio para la auditoría (Foto 3)
    cur.execute("""
        SELECT t.*, u_e.nombre as emisor_nombre, u_r.nombre as receptor_nombre
        FROM transacciones t
        JOIN users u_e ON t.emisor::text = u_e.id::text
        JOIN users u_r ON t.receptor::text = u_r.id::text
        WHERE t.referencia = %s
    """, (tx_id,))
    tx_data = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('user/comprobante.html', tx=tx_data)

# --- RUTA DE INYECCIÓN DE EMERGENCIA ---
# (Mantener la que ya teníamos para crear tablas y usuarios de prueba)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
