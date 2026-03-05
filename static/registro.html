// Módulo de ADN Digital Will-Pay - GESTIÓN BANCARIA
window.iniciarRegistroADN = () => {
    const panel = document.getElementById('content-box');
    
    panel.innerHTML = `
        <div style="animation: fadeIn 0.5s; padding: 10px; text-align: center;">
            <div style="margin-bottom: 20px;">
                <h2 style="color: var(--gold); margin: 0; font-size: 1.6rem; letter-spacing: 2px;">ADN DIGITAL</h2>
                <p style="color: #666; font-size: 0.6rem; letter-spacing: 3px; text-transform: uppercase;">Configuración de Cuenta y Retiros</p>
            </div>

            <div style="background: #0a0a0a; border: 1.5px solid #1a1a1a; border-radius: 30px; padding: 25px; box-shadow: 0 15px 35px rgba(0,0,0,0.8);">
                
                <div style="max-height: 65vh; overflow-y: auto; padding-right: 5px; text-align: left;">
                    
                    <p style="color:var(--gold); font-size:0.7rem; border-bottom:1px solid #222; padding-bottom:5px; margin-bottom:15px;">1. IDENTIDAD</p>
                    <label style="color: #555; font-size: 0.6rem; font-weight: bold; margin-left: 10px;">NOMBRE Y APELLIDO</label>
                    <input type="text" id="reg-nombre" placeholder="Ej: Wilfredo Donquiz" style="width:100%; padding:15px; margin: 8px 0 20px 0; background:#000; border:1px solid #222; color:#fff; border-radius:18px;">

                    <label style="color: #555; font-size: 0.6rem; font-weight: bold; margin-left: 10px;">CÉDULA / RIF</label>
                    <input type="number" id="reg-cedula" placeholder="Ej: 13496133" style="width:100%; padding:15px; margin: 8px 0 20px 0; background:#000; border:1px solid #222; color:#fff; border-radius:18px;">

                    <p style="color:var(--gold); font-size:0.7rem; border-bottom:1px solid #222; padding-bottom:5px; margin-top:10px; margin-bottom:15px;">2. DESTINO DE FONDOS (PARA RETIROS)</p>
                    
                    <label style="color: #555; font-size: 0.6rem; font-weight: bold; margin-left: 10px;">BANCO DESTINO</label>
                    <select id="reg-banco" style="width:100%; padding:15px; margin: 8px 0 20px 0; background:#000; border:1px solid #222; color:#fff; border-radius:18px; font-family: 'Lexend';">
                        <option value="0102">BANCO DE VENEZUELA</option>
                        <option value="0134">BANESCO</option>
                        <option value="0105">MERCANTIL</option>
                        <option value="0108">PROVINCIAL</option>
                        <option value="0172">BANCAMIGA</option>
                    </select>

                    <label style="color: #555; font-size: 0.6rem; font-weight: bold; margin-left: 10px;">TELÉFONO PAGO MÓVIL</label>
                    <input type="number" id="reg-tlf-banco" placeholder="0412..." style="width:100%; padding:15px; margin: 8px 0 20px 0; background:#000; border:1px solid #222; color:#fff; border-radius:18px;">

                    <p style="color:var(--gold); font-size:0.7rem; border-bottom:1px solid #222; padding-bottom:5px; margin-top:10px; margin-bottom:15px;">3. SEGURIDAD ADN</p>
                    
                    <label style="color: #555; font-size: 0.6rem; font-weight: bold; margin-left: 10px;">MODALIDAD</label>
                    <select id="reg-tipo" onchange="window.verificarActividad()" style="width:100%; padding:15px; margin: 8px 0 25px 0; background:#000; border:1.5px solid var(--gold); color:#fff; border-radius:18px;">
                        <option value="normal">Usuario Normal (Tasa 1.5%)</option>
                        <option value="negocio">Socio Comercial (Tasa 5.0%)</option>
                    </select>

                    <div id="seccion-negocio" style="display: none; margin-bottom: 20px;">
                        <label style="color: #555; font-size: 0.6rem; font-weight: bold; margin-left: 10px;">RAMA COMERCIAL</label>
                        <select id="reg-actividad" style="width:100%; padding:15px; margin: 8px 0; background:#000; border:1px solid #222; color:#fff; border-radius:18px;">
                            <option>Transporte</option><option>Alimentos</option><option>Servicios</option>
                        </select>
                    </div>

                    <label style="color: #555; font-size: 0.6rem; font-weight: bold; margin-left: 10px;">PIN DE SEGURIDAD (6 DÍGITOS)</label>
                    <input type="password" id="reg-pin" maxlength="6" placeholder="••••••" style="width:100%; padding:15px; margin: 8px 0; background:#000; border:1px solid #222; color:var(--gold); border-radius:18px; text-align:center; font-size: 1.5rem; letter-spacing: 8px;">
                </div>

                <button onclick="window.finalizarADN()" class="btn-gold" style="margin-top: 15px;">
                    GENERAR MI ADN DIGITAL
                </button>
            </div>
            
            <p onclick="location.reload()" style="color: #444; font-size: 0.7rem; text-align: center; margin-top: 25px; cursor: pointer;">← VOLVER</p>
        </div>
    `;
};

window.verificarActividad = () => {
    const tipo = document.getElementById('reg-tipo').value;
    document.getElementById('seccion-negocio').style.display = (tipo === 'negocio') ? 'block' : 'none';
};

window.finalizarADN = () => {
    const nombre = document.getElementById('reg-nombre').value;
    const banco = document.getElementById('reg-banco').value;
    const tlf = document.getElementById('reg-tlf-banco').value;
    const pin = document.getElementById('reg-pin').value;

    if(!nombre || !tlf || pin.length < 6) {
        return alert("⚠️ Faltan datos bancarios o el PIN no es de 6 dígitos.");
    }

    alert(`🎯 ADN GENERADO\n\nSocio: ${nombre.toUpperCase()}\nBanco: ${banco}\nPago Móvil: ${tlf}\n\nEspere aprobación de Wilfredo Donquiz.`);
    location.reload();
};
