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
        body, html { margin: 0; padding: 0; width: 100%; height: 100%; background-color: #000; overflow: hidden; }
        
        /* FASE 1: PRESENTACIÓN */
        #fase1-splash {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-color: #000; display: flex; justify-content: center; align-items: center;
            z-index: 9999; opacity: 1; transition: opacity 1.5s ease;
        }
        
        /* Ajuste para que la imagen ocupe la pantalla correctamente */
        #fase1-splash img { 
            width: 100vw; 
            height: 100vh; 
            object-fit: contain; /* Cambia a 'cover' si quieres que llene todo sin bordes negros */
        }

        /* FASE 2: REGISTRO */
        #fase2-registro {
            display: none; width: 100%; height: 100%;
            /* Usamos una ruta absoluta para la imagen de fondo */
            background: url('/static/cara2.jpg') no-repeat center center;
            background-size: cover; opacity: 0; transition: opacity 1.5s ease;
        }
        .capa-oscura { 
            width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); 
            display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; 
        }
    </style>
</head>
<body>
    <div id="fase1-splash">
        <img src="/static/cara1.jpg" onerror="this.src='https://via.placeholder.com/800x600?text=Error+Cargando+Cara1'" alt="Will-Pay Inicio">
    </div>

    <div id="fase2-registro">
        <div class="capa-oscura">
            <h1 style="color: #D4AF37; font-size: 3rem;">WILL-PAY</h1>
            <p style="letter-spacing: 5px;">VENEZUELA</p>
            <div style="margin-top: 20px; border: 1px solid #D4AF37; padding: 10px;">
                Fase 2: Registro en construcción...
            </div>
        </div>
    </div>

    <script>
        window.onload = function() {
            // Esperamos 5 segundos antes de atenuar
            setTimeout(() => {
                const splash = document.getElementById('fase1-splash');
                splash.style.opacity = '0';
                
                setTimeout(() => {
                    splash.style.display = 'none';
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
