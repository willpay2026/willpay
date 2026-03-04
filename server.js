const express = require('express');
const app = express();

app.use(express.json());

// --- DATOS DE WILFREDO DONQUIZ ---
const misDatosDePago = {
    banco: "Banesco",
    telefono: "04126602555",
    id: "13496133",
    mensaje: "Will-Pay: El legado de Wilyanny Donquiz"
};

let capturasUsadas = []; // El búnker que bloquea estafas

// Página principal que verá la gente
app.get('/', (req, res) => {
    res.send(`
        <div style="text-align:center; padding:50px; font-family:Arial;">
            <h1>🚀 Will-Pay Global 2026</h1>
            <p>Sistema Revolucionario de Pagos en Venezuela</p>
            <div style="background:#f4f4f4; padding:20px; border-radius:10px; display:inline-block;">
                <h3>Para recargar saldo envíe Pago Móvil:</h3>
                <p><b>Banco:</b> ${misDatosDePago.banco}</p>
                <p><b>Teléfono:</b> ${misDatosDePago.telefono}</p>
                <p><b>Cédula:</b> ${misDatosDePago.id}</p>
            </div>
            <p style="margin-top:20px;"><i>Wilfredo Donquiz aprobará su saldo al recibir el capture.</i></p>
        </div>
    `);
});

// Ruta para procesar la recarga y chequear el capture
app.post('/recargar', (req, res) => {
    const { idCapture } = req.body;

    if (capturasUsadas.includes(idCapture)) {
        return res.status(400).json({ error: "❌ Este capture ya fue usado anteriormente." });
    }

    capturasUsadas.push(idCapture);
    res.json({ success: true, message: "Recarga en proceso. Wilfredo está verificando." });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log("Motor Will-Pay encendido 🚀");
});
