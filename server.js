const express = require('express');
const app = express();
const path = require('path');

app.use(express.json());
// Esto permite que el servidor use las carpetas 'static' o 'public' que ya tienes
app.use(express.static(path.join(__dirname, 'static')));

// 1. PÁGINA DE ENTRADA (EL COHETE 🚀)
app.get('/', (req, res) => {
    res.send(`
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Will-Pay | El Legado</title>
            <style>
                body { background-color: #000; color: #fff; font-family: sans-serif; text-align: center; padding: 20px; }
                .card { background: #1a1a1a; border: 2px solid #ffcf40; border-radius: 15px; padding: 20px; margin-top: 20px; }
                .btn { background: #ffcf40; color: #000; border: none; padding: 15px 30px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; margin-top: 10px; }
                img { max-width: 150px; margin-bottom: 10px; }
            </style>
        </head>
        <body>
            <img src="https://raw.githubusercontent.com/willpay2026/willpay/main/static/logonuevo.jpg" alt="Will-Pay Logo">
            <h1>🚀 Will-Pay Global 2026</h1>
            <p>El legado para <b>Wilyanny Donquiz</b> está en línea.</p>
            
            <div class="card">
                <h3>Datos para Recarga:</h3>
                <p><b>Banco:</b> Banesco</p>
                <p><b>Pago Móvil:</b> 04126602555</p>
                <p><b>C.I:</b> 13496133</p>
                <p style="font-size: 0.8rem; color: #ffcf40;">Wilfredo aprobará tu saldo al verificar el capture.</p>
            </div>

            <button class="btn" onclick="location.href='/registro'">REGISTRAR MI ADN DIGITAL</button>
            <p><a href="/login" style="color: #888; text-decoration: none;">¿Ya tienes cuenta? Entrar a mi Bóveda</a></p>
        </body>
        </html>
    `);
});

// 2. CORRECCIÓN DEL ERROR: RUTA DE REGISTRO
app.get('/registro', (req, res) => {
    // Esto busca el archivo en tu carpeta 'static'
    res.sendFile(path.join(__dirname, 'static', 'registro.html'));
});

// 3. RUTA PARA EL LOGIN / BÓVEDA
app.get('/login', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log('El Búnker de Wilfredo está rugiendo en el puerto ' + PORT);
});
