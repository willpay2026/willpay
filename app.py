from flask import Flask, render_template_string, os

app = Flask(__name__)

# --- EL MOTOR DE LAS 3 FASES ---
# Nota: La Fase 1 usa cara1.jpg y la Fase 2 usa cara2.jpg
LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay | Legado</title>
    <style>
        body, html {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            background-color: #000;
            overflow: hidden;
            font-family: sans-serif;
        }

        /* FASE 1: PRESENTACIÓN PURA */
        #fase1-splash {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            transition: opacity 1.5s ease; /* Efecto de atenuado */
        }

        #fase1-splash img {
            width: 100%;
            height: 100%;
            object-fit: contain; /* MANTIENE LA IMAGEN COMPLETA SIN ALTERAR */
        }

        /* FASE 2: REGISTRO (FONDO CARA2) */
        #fase2-registro {
            display: none;
            width: 100%;
            height: 100%;
            background: url('/static/cara2.jpg') no-repeat center center;
            background-size: cover;
            opacity: 0;
            transition: opacity 1.5s ease;
        }

        .capa-oscura {
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5); /* Para que los botones resalten luego */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
        }
    </style>
</head>
<body>

    <div id="fase1-splash">
        <img src="/static/cara1.jpg" alt="Will-Pay Inicio">
    </div>

    <div id="fase2-registro">
        <div class="capa-oscura">
            <h2 style="color: #D4AF37;">WILL-PAY</h2>
            <p>Fase de Registro en preparación...</p>
        </div>
    </div>

    <script>
        window.onload = function() {
            const splash = document.getElementById('fase1-splash');
            const registro = document.getElementById('fase2-registro');

            // 1. Mostrar cara1.jpg por 5 segundos
            setTimeout(() => {
                // 2. Atenuar imagen (Fade Out)
                splash.style.opacity = '0';
                
                // 3. Quitar Fase 1 y mostrar Fase 2 (cara2.jpg)
                setTimeout(() => {
                    splash.style.display = 'none';
                    registro.style.display = 'block';
                    setTimeout(() => {
                        registro.style.opacity = '1';
                    }, 50);
                }, 1500); 

            }, 5000); // 5 segundos de imagen pura
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(LAYOUT)

if __name__ == '__main__':
    # Configuración para Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
