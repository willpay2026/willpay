from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026'

# CONEXIÓN AL BÚNKER (Render URL)
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

# Carpeta para el ADN Digital (Fotos)
UPLOAD_FOLDER = 'static/adn_digital'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
    # 1. Recolección de datos
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    telefono = request.form.get('telefono')
    tipo = request.form.get('tipo_usuario')
    actividad = request.form.get('actividad_oficio') or request.form.get('nombre_empresa') or "Usuario Natural"
    pin = request.form.get('pin')
    codigo_socio = request.form.get('codigo_socio')

    # 2. Manejo de Fotos (ADN Digital)
    f_cedula = request.files.get('foto_cedula')
    f_selfie = request.files.get('foto_selfie')
    
    path_cedula = ""
    path_selfie = ""

    if f_cedula and f_selfie:
        filename_c = secure_filename(f"{cedula}_cedula.png")
        filename_s = secure_filename(f"{cedula}_selfie.png")
        path_cedula = os.path.join(UPLOAD_FOLDER, filename_c)
        path_selfie = os.path.join(UPLOAD_FOLDER, filename_s)
        f_cedula.save(path_cedula)
        f_selfie.save(path_selfie)

    # 3. Lógica de Comisiones y Socios
    tasa = 1.5
    es_socio = False
    codigos_validos = ['willpay socio 1', 'willpay socio 2', 'willpay socio 3', 'willpay socio 4', 'willpay socio 5']
    
    if codigo_socio in codigos_validos:
        es_socio = True
        tasa = 1.0  # Tasa preferencial socio
    elif tipo == 'firma':
        tasa = 2.1
    elif tipo == 'juridico':
        tasa = 3.1

    # 4. Guardar en el Búnker de PostgreSQL
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO usuarios_willpay 
            (nombre_completo, cedula_rif, telefono, tipo_usuario, actividad_economica, comision_asignada, pin_seguridad, ruta_cedula, ruta_selfie, es_socio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (nombre, cedula, telefono, tipo, actividad, tasa, pin, path_cedula, path_selfie, es_socio))
        
        nuevo_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
