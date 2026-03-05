const express = require('express');
const app = express();
const path = require('path');
const ejs = require('ejs');

// 1. MOTOR DE VISTA (Para que los cuadros dorados brillen)
app.set('views', path.join(__dirname, 'templates'));
app.engine('html', ejs.renderFile);
app.set('view engine', 'html');

// 2. MIDDLEWARES (Los porteros del búnker)
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'static')));

// 3. RUTA PRINCIPAL (Entrada pública)
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// 4. EL PANEL MAESTRO (Tu oficina de CEO)
app.get('/ceo', (req, res) => {
    // Aquí definimos los datos que el HTML "clásico" necesita para no dar error
    const u = { 
        id_dna: "CEO-0001-FOUNDER",
        nombre: "WILFREDO DONQUIZ", 
        saldo_bs: 0.00,
        saldo_wpc: 0.00,
        saldo_usd: 0.00,
        ganancia_neta: 0.00,
        ultimo_id_pendiente: "000000",
        ultimo_monto_pendiente: 0.00
    };
    
    // Enviamos los datos 'u' y una lista de movimientos 'm' (vacía por ahora)
    res.render('ceo_panel.html', { u: u, m: [] });
});

// 5. ACCESO (Lógica para entrar al panel)
app.post('/acceso', (req, res) => {
    console.log("Acceso autorizado al Búnker");
    res.redirect('/ceo'); 
});

// 6. ENCENDIDO DEL SERVIDOR
const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
    console.log('--- SISTEMA WILL-PAY: PANEL CLÁSICO ACTIVADO EN PUERTO ' + PORT + ' ---');
});
