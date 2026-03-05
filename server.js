const express = require('express');
const app = express();
const path = require('path');

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'static')));

// --- 1. RUTA PRINCIPAL (EL COHETE) ---
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// --- 2. RUTAS DE NAVEGACIÓN ---
app.get('/acceso', (req, res) => res.sendFile(path.join(__dirname, 'static', 'acceso.html')));
app.get('/registro', (req, res) => res.sendFile(path.join(__dirname, 'static', 'registro.html')));
app.get('/boveda', (req, res) => res.sendFile(path.join(__dirname, 'static', 'boveda.html')));
app.get('/dashboard', (req, res) => res.sendFile(path.join(__dirname, 'static', 'dashboard.html')));
app.get('/ceo', (req, res) => res.sendFile(path.join(__dirname, 'static', 'ceo_panel.html')));

// --- 3. LÓGICA DE PROCESOS (POST) ---
app.post('/acceso', (req, res) => {
    console.log("Intento de entrada al Búnker...");
    res.redirect('/boveda'); 
});

app.post('/guardar-registro', (req, res) => {
    res.send("<h1>✅ Registro Exitoso</h1><a href='/acceso'>Ir al Login</a>");
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log('--- SISTEMA WILL-PAY TOTALMENTE CONECTADO ---');
});
