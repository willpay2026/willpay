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

@app.route('/panel_ceo')
def panel_ceo():
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Capital Total y Ganancias
    cur.execute("SELECT SUM(saldo) as total FROM usuarios_willpay")
    capital = cur.fetchone()['total'] or 0.00
    
    # 2. Actividad en Vivo (10 en 10)
    cur.execute("""
        SELECT id, telefono, actividad_economica, fecha_registro 
        FROM usuarios_willpay ORDER BY fecha_registro DESC LIMIT 10
    """)
    usuarios = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('panel_ceo.html', capital=capital, usuarios=usuarios)

@app.route('/actualizar_tasas', methods=['POST'])
def actualizar_tasas():
    # Recuadros manipulables limpios
    t_pagos = request.form.get('tasa_pagos')
    t_retiros = request.form.get('tasa_retiros')
    t_juridicos = request.form.get('tasa_juridicos')
    
    conn = get_db()
    cur = conn.cursor()
    # Actualización masiva por tipo
    cur.execute("UPDATE usuarios_willpay SET comision_asignada = %s WHERE tipo_usuario = 'natural'", (t_pagos,))
    cur.execute("UPDATE usuarios_willpay SET comision_asignada = %s WHERE tipo_usuario = 'tecnico'", (t_retiros,))
    cur.execute("UPDATE usuarios_willpay SET comision_asignada = %s WHERE tipo_usuario = 'juridico'", (t_juridicos,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Tasas actualizadas con éxito")
    return redirect(url_for('panel_ceo'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
