from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026'

# CONEXIÓN AL BÚNKER EN RENDER
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# --- PANEL CEO: CONTROL DE MANDOS ---
@app.route('/panel_ceo')
def panel_ceo():
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Datos Financieros
    cur.execute("SELECT SUM(saldo) as total FROM usuarios_willpay")
    capital_bunker = cur.fetchone()['total'] or 0.00
    
    # 2. Usuarios para la tabla (10 en 10)
    cur.execute("SELECT id, telefono, actividad_economica, fecha_registro FROM usuarios_willpay ORDER BY fecha_registro DESC LIMIT 10")
    usuarios = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('panel_ceo.html', 
                           capital=capital_bunker, 
                           usuarios=usuarios)

# --- ACTUALIZAR TASAS DESDE LOS RECUADROS ---
@app.route('/actualizar_tasas', methods=['POST'])
def actualizar_tasas():
    # Los 3 recuadros manipulables
    tasa_pagos = request.form.get('tasa_pagos')
    tasa_actividades = request.form.get('tasa_actividades')
    tasa_juridica = request.form.get('tasa_juridica')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Actualizamos masivamente según el tipo de usuario
    cur.execute("UPDATE usuarios_willpay SET comision_asignada = %s WHERE tipo_usuario = 'natural'", (tasa_pagos,))
    cur.execute("UPDATE usuarios_willpay SET comision_asignada = %s WHERE tipo_usuario = 'firma'", (tasa_actividades,))
    cur.execute("UPDATE usuarios_willpay SET comision_asignada = %s WHERE tipo_usuario = 'juridico'", (tasa_juridica,))
    
    conn.commit()
    cur.close()
    conn.close()
    flash("Tasas actualizadas en todo el sistema Will-Pay")
    return redirect(url_for('panel_ceo'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
