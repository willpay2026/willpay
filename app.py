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

# --- REGISTRO CON DATOS PARA REINTEGROS ---
@app.route('/registro', methods=['POST'])
def registro_usuario():
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    telefono = request.form.get('telefono')
    # Datos obligatorios para que el usuario reciba sus retiros [cite: 2026-03-01]
    banco = request.form.get('banco_pago_movil')
    telf_pm = request.form.get('telf_pago_movil')
    tipo_user = request.form.get('tipo_usuario') 

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO usuarios_willpay (nombre_completo, cedula_rif, telefono, banco_pago_movil, telf_pago_movil, tipo_usuario, saldo)
            VALUES (%s, %s, %s, %s, %s, %s, 0.00)
        """, (nombre, cedula, telefono, banco, telf_pm, tipo_user))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f"Error: {e}"
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('dashboard'))

# --- ACTUALIZACIÓN DE TASAS (SÓLO NÚMEROS) ---
@app.route('/actualizar_tasas', methods=['POST'])
def actualizar_tasas():
    t_pagos = request.form.get('tasa_pagos')
    t_tecnicos = request.form.get('tasa_tecnicos')
    t_juridicos = request.form.get('tasa_juridicos')
    
    conn = get_db()
    cur = conn.cursor()
    # Actualización masiva por tipo de usuario en el búnker
    cur.execute("UPDATE usuarios_willpay SET comision_asignada = %s WHERE tipo_usuario = 'natural'", (t_pagos,))
    cur.execute("UPDATE usuarios_willpay SET comision_asignada = %s WHERE tipo_usuario = 'tecnico'", (t_tecnicos,))
    cur.execute("UPDATE usuarios_willpay SET comision_asignada = %s WHERE tipo_usuario = 'juridico'", (t_juridicos,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('panel_ceo'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
