from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026'

# CONEXIÓN AL BÚNKER EN RENDER
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# 1. EL COMIENZO: Splash Screen (Logo solo por 4 seg)
@app.route('/')
def home():
    return render_template('splash.html')

# 2. EL ACCESO: Panel de Login elegante
@app.route('/acceso')
def acceso():
    return render_template('acceso.html')

# 3. EL REGISTRO: Expediente Digital (KYC)
@app.route('/registro')
def registro():
    return render_template('registro.html')

# 4. TU MANDO: Panel Maestro del CEO
@app.route('/panel_maestro')
def panel_maestro():
    # Aquí cargaremos el Capital Total en Búnker después
    u = {'saldo_total': '0.00', 'ganancias_ceo': '0.00'}
    return render_template('panel_maestro.html', u=u, movimientos=[], libres=5)

# 5. BILLETERA: Dashboard del Usuario
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    # Puerto dinámico para que Render no dé error 502
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
