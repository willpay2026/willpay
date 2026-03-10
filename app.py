from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- INICIALIZACIÓN (Obligatorio primero) ---
app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026'

# CONEXIÓN AL BÚNKER EN RENDER
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# --- RUTA RAÍZ (Para evitar el Error 404) ---
@app.route('/')
def index():
    # Redirigimos al panel CEO por ahora para que Render vea actividad
    return redirect(url_for('panel_ceo'))

# --- PANEL CEO (DASHBOARD) ---
@app.route('/panel_ceo')
def panel_ceo():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Capital Total
        cur.execute("SELECT SUM(saldo) as total FROM usuarios_willpay")
        res = cur.fetchone()
        capital = res['total'] if res and res['total'] else 0.00
        
        # Últimos 10 usuarios
        cur.execute("""
            SELECT cedula_rif, telefono, tipo_usuario 
            FROM usuarios_willpay 
            ORDER BY fecha_registro DESC LIMIT 10
        """)
        usuarios = cur.fetchall()
        
        cur.close()
        conn.close()
        return render_template('panel_ceo.html', capital=capital, usuarios=usuarios)
    except Exception as e:
        return f"Error en el búnker: {e}"

# --- ACTUALIZACIÓN DE RED ---
@app.route('/actualizar_tasas', methods=['POST'])
def actualizar_tasas():
    flash("Configuración de Red Actualizada")
    return redirect(url_for('panel_ceo'))

if __name__ == '__main__':
    # Render usa el puerto 10000 por defecto
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
