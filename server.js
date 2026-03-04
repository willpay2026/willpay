const express = require('express');
const app = express();
app.use(express.json());

// --- CONFIGURACIÓN DE SEGURIDAD ---
const PORT = process.env.PORT || 10000; 
const MASTER_PASSWORD = "WILL_PAY_BOSS"; // Tu clave para el panel

let balanceTotal = 0;
let comisionesGanadas = 0;
let usedCaptures = []; // Búnker anti-fraude

// TUS DATOS DE PAGO (Banesco)
const paymentDetails = {
    bank: "Banesco",
    phone: "04126602555",
    id: "13496133",
    owner: "Wilfredo Donquiz"
};

// 1. VISTA PÚBLICA (Diseño limpio y directo)
app.get('/', (req, res) => {
    res.send(`
        <div style="text-align:center; font-family:sans-serif; margin-top:50px;">
            <h1 style="color:#1a73e8;">🚀 Will-Pay Global 2026</h1>
            <p>El legado para <b>Wilyanny Donquiz</b> está en línea.</p>
            <hr style="width:50%">
            <div style="background:#f4f4f4; padding:20px; border-radius:10px; display:inline-block; border:1px solid #ccc;">
                <h3>Datos para Recarga:</h3>
                <p><b>Banco:</b> ${paymentDetails.bank}<br>
                   <b>Pago Móvil:</b> ${paymentDetails.phone}<br>
                   <b>C.I:</b> ${paymentDetails.id}</p>
            </div>
            <p style="color:gray; margin-top:20px;"><i>Wilfredo aprobará tu saldo al verificar el capture.</i></p>
        </div>
    `);
});

// 2. PANEL DE CONTROL (Solo para ti y tus 5 socios reservados)
app.get('/panel-control', (req, res) => {
    const pass = req.query.pass;
    if (pass !== MASTER_PASSWORD) {
        return res.status(403).send("<h1>🚫 Acceso Denegado</h1>");
    }

    res.send(`
        <div style="font-family:sans-serif; padding:20px;">
            <h2>🛠️ Mi Panel - Wilfredo Donquiz</h2>
            <div style="background:#e8f0fe; padding:15px; border-radius:10px;">
                <p><b>Comisiones Acumuladas:</b> $${comisionesGanadas}</p>
                <p><b>Espacios Reservados:</b> 5 Socios.</p>
            </div>
            <h3>Captures Procesados:</h3>
            <p>${usedCaptures.length} transacciones verificadas.</p>
        </div>
    `);
});

// 3. LÓGICA DE PROCESAMIENTO (Anti-fraude)
app.post('/process-payment', (req, res) => {
    const { captureId, amount } = req.body;

    if (usedCaptures.includes(captureId)) {
        return res.status(400).json({ error: "Capture ya usado." });
    }

    usedCaptures.push(captureId);
    // Cálculo de comisión (Ejemplo: 1%)
    comisionesGanadas += (amount * 0.01);
    
    res.json({ message: "Pago en revisión por el administrador." });
});

app.listen(PORT, () => {
    console.log("Motor Will-Pay encendido 🚀");
});
