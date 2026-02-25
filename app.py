import os
from flask import Flask, render_template_string

app = Flask(__name__)

# --- CONFIGURACIÓN DE LAS 3 FASES ---
LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay | Legado</title>
    <style>
        body, html { margin: 0; padding: 0; width: 100%; height: 100%; background-color: #000; overflow: hidden; font-family: sans-serif; }
        
        /* FASE 1: PRESENTACIÓN */
        #fase1-splash {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-color: #000; display: flex; justify-content: center; align-items: center;
            z-index: 9999; transition: opacity 1.5s ease;
        }
        #fase1-splash img { width: 100%; height: 100%; object-fit: contain; }

        /* FASE 2: REGISTRO */
        #fase2-registro {
            display: none; width: 100%; height: 100%;
            background: url('/static/cara2.jpg') no-repeat center center;
            background-size: cover; opacity: 0; transition: opacity 1.5s ease;
        }
        .capa-oscura { 
            width: 100%; height: 100%; background: rgba(0, 0, 0, 0.6); 
            display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; 
        }
    </style>
</head>
<body>
    <div id="fase1-splash">
        <img src="/static/cara1.jpg" alt="Will-Pay Inicio">
    </div>

    <div id="fase2-registro">
        <div class="capa-oscura">
            <h1 style="color: #D4AF37;">WILL-PAY</h1>
            <p>CONECTANDO TU MUNDO</p>
            <small>Fase 2: Registro en construcción...</small>
        </div>
    </div>

    <script>
        window.onload = function() {
            setTimeout(() => {
                document.getElementById('fase1-splash').style.opacity = '0';
                setTimeout(() => {
                    document.getElementById('fase1-splash').style.display = 'none';
                    const f2 = document.getElementById('fase2-registro');
                    f2.style.display = 'block';
                    setTimeout(() => { f2.style.opacity = '1'; }, 50);
                }, 1500);
            }, 5000); 
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(LAYOUT)

if __name__ == '__main__':
    # Esto es vital para que Render no de error 503
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
