from flask import Flask, render_template_string, request, redirect, session, send_from_directory, jsonify
import csv, os, datetime

app = Flask(__name__)
app.secret_key = 'willpay_global_gold_2026'

# --- CONFIGURACIÓN DE ARCHIVOS (Usando tus versiones v21) ---
DB_USUARIOS = 'db_usuarios_v21.csv'
DB_RECARGAS = 'db_recargas_v21.csv'
DB_HISTORIAL = 'db_historial_v21.csv'
COMISION = 0.01  # Tu 1% estratégico

def inicializar_db():
    if not os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN", "Status_KYC", "Tipo_Servicio"])
            writer.writerow(["admin", "Admin Central", "0", "0.00", "admin", "1234", "ACTIVO", "SISTEMA"])
    
    if not os.path.exists(DB_HISTORIAL):
        with open(DB_HISTORIAL, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Emisor", "Receptor", "Monto", "Concepto", "Comision_WillPay"])

def obtener_usuarios():
    data = {}
    if not os.path.exists(DB_USUARIOS): inicializar_db()
    try:
        with open(DB_USUARIOS, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('ID'): data[row['ID']] = row
    except: pass
    return data

def registrar_movimiento(emisor, receptor, monto, concepto, comision=0):
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DB_HISTORIAL, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([fecha, emisor, receptor, monto, concepto, comision])

@app.route('/logo')
def logo(): 
    return send_from_directory(os.getcwd(), 'logo will-pay.jpg') if os.path.exists('logo will-pay.jpg') else "Logo"

HTML_APP = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #000; color: white; text-align: center; font-family: sans-serif; }
        .will-container { border: 2px solid #D4AF37; border-radius: 30px; padding: 25px; margin: 20px auto; max-width: 400px; background: #0a0a0a; box-shadow: 0 0 15px rgba(212, 175, 55, 0.2); }
        .gold { color: #D4AF37; font-weight: bold; }
        .btn-will { background: #D4AF37; color: #000; font-weight: bold; border-radius: 12px; border: none; padding: 12px; width: 100%; text-decoration: none; display: inline-block; margin-top: 10px; }
        .form-control { background: #111; border: 1px solid #333; color: white; margin-bottom: 15px; border-radius: 10px; }
        .historial-item { border-bottom: 1px solid #222; padding: 10px 0; text-align: left; font-size: 0.8rem; }
    </style>
</head>
<body>
    <div class="container py-4">
        <img src="/logo" style="width: 120px; margin-bottom: 15px;">
        
        {% if vista == 'inicio' %}
        <div class="will-container">
            <h3 class="gold mb-4">WILL-PAY</h3>
            <a href="/vista_login" class="btn-will">INICIAR SESIÓN</a>
            <a href="/vista_registro" class="btn-will" style="background:transparent; color:#D4AF37; border:1px solid #D4AF37;">REGISTRARSE</a>
        </div>

        {% elif vista == 'main' %}
        <div class="will-container">
            <span class="badge border border-warning text-warning mb-2">{{ usuario.Tipo_Servicio }}</span>
            <p class="mb-1 small text-secondary">Saldo Disponible</p>
            <h2 class="gold">Bs. {{ usuario.Saldo_Bs }}</h2>
            <hr style="border-color: #333;">
            
            {% if usuario.ID == 'admin' %}
            <h5 class="gold">PANEL MAESTRO</h5>
            <p class="small">Aquí caen tus ganancias del 1%</p>
            {% else %}
            <form action="/pagar" method="POST">
                <input type="text" name="receptor" class="form-control" placeholder="ID del Chofer/Comercio">
                <input type="number" step="0.01" name="monto" class="form-control" placeholder="Monto Bs.">
                <button class="btn-will">PAGAR AHORA</button>
            </form>
            {% endif %}
            
            <a href="/logout" class="text-danger small d-block mt-4 text-decoration-none">Cerrar Sesión</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if 'u' in session:
        u = obtener_usuarios().get(session['u'])
        if u: return render_template_string(HTML_APP, vista='main', usuario=u)
    return render_template_string(HTML_APP, vista='inicio')

@app.route('/vista_login')
def vista_login(): return render_template_string(HTML_APP, vista='inicio', vista_sub='login') # Simplificado para el ejemplo

@app.route('/login', methods=['POST'])
def login():
    uid, pin = request.form.get('id'), request.form.get('pin')
    users = obtener_usuarios()
    if uid in users and users[uid]['PIN'] == pin:
        session['u'] = uid
    return redirect('/')

@app.route('/pagar', methods=['POST'])
def pagar():
    emisor_id = session.get('u')
    receptor_id = request.form.get('receptor')
    monto = float(request.form.get('monto'))
    
    users = obtener_usuarios()
    
    if emisor_id in users and receptor_id in users and float(users[emisor_id]['Saldo_Bs']) >= monto:
        # CÁLCULO ESTRATÉGICO
        ganancia_will = monto * COMISION
        pago_final_receptor = monto - ganancia_will
        
        # ACTUALIZAR SALDOS
        users[emisor_id]['Saldo_Bs'] = str(round(float(users[emisor_id]['Saldo_Bs']) - monto, 2))
        users[receptor_id]['Saldo_Bs'] = str(round(float(users[receptor_id]['Saldo_Bs']) + pago_final_receptor, 2))
        users['admin']['Saldo_Bs'] = str(round(float(users['admin']['Saldo_Bs']) + ganancia_will, 2))
        
        # GUARDAR EN CSV
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN", "Status_KYC", "Tipo_Servicio"])
            writer.writeheader()
            for u in users.values(): writer.writerow(u)
        
        registrar_movimiento(emisor_id, receptor_id, monto, "Pago Pasaje/Servicio", ganancia_will)
        
    return redirect('/')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    inicializar_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
