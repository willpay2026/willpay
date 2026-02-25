import os
from flask import Flask, render_template_string

app = Flask(__name__)

# HTML Simplificado al máximo
LAYOUT = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body, html { margin: 0; padding: 0; width: 100%; height: 100%; background: black; overflow: hidden; }
        
        /* FASE 1 */
        #fase1 {
            position: fixed; width: 100%; height: 100%;
            display: flex; justify-content: center; align-items: center;
            z-index: 10; transition: opacity 2s;
        }
        #fase1 img { width: 100%; height: 100%; object-fit: contain; }

        /* FASE 2 */
        #fase2 {
            display: none; width: 100%; height: 100%;
            background: url('/static/cara2.jpg') no-repeat center center;
            background-size: cover; opacity: 0; transition: opacity 2s;
        }
    </style>
</head>
<body>
    <div id="fase1">
        <img src="/static/cara1.jpg">
    </div>

    <div id="fase2">
        <h1 style="color: gold; text-align: center; margin-top: 50px;">FASE 2: REGISTRO</h1>
    </div>

    <script>
        setTimeout(() => {
            document.getElementById('fase1').style.opacity = '0';
            setTimeout(() => {
                document.getElementById('fase1').style.display = 'none';
                let f2 = document.getElementById('fase2');
                f2.style.display = 'block';
                setTimeout(() => { f2.style.opacity = '1'; }, 50);
            }, 2000);
        }, 5000);
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
