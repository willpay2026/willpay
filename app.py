from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_legado_final_2026'
DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL, sslmode='require')

@app.route('/')
def index(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre', '').upper()
    cedula = request.form.get('cedula', '').strip()
    telefono = request.form.get('telefono', '').strip()
    pin = request.form.get('pin', '').strip()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Registramos como PENDIENTE para que Wilfredo autorice
        cur.execute("""INSERT INTO usuarios (nombre, cedula, telefono, pin, rol, saldo_bs, saldo_wpc, saldo_usd, ganancia_neta) 
                     VALUES (%s, %s, %s, %s, 'PENDIENTE', 0.0, 0.0, 0.0, 0.0)""", 
                     (nombre, cedula, telefono, pin))
        conn.commit()
        return redirect(url_for('acceso'))
    except Exception as e:
        return f"<h1>⚠️ Error</h1><p>{e}</p><a href='/registro'>Volver</a>"
    finally:
        cur.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    dato = request.form.get('telefono_login', '').strip()
    pin = request.form.get('pin_login', '').strip()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE (cedula=%s OR telefono=%s) AND pin=%s", (dato, dato, pin))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))
    return "<h1>❌ Datos Incorrectos</h1><a href='/acceso'>Volver</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    
    # 🦅 OJO DE ÁGUILA: Filtramos por 'estado' para evitar el error previo
    cur.execute("SELECT * FROM recargas WHERE estado = 'PENDIENTE' ORDER BY id DESC")
    recargas_pendientes = cur.fetchall()
    
    # También traemos usuarios pendientes de aprobación
    cur.execute("SELECT * FROM usuarios WHERE rol = 'PENDIENTE' ORDER BY id DESC")
    usuarios_pendientes = cur.fetchall()
    
    cur.close()
    conn.close()
    if u['cedula'] == '13496133':
        return render_template('ceo_panel.html', u=u, recargas=recargas_pendientes, usuarios=usuarios_pendientes)
    return render_template('dashboard.html', u=u)

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    monto = request.form.get('monto')
    referencia = request.form.get('referencia') # El "Ojo de Águila" valida que sea ÚNICA
    telf_destino = request.form.get('telf_destino', '') # Por si es para un familiar
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO recargas (user_id, monto, referencia, telf_destino, estado) 
                     VALUES (%s, %s, %s, %s, 'PENDIENTE')""", 
                     (session['user_id'], monto, referencia, telf_destino))
        conn.commit()
        return "<h1>✅ Recarga en Verificación</h1><p>Wilfredo está revisando tu pago.</p><a href='/dashboard'>Volver</a>"
    except:
        return "<h1>⚠️ Error</h1><p>Esa referencia ya fue usada. No intentes estafar al sistema.</p><a href='/dashboard'>Volver</a>"
    finally:
        cur.close()
        conn.close()

@app.route('/aprobar_recarga/<int:id_recarga>')
def aprobar_recarga(id_recarga):
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Buscamos la recarga
    cur.execute("SELECT * FROM recargas WHERE id = %s", (id_recarga,))
    r = cur.fetchone()
    
    if r:
        # 1. Marcamos como APROBADA
        cur.execute("UPDATE recargas SET estado = 'APROBADA' WHERE id = %s", (id_recarga,))
        # 2. Sumamos el saldo al usuario (o al teléfono destino si existe)
        target = r['telf_destino'] if r['telf_destino'] else r['user_id']
        if r['telf_destino']:
            cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE telefono = %s", (r['monto'], r['telf_destino']))
        else:
            cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (r['monto'], r['user_id']))
            
        conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/instalar')
def instalar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios, recargas CASCADE")
    # Tabla Usuarios
    cur.execute("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, cedula TEXT UNIQUE, 
        telefono TEXT, pin TEXT, rol TEXT, 
        saldo_bs FLOAT DEFAULT 0.0, saldo_wpc FLOAT DEFAULT 0.0, 
        saldo_usd FLOAT DEFAULT 0.0, ganancia_neta FLOAT DEFAULT 0.0)""")
    
    # Tabla Recargas con columna 'estado' para coincidir con el HINT del log
    cur.execute("""CREATE TABLE recargas (
        id SERIAL PRIMARY KEY, user_id INTEGER, monto FLOAT, 
        referencia TEXT UNIQUE, telf_destino TEXT, estado TEXT DEFAULT 'PENDIENTE')""")
    
    # Insertamos al CEO (Wilfredo)
    cur.execute("""INSERT INTO usuarios (nombre, cedula, telefono, pin, rol, saldo_bs, saldo_wpc, saldo_usd, ganancia_neta) 
                VALUES ('WILFREDO DONQUIZ', '13496133', '04126602555', '1234', 'CEO', 100.0, 50.0, 10.0, 5.0)""")
    
    # Reservamos los 5 espacios para partners
    for i in range(1, 6):
        cur.execute("INSERT INTO usuarios (nombre, cedula, pin, rol) VALUES (%s, %s, '0000', 'SOCIO_RESERVADO')", 
                    (f"SOCIO RESERVADO {i}", f"PARTNER-{i}"))
        
    conn.commit()
    cur.close()
    conn.close()
    return "<h1>🏛️ Will-Pay Sincronizado</h1><p>Sistema Ojo de Águila activo.</p>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
