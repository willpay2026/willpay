from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026'

# CONEXIÓN AL BÚNKER EN RENDER
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# --- REGISTRO CON DATOS DE PAGO MÓVIL PARA RETIROS ---
@app.route('/registro', methods=['POST'])
def registro_usuario():
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    telefono = request.form.get('telefono')
    # Datos para el Reintegro (Retiro) [cite: 2026-03-01]
    banco_receptor = request.form.get('banco_receptor')
    telf_pago_movil = request.form.get('telf_pago_movil')
    tipo_user = request.form.get('tipo_usuario') # natural, firma, juridico

    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO usuarios_willpay (nombre_completo, cedula_rif, telefono, banco_pago_movil, telf_pago_movil, tipo_usuario, saldo)
            VALUES (%s, %s, %s, %s, %s, %s, 0.00)
        """, (nombre, cedula, telefono, banco_receptor, telf_pago_movil, tipo_user))
        conn.commit()
        flash("Registro exitoso. Ya puedes usar Will-Pay.")
    except Exception as e:
        conn.rollback()
        flash(f"Error en registro: {e}")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('login'))

# --- SOLICITUD DE RETIRO (USER) ---
@app.route('/solicitar_retiro', methods=['POST'])
def solicitar_retiro():
    monto = float(request.form.get('monto'))
    user_id = session.get('user_id')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Verificar si tiene saldo suficiente
    cur.execute("SELECT saldo FROM usuarios_willpay WHERE cedula_rif = %s", (user_id,))
    saldo_actual = cur.fetchone()['saldo']
    
    if saldo_actual >= monto:
        # Descontar saldo y poner en espera
        cur.execute("UPDATE usuarios_willpay SET saldo = saldo - %s WHERE cedula_rif = %s", (monto, user_id))
        cur.execute("""
            INSERT INTO movimientos_willpay (cedula_usuario, tipo_operacion, monto, estatus)
            VALUES (%s, 'Retiro Pendiente', %s, 'En Espera')
        """, (user_id, monto))
        conn.commit()
        flash("Solicitud enviada. El CEO procesará tu pago móvil.")
    else:
        flash("Saldo insuficiente para este retiro.")
        
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))

# --- PANEL CEO: VER RETIROS POR PAGAR ---
@app.route('/panel_ceo')
def panel_ceo():
    conn = get_db()
    cur = conn.cursor()
    
    # Traer retiros pendientes con los datos bancarios del usuario [cite: 2026-03-01]
    cur.execute("""
        SELECT m.id, u.nombre_completo, u.banco_pago_movil, u.telf_pago_movil, u.cedula_rif, m.monto
        FROM movimientos_willpay m
        JOIN usuarios_willpay u ON m.cedula_usuario = u.cedula_rif
        WHERE m.tipo_operacion = 'Retiro Pendiente' AND m.estatus = 'En Espera'
    """)
    retiros_pendientes = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('panel_ceo.html', retiros=retiros_pendientes)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
