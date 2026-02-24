from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay | Emporio Digital</title>
    <style>
        body, html { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #000; }

        /* 1. PANTALLA DE PRESENTACIÓN (SPLASH) */
        #splash-screen {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: #000;
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            z-index: 9999;
            transition: opacity 1s ease-out, visibility 1s;
        }

        .escudo-img {
            width: 200px;
            filter: drop-shadow(0 0 15px rgba(212, 175, 55, 0.5));
            animation: latido 3s infinite ease-in-out;
        }

        .brand-name {
            font-size: 3.5rem;
            font-weight: bold;
            background: linear-gradient(to bottom, #FFD700, #B8860B);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 10px 0 0 0;
        }

        .slogan { color: #D4AF37; font-size: 1.2rem; font-weight: 300; letter-spacing: 1px; }

        .footer-credit {
            position: absolute; bottom: 30px;
            color: rgba(255, 255, 255, 0.5); font-size: 0.8rem;
        }

        /* 2. PANEL DE CONTROL (BILLETERA) - OCULTO AL INICIO */
        #main-content {
            opacity: 0;
            transition: opacity 1.5s ease-in;
            padding: 20px;
            color: white;
            text-align: center;
        }

        .wallet-card {
            background: linear-gradient(135deg, #1a1a1a 0%, #000 100%);
            border: 1px solid #D4AF37;
            border-radius: 15px;
            padding: 30px;
            margin-top: 50px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }

        .balance-label { color: #D4AF37; text-transform: uppercase; font-size: 0.9rem; }
        .balance-amount { font-size: 2.5rem; font-weight: bold; margin: 10px 0; }

        /* ANIMACIONES */
        @keyframes latido { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
        
        /* CLASE PARA OCULTAR EL SPLASH */
        .fade-out { opacity: 0; visibility: hidden; }
        .fade-in { opacity: 1 !important; }
    </style>
</head>
<body>

    <div id="splash-screen">
        <img src="/static/logo%20will-pay.jpg" class="escudo-img" alt="Will-Pay" 
             onerror="this.src='https://via.placeholder.com/200/000000/D4AF37?text=WP'">
        <h1 class="brand-name">Will-Pay</h1>
        <div class="slogan">Tu Billetera Digital de Confianza</div>
        <div class="footer-credit">Desarrollado por: Wildon C.A.</div>
    </div>

    <div id="main-content">
        <div style="margin-top: 20px;">
            <h2 style="color: #D4AF37;">Panel de Control</h2>
            <p>Bienvenido al futuro de los pagos en Venezuela</p>
        </div>

        <div class="wallet-card">
            <div class="balance-label">Saldo Disponible</div>
            <div class="balance-amount">$ 1,250.00</div>
            <hr style="border: 0.5px solid #333; margin: 20px 0;">
            <div style="display: flex; justify-content: space-around;">
                <button style="background: #D4AF37; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold;">Recargar</button>
                <button style="background: transparent; border: 1px solid #D4AF37; color: white; padding: 10px 20px; border-radius: 5px;">Transferir</button>
            </div>
        </div>
    </div>

    <script>
        // ESTA ES LA MAGIA: Espera 5 segundos y cambia de pantalla
        setTimeout(function() {
            document.getElementById('splash-screen').classList.add('fade-out');
            document.getElementById('main-content').classList.add('fade-in');
        }, 5000); // 5000 milisegundos = 5 segundos
    </script>

</body>
</html>
''')

if __name__ == '__main__':
    app.run()
