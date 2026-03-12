from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    # Conexión a la base de datos en Render
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# ==========================================
# >>> CONFIGURACIÓN DE RUTAS DE ACCESO <<<
# ==========================================

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    return render_template('acceso.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/panel_ceo')
def panel_ceo():
    conn = get_db()
    cur = conn.cursor()
    # Buscamos la configuración del CEO
    cur.execute("SELECT * FROM config_ceo WHERE id = 1")
    config = cur.fetchone()
    # Sumamos el capital total y lo depositado
    cur.execute("SELECT SUM(saldo) as total, SUM(depositado) as dep FROM users")
    res = cur.fetchone()
    # Lista de los últimos 10 usuarios
    cur.execute("SELECT id, nombre, telefono, rol, cedula FROM users ORDER BY id DESC LIMIT 10")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('panel_ceo.html', config=config, capital=res['total'] or 0.0, depositado=res['dep'] or 0.0, usuarios=usuarios)

# Rutas de guardado de porcentajes
@app.route('/actualizar_porcentajes', methods=['POST'])
def actualizar_porcentajes():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE config_ceo SET p_pagos=%s, p_personal=%s, p_juridica=%s WHERE id=1", 
               (request.form.get('p_pagos'), request.form.get('p_personal'), request.form.get('p_juridica')))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('panel_ceo'))

# Carga de saldo manual
@app.route('/cargar_saldo', methods=['POST'])
def cargar_saldo():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET saldo = saldo + %s, depositado = depositado + %s WHERE telefono = %s", 
               (float(request.form.get('monto')), float(request.form.get('monto')), request.form.get('telefono')))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('panel_ceo'))

if __name__ == '__main__':
    # Puerto automático para Render
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
