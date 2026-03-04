const express = require('express');
const app = express();
app.use(express.json());

// --- CONFIGURACIÓN DEL DUEÑO (Wilfredo Donquiz) ---
const PORT = process.env.PORT || 10000; // Render usa el 10000
const MASTER_PASSWORD = "WILL_PAY_BOSS"; // Tu clave para el panel
const SOCIOS_PASSWORD = "WILL_PARTNER"; // Clave para tus 5 socios

let balanceTotal = 0;
let comisionesGanadas = 0;
let solicitudesPendientes = [];
let capturesUsados = []; // Búnker anti-fraude

// Datos de pago (Banesco)
const misDatos = {
    banco: "Banesco",
    telefono: "04126602555",
    cedula: "13496133",
    titular: "Wilfredo Donquiz"
};

// 1. VISTA PÚBLICA (Lo que ve el cliente)
app.get('/', (req, res) => {
    res.send(`
        <body style="font-family:sans-serif; text-align:center; padding:40px; background:#f0f2f5;">
            <h1 style="color:#1a73e8;">🚀 Will-Pay Global 2026</h1>
            <p>El legado de <b>Wilyanny Donquiz</b> para el mundo.</p>
            <div style="background:white; display:inline-block; padding:20px; border-radius:15px; border:2px solid #1a73e8;">
                <h3>Recarga tu Billetera aquí:</h3>
                <p><b>Banco:</b> ${misDatos.banco}</p>
                <p><b>Pago Móvil:</b> ${misDatos.telefono}</p>
                <p><b>C.I:</b> ${misDatos.cedula}</p>
            </div>
            <p><i>Envía tu capture al administrador para activar tu saldo.</i></p>
        </body>
    `);
});

// 2. PANEL MAESTRO Y DE SOCIOS (Protegido)
app.get('/panel-control', (req, res) => {
    const pass = req.query.pass;
    
    if (pass !== MASTER_PASSWORD && pass !== SOCIOS_PASSWORD) {
        return res.send("<h1>🚫 Acceso Denegado</h1><p>El búnker está protegido.</p>");
    }

    const esDuenio = (pass === MASTER_PASSWORD);
    
    res.send(`
        <body style="font-family:sans-serif; padding:20px; background:#e8f0fe;">
            <h2>🛠️ Panel de Control - ${esDuenio ? 'MODO DUEÑO' : 'MODO SOCIO'}</h2>
            <div style="background:white; padding:15px; border-radius:10px; margin-bottom:20px;">
                <h3>💰 Estado Financiero</h3>
                <p><b>Balance del Sistema:</b> $${balanceTotal}</p>
                ${esDuenio ? `<p style="color:green;"><b>Mis Comisiones:</b> $${comisionesGanadas}</p>` : ''}
            </div>
            <h3>📂 Solicitudes de Saldo (Aprobación Manual)</h3>
            ${solicitudesPendientes.length === 0 ? '<p>No hay pagos pendientes.</p>' : '<ul>...lista de pagos...</ul>'}
            <p><small>Espacios para socios reservados: 5 de 5.</small></p>
        </body>
    `);
});

// 3. RUTA PARA RECIBIR PAGOS (Anti-fraude)
app.post('/enviar-pago', (req, res) => {
    const { captureId, monto } = req.body;

    if (capturesUsados.includes(captureId)) {
        return res.status(400).json({ error: "❌ Este comprobante ya fue usado." });
    }

    capturesUsados.push(captureId);
    solicitudesPendientes.push({ captureId, monto, status: 'Pendiente' });
    
    // Aquí calculamos la comisión (ejemplo 1%)
    const comision = monto * 0.01;
    comisionesGanadas += comision;
    balanceTotal += (monto - comision);

    res.json({ message: "✅ Pago enviado. Wilfredo aprobará en breve." });
});

app.listen(PORT, () => {
    console.log(`Motor Will-Pay encendido en puerto ${PORT} 🚀`);
});
