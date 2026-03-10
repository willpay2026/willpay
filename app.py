from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026'

# CONEXIÓN AL BÚNKER
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

@app.route('/')
def home():
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    return render_template('acceso.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/registro_proceso', methods=['POST'])
def registro_proceso():
    # Recolección de datos para el ADN Digital
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    telefono = request.form.get('telefono')
    tipo = request.form.get('tipo_usuario')
    actividad = request.form.get('actividad_oficio') or request.form.get('nombre_empresa') or "Usuario Natural"
    pin = request.form.get('pin')
    codigo_socio = request.form.get('codigo_socio')

    # Lógica de Comisiones
    tasa = 1.5
    es_socio = False
    if tipo == 'firma': tasa = 2.1
    if tipo == 'juridico': tasa = 3.1
    
    # Validación de los 5 socios exclusivos
    codigos_validos = ['willpay socio 1', 'willpay socio 2', 'willpay socio 3', 'willpay socio 4', 'willpay socio 5']
    if codigo_socio in codigos_validos:
        es_socio = True
        tasa = 1.0 # Beneficio de socio

    # Aquí se guardaría en la base de datos (simulado para el ticket)
    session['usuario_actual'] = {
        'nombre': nombre, 'cedula': cedula, 'tipo': tipo, 
        'tasa': tasa, 'es_socio': es_socio, 'id': 'WP-00001'
    }
    
    return redirect(url_for('ticket_bienvenida'))

@app.route('/ticket_bienvenida')
def ticket_bienvenida():
    u = session.get('usuario_actual')
    return render_template('ticket_bienvenida.html', u=u)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
