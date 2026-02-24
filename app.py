LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay | Emporio</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/@zxing/library@latest"></script>
    <style>
        :root { --oro: #D4AF37; --negro: #000; --gris: #121212; }
        body { background: var(--negro); color: white; font-family: 'Lexend', sans-serif; overflow-x: hidden; }
        
        /* PANTALLA DE BIENVENIDA (SPLASH) */
        #splash {
            position: fixed; top:0; left:0; width:100%; height:100%;
            background: var(--negro); z-index: 10000;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        .escudo-animado { width: 180px; animation: pulso 2s infinite; }
        @keyframes pulso { 0%{transform:scale(1);} 50%{transform:scale(1.1); filter: drop-shadow(0 0 15px var(--oro));} 100%{transform:scale(1);} }

        /* CONTENEDORES */
        .app-container { max-width: 500px; margin: auto; padding: 20px; display: none; }
        .card-will { background: var(--gris); border: 2px solid var(--oro); border-radius: 25px; padding: 25px; margin-top: 15px; }
        .btn-will { background: var(--oro); color: black; font-weight: bold; border-radius: 15px; padding: 12px; border: none; width: 100%; transition: 0.3s; }
        .btn-will:hover { transform: scale(1.02); opacity: 0.9; }
        .oro-text { color: var(--oro); }
        .saldo-v { font-size: 3.5rem; font-weight: bold; color: var(--oro); }
        
        /* INPUTS */
        .form-control { background: #1a1a1a !important; color: white !important; border: 1px solid #333 !important; border-radius: 12px; padding: 12px; }
        .form-control:focus { border-color: var(--oro) !important; box-shadow: none; }
    </style>
</head>
<body>

    <div id="splash">
        <img src="https://i.imgur.com/Tu8Rj9v.png" class="escudo-animado"> <h1 class="oro-text mt-4" style="letter-spacing: 5px;">WILL-PAY</h1>
        <p class="text-secondary small">Tecnología con corazón</p>
    </div>

    <div class="app-container" id="main_content" style="display: block;">
        <header class="text-center mb-4">
            <h2 class="oro-text mb-0">WILL-PAY</h2>
            <p class="small text-muted">Empoderando a Venezuela</p>
        </header>

        {% if not session.get('u') %}
            <div id="auth_section">
                <div class="card-will" id="login_box">
                    <h4 class="text-center mb-4">INICIAR SESIÓN</h4>
                    <form action="/login" method="POST">
                        <input name="t" placeholder="Teléfono" class="form-control mb-2" required>
                        <input name="p" type="password" placeholder="PIN de 4 dígitos" class="form-control mb-3" maxlength="4" required>
                        <button class="btn-will">ENTRAR AL SISTEMA</button>
                    </form>
                    <button class="btn btn-link w-100 mt-3 text-secondary" onclick="showRegister()">¿No tienes cuenta? Regístrate</button>
                </div>

                <div class="card-will" id="register_box" style="display:none;">
                    <h4 class="text-center mb-2">NUEVO REGISTRO</h4>
                    <p class="small text-center text-muted mb-4">Únete a la revolución económica</p>
                    <form action="/registro_completo" method="POST" enctype="multipart/form-data">
                        <select name="tipo_persona" class="form-control mb-2" required>
                            <option value="">Tipo de Persona</option>
                            <option value="natural">Persona Natural</option>
                            <option value="juridica">Persona Jurídica (Negocio)</option>
                        </select>
                        <select name="categoria" class="form-control mb-2" required>
                            <option value="">Categoría de Servicio</option>
                            <option value="transporte">🚐 Transporte / Taxi</option>
                            <option value="bodega">🛒 Bodega / Abasto</option>
                            <option value="delivery">📦 Delivery / Mensajería</option>
                            <option value="otros">💼 Otros Servicios</option>
                        </select>
                        <input name="nombre" placeholder="Nombre o Razón Social" class="form-control mb-2" required>
                        <input name="identificacion" placeholder="Cédula o RIF" class="form-control mb-2" required>
                        <input name="telefono" placeholder="Teléfono (Será tu Usuario)" class="form-control mb-2" required>
                        <input name="pin" type="password" placeholder="Crea un PIN de 4 dígitos" class="form-control mb-3" maxlength="4" required>
                        
                        <div class="row mb-3">
                            <div class="col-6"><label class="small text-muted">Foto ID</label><input type="file" class="form-control form-control-sm" required></div>
                            <div class="col-6"><label class="small text-muted">Selfie</label><input type="file" class="form-control form-control-sm" required></div>
                        </div>
                        
                        <button class="btn-will">SOLICITAR AFILIACIÓN</button>
                    </form>
                    <button class="btn btn-link w-100 mt-2 text-secondary" onclick="showLogin()">Ya tengo cuenta</button>
                </div>
            </div>
        {% else %}
            <div id="dashboard">
                <div class="card-will text-center">
                    <span class="text-secondary small">Saldo disponible</span>
                    <div class="saldo-v">Bs. {{ "%.2f"|format(u.saldo_bs) }}</div>
                    
                    <div class="row g-2 mt-2">
                        <div class="col-6"><button class="btn btn-outline-warning w-100" onclick="showRecarga()">RECARGAR</button></div>
                        <div class="col-6"><a href="/logout" class="btn btn-outline-danger w-100">SALIR</a></div>
                    </div>
                </div>

                <div class="btn-group w-100 mt-4 mb-4" style="height: 60px;">
                    <a href="/rol/pasajero" class="btn {{ 'btn-warning' if u.rol == 'pasajero' else 'btn-dark' }} d-flex align-items-center justify-content-center"><b>PAGAR</b></a>
                    <a href="/rol/prestador" class="btn {{ 'btn-warning' if u.rol == 'prestador' else 'btn-dark' }} d-flex align-items-center justify-content-center"><b>COBRAR</b></a>
                </div>

                <div class="card-will text-center" id="action_area">
                    {% if u.rol == 'pasajero' %}
                        <p class="oro-text">¿Cuánto vas a pagar?</p>
                        <input type="number" id="val_pago" class="form-control text-center mb-3" style="font-size:2rem; background:transparent !important;" placeholder="0.00" oninput="genQR()">
                        <div class="bg-white p-3 d-inline-block rounded shadow-lg"><img id="q_img" src="" style="width:200px;"></div>
                    {% else %}
                        <button class="btn-will py-4" onclick="scan()">📷 ABRIR ESCÁNER DE COBRO</button>
                        <video id="v" style="width:100%; display:none; border-radius:20px; margin-top:15px;"></video>
                    {% endif %}
                </div>
            </div>
        {% endif %}
    </div>

    <script>
        // Lógica del Splash
        setTimeout(() => {
            document.getElementById('splash').style.opacity = '0';
            setTimeout(() => { document.getElementById('splash').style.display = 'none'; }, 500);
        }, 3000);

        function showRegister() { document.getElementById('login_box').style.display='none'; document.getElementById('register_box').style.display='block'; }
        function showLogin() { document.getElementById('login_box').style.display='block'; document.getElementById('register_box').style.display='none'; }
        
        // ... (Aquí sigue el resto de tu JS de QR y Sonido que ya tenemos)
    </script>
</body>
</html>
'''
