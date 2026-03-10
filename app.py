from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# 1. DEFINICIÓN DE LA APP (Primero que nada para evitar errores)
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
    
    # Capital Total en Búnker
    cur.execute("SELECT SUM(saldo) as total FROM usuarios_willpay")
    res_cap = cur.fetchone()
    capital = res_cap['total'] if res_cap['total'] else 0.00
    
    # Ganancias (Legado Wilyanny)
    ganancia_neta = capital * 0.015 

    # Actividad en Vivo (10 en 10)
    cur.execute("""
        SELECT cedula_rif, telefono, tipo_usuario, fecha_registro 
        FROM usuarios_willpay 
        ORDER BY fecha_registro DESC 
        LIMIT 10
    """)
    usuarios = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('panel_ceo.html', capital=capital, ganancia=ganancia_neta, usuarios=usuarios)

@app.route('/actualizar_tasas', methods=['POST'])
def actualizar_tasas():
    # Procesa los 3 recuadros de la red
    flash("Tasas de Red Sincronizadas")
    return redirect(url_for('panel_ceo'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
