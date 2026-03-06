from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026'

# TU CONEXIÓN AL BÚNKER
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/acceso')
def acceso():
    return render_template('acceso.html')

@app.route('/panel_maestro')
def panel_maestro():
    # Solo tú entras con tu cédula guardada en los recuerdos
    # (Simulación de seguridad para Wilfredo)
    u = {'saldo_total': 'Cargando...', 'ganancias_ceo': '0.00'}
    return render_template('panel_maestro.html', u=u, movimientos=[], libres=5)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
