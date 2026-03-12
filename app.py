from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

def get_db():
    # Conexión automática a la base de datos de Render
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# ==========================================
# >>> RUTAS DE NAVEGACIÓN RECUPERADAS <<<
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
    
    # Buscamos la configuración (porcentajes, etc.)
    cur.execute("SELECT * FROM config_ceo WHERE id = 1")
    config = cur.fetchone()
    
    # Calculamos el capital total en el búnker
    cur.execute("SELECT SUM(saldo) as total, SUM(depositado) as dep FROM users")
    res = cur.fetchone()
    
    # Mostramos los últimos usuarios
    cur.execute("SELECT id, nombre, telefono, rol, cedula FROM users ORDER BY id DESC LIMIT 10")
    usuarios = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('panel_ceo.html', 
                           config=config, 
                           capital=res['total'] or 0.0, 
                           depositado=res['dep'] or 0.0, 
                           usuarios=usuarios)

if __name__ == '__main__':
    # Puerto dinámico para que Render no falle
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
