from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory
import csv, os, datetime

# --- CONFIGURACIÓN DE LA APP ---
app = Flask(__name__)
app.secret_key = 'willpay_2026_key_secure'

# Nombres de archivos de base de datos
DB_USUARIOS = 'usuarios_v1.csv'
DB_RECARGAS = 'recargas_v1.csv'
DB_HISTORIAL = 'historial_v1.csv'

def inicializar_db():
    if not os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            writer.writerow(["admin", "Admin Will-Pay", "V-000", "0.0", "prestador", "1234"])
    
    if not os.path.exists(DB_RECARGAS):
        with open(DB_RECARGAS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID_User", "Referencia", "Monto_Bs", "Status"])
            
    if not os.path.exists(DB_HISTORIAL):
        with open(DB_HISTORIAL, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Emisor", "Receptor", "Monto", "Concepto"])

def obtener_usuarios():
    usuarios = {}
    if os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                usuarios[row['ID']] = row
    return usuarios

def registrar_movimiento(emisor, receptor, monto, concepto):
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DB_HISTORIAL, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([fecha, emisor, receptor, monto, concepto])

@app.route('/logo')
def logo():
    return send_from_directory(os.getcwd(), 'logo will-pay.jpg')

# --- INTERFAZ HTML ---
HTML_LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/@zxing/library@latest"></script>
    <style>
        body { background-color: #000; color: #fff; font-family: sans-serif; }
        .will-container { max-width: 450px; margin: 20px auto; padding: 20px; text-align: center; }
        .logo-img { width: 180px; margin-bottom: 20px; border-radius: 10px; }
        .main-card { 
            background: #111; border: 2px solid #d4af37; border-radius: 25px; 
            padding: 30px; box-shadow: 0 0 15px rgba(212, 175, 55, 0.3);
        }
        .btn-gold { background-color: #d4af37; color: #000; font-weight: bold; border-radius: 12px; padding: 12px; width: 100%; border:none; }
        .btn-outline-gold { background: transparent; color: #d4af37; border: 1px solid #d4af37; border-radius: 12px; padding: 10px; width: 100%; text-decoration: none; display: block; }
        .saldo-display { color: #d4af37; font-size: 2.5rem; font-weight: bold; margin: 10px 0; }
        .monto-selector { background: transparent; border: 1px solid #444; border-radius: 15px; color: #d4af37; font-size: 2rem; padding: 10px; width: 100%; margin: 15px 0; }
        .historial-item { background: #1a1a1a; border-left: 4px solid #d4af37; padding: 10px; margin-bottom: 10px; border-radius: 8px; text-align: left; }
    </style>
</head>
<body>
    <div class="will-container">
        <img src="/logo" class="logo-img" onerror="this.src='https://via.placeholder.com/180x80/000/d4af37?text=Will-Pay'">
        
        {% if vista == 'landing' %}
        <div class="main-card">
            <h2 style="color: #d4af37; font-weight: bold;">WILL-PAY</h2>
            <p class="text-secondary small">Tu Billetera Digital</p>
            <div class="mt-4">
                <a href="/login_view" class="btn-gold d-block mb-3 py-2 text-decoration-none" style="color:#000">INICIAR SESIÓN</a>
                <a href="/registro_view" class="btn-outline-gold">REGISTRARSE</a>
            </div>
        </div>

        {% elif vista == 'login' %}
        <div class="main-card">
            <h4 class="mb-4" style="color: #d4af37;">Ingresar</h4>
            <form action="/procesar_login" method="POST">
                <input type="text" name="telefono" class="form-control bg-dark text-white border-secondary mb-3" placeholder="Teléfono" required>
                <input type="password" name="pin" class="form-control bg-dark text-white border-secondary mb-4" placeholder="PIN" required>
                <button type="submit" class="btn-gold py-2">ENTRAR</button>
            </form>
            <a href="/" class="text-secondary small d-block mt-3">Volver</a>
        </div>

        {% elif vista == 'registro' %}
        <div class="main-card">
            <h4 class="mb-4" style="color: #d4af37;">Nuevo Usuario</h4>
            <form action="/procesar_registro" method="POST">
                <input type="text" name="nombre" class="form-control bg-dark text-white border-secondary mb-2" placeholder="Nombre" required>
                <input type="text" name="telefono" class="form-control bg-dark text-white border-secondary mb-2" placeholder="Teléfono" required>
                <input type="password" name="pin" class="form-control bg-dark text-white border-secondary mb-4" placeholder="PIN 4 dígitos" maxlength="4" required>
                <button type="submit" class="btn-gold py-2">CREAR CUENTA</button>
            </form>
            <a href="/" class="text-secondary small d-block mt-3">Volver</a>
        </div>

        {% elif vista == 'main' %}
        <div class="main-card">
            {% if usuario.ID == 'admin' %}<div class="badge bg-danger mb-3">MODO ADMINISTRADOR</div>{% endif %}
            <p class="text-secondary mb-0">Saldo Disponible</p>
            <div class="saldo-display">Bs. {{ "%.2f"|format(usuario.Saldo_Bs|float) }}</div>
            
            <div class="d-flex gap-2 mb-3">
                <button class="btn btn-sm btn-outline-warning w-100" onclick="document.getElementById('div_recarga').style.display='block'">RECARGAR</button>
                {% if usuario.ID == 'admin' %}<a href="/pantalla_admin" class="btn btn-sm btn-danger w-100">REPORTES</a>{% endif %}
            </div>

            <div id="div_recarga" style="display:none;" class="bg-dark p-3 rounded border border-warning mb-3">
                <form action="/reportar_pago" method="POST">
                    <input type="text" name="ref" class="form-control form-control-sm mb-2" placeholder="Referencia" required>
                    <input type="number" name="monto" class="form-control form-control-sm mb-2" placeholder="Monto" required>
                    <button class="btn btn-success btn-sm w-100">Enviar</button>
                </form>
            </div>

            <div class="btn-group w-100 mb-4">
                <a href="/set_rol/pasajero" class="btn btn-sm {{ 'btn-warning' if usuario.Rol == 'pasajero' else 'btn-dark' }}">PAGAR</a>
                <a href="/set_rol/prestador" class="btn btn-sm {{ 'btn-warning' if usuario.Rol == 'prestador' else 'btn-dark' }}">COBRAR</a>
            </div>

            {% if usuario.Rol == 'pasajero' %}
                <div class="monto-selector" id="val_monto">0.00</div>
                <input type="range" class="form-range mb-4" min="0" max="500" step="1" value="0" oninput="actualizarQR(this.value)">
                <div class="bg-white p-3 d-inline-block rounded-4">
                    <img id="img_qr" src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=WILLPAY|{{usuario.ID}}|0">
                </div>
            {% else %}
                <div id="scanner_container" style="display:none;"><video id="webcam_video" style="width: 100%; border-radius: 15px;"></video></div>
                <button id="btn_scan" class="btn-gold py-3" onclick="iniciarEscaneo()">📷 COBRAR PASAJE</button>
            {% endif %}

            <h6 class="text-start mt-4" style="color: #d4af37;">Historial</h6>
            <div style="max-height: 200px; overflow-y: auto;">
                {% for item in historial %}
                <div class="historial-item">
                    <div class="d-flex justify-content-between small">
                        <span>{{ item.Concepto }}</span>
                        <b class="{{ 'text-success' if item.Receptor == usuario.ID else 'text-danger' }}">Bs. {{ item.Monto }}</b>
