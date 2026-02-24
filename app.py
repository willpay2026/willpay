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
    <title>Will-Pay | Inicio</title>
    <style>
        body { 
            background-color: #000; 
            margin: 0; 
            height: 100vh; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            font-family: 'Helvetica Neue', Arial, sans-serif;
            color: white;
            overflow: hidden;
        }

        /* CONTENEDOR DEL ESCUDO */
        .escudo-wrapper {
            animation: aparecer 2s ease-out;
            margin-bottom: 20px;
        }

        .escudo-img {
            width: 180px;
            height: auto;
            filter: drop-shadow(0 0 20px rgba(212, 175, 55, 0.4));
            animation: latido 3s infinite ease-in-out;
        }

        /* TIPOGRAFÍA WILL-PAY (DORADA) */
        .brand-name {
            font-size: 3rem;
            font-weight: bold;
            background: linear-gradient(to bottom, #FFD700, #B8860B);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            letter-spacing: -1px;
        }

        .slogan {
            color: #D4AF37;
            font-size: 1.1rem;
            margin-top: 5px;
            letter-spacing: 1px;
            font-weight: 300;
        }

        /* CRÉDITO INFERIOR (BLANCO) */
        .footer-credit {
            position: absolute;
            bottom: 40px;
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.8rem;
            letter-spacing: 1px;
            text-transform: none;
        }

        /* ANIMACIONES */
        @keyframes aparecer { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
        @keyframes latido { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
    </style>
</head>
<body>

    <div class="escudo-wrapper">
        <img src="/static/logo%20will-pay.jpg" class="escudo-img" alt="Will-Pay Shield" 
             onerror="this.src='https://via.placeholder.com/180/000000/D4AF37?text=ESCUDO'">
    </div>

    <h1 class="brand-name">Will-Pay</h1>
    <div class="slogan">Tu Billetera Digital de Confianza</div>

    <div class="footer-credit">Desarrollado por: Wildon C.A.</div>

</body>
</html>
''')

if __name__ == '__main__':
    app.run()
