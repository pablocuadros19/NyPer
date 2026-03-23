// ============================
// Tablero Nacho — Lógica del tablero
// ============================

// Configuración de animación
const CONFIG = {
    velocidadMovimiento: 'normal', // 'normal' (500ms) o 'lenta' (1200ms)
};

// Estado
let estado = {
    enPartida: false,
    casillaSeleccionada: null,
    movimientosValidos: [],
    colorJugador: 'blancas',
    modoEnsenanza: true,
    nivelSeleccionado: 1,
    colorSeleccionado: 'blancas',
    esperandoRespuesta: false,
};

// Utilidades
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function svgPieza(simbolo) {
    const esBlanca = simbolo === simbolo.toUpperCase();
    const color = esBlanca ? 'w' : 'b';
    const letra = simbolo.toUpperCase();
    return `/static/assets/piezas/${color}${letra}.svg`;
}

// ---- Inicialización ----

document.addEventListener('DOMContentLoaded', () => {
    dibujarTableroVacio();
    cargarEstado();
});

function dibujarTableroVacio() {
    const tablero = document.getElementById('tablero');
    tablero.innerHTML = '';

    for (let fila = 7; fila >= 0; fila--) {
        for (let col = 0; col < 8; col++) {
            const casilla = document.createElement('div');
            const esClara = (fila + col) % 2 === 1;
            const nombre = String.fromCharCode(97 + col) + (fila + 1);

            casilla.className = `casilla ${esClara ? 'clara' : 'oscura'}`;
            casilla.dataset.casilla = nombre;
            casilla.onclick = () => clickCasilla(nombre);

            // Coordenadas
            if (col === 0) {
                const coord = document.createElement('span');
                coord.className = 'coord-fila';
                coord.textContent = fila + 1;
                casilla.appendChild(coord);
            }
            if (fila === 0) {
                const coord = document.createElement('span');
                coord.className = 'coord-col';
                coord.textContent = String.fromCharCode(97 + col);
                casilla.appendChild(coord);
            }

            tablero.appendChild(casilla);
        }
    }
}

function dibujarTablero() {
    const tablero = document.getElementById('tablero');
    tablero.innerHTML = '';

    const invertir = estado.colorJugador === 'negras';
    const rangoFilas = invertir ? [0,1,2,3,4,5,6,7] : [7,6,5,4,3,2,1,0];
    const rangoCols = invertir ? [7,6,5,4,3,2,1,0] : [0,1,2,3,4,5,6,7];

    for (const fila of rangoFilas) {
        for (const col of rangoCols) {
            const casilla = document.createElement('div');
            const esClara = (fila + col) % 2 === 1;
            const nombre = String.fromCharCode(97 + col) + (fila + 1);

            casilla.className = `casilla ${esClara ? 'clara' : 'oscura'}`;
            casilla.dataset.casilla = nombre;
            casilla.onclick = () => clickCasilla(nombre);

            // Coordenadas en bordes
            const filaIdx = rangoFilas.indexOf(fila);
            const colIdx = rangoCols.indexOf(col);
            if (colIdx === 0) {
                const coord = document.createElement('span');
                coord.className = 'coord-fila';
                coord.textContent = fila + 1;
                casilla.appendChild(coord);
            }
            if (filaIdx === 7) {
                const coord = document.createElement('span');
                coord.className = 'coord-col';
                coord.textContent = String.fromCharCode(97 + col);
                casilla.appendChild(coord);
            }

            tablero.appendChild(casilla);
        }
    }
}

// ---- Renderizado ----

function renderizarPiezas(piezas) {
    document.querySelectorAll('.casilla .pieza').forEach(el => el.remove());

    for (const [casilla, info] of Object.entries(piezas)) {
        const el = document.querySelector(`[data-casilla="${casilla}"]`);
        if (!el) continue;

        const img = document.createElement('img');
        img.className = 'pieza';
        img.src = svgPieza(info.simbolo);
        img.alt = info.nombre || '';
        img.draggable = false;
        el.appendChild(img);
    }
}

function actualizarEstadoVisual(data) {
    if (!data) return;

    // Redibujar tablero con orientación correcta
    dibujarTablero();

    // Piezas
    if (data.piezas) {
        renderizarPiezas(data.piezas);
    }

    // Último movimiento
    if (data.ultimo_movimiento) {
        marcarCasilla(data.ultimo_movimiento.origen, 'ultimo-mov');
        marcarCasilla(data.ultimo_movimiento.destino, 'ultimo-mov');
    }

    // Rey en jaque
    if (data.es_jaque && data.rey_en_jaque) {
        marcarCasilla(data.rey_en_jaque, 'en-jaque');
    }

    // Turno
    const turnoLabel = document.getElementById('turno-label');
    if (data.es_jaque_mate) {
        turnoLabel.textContent = '¡Jaque mate!';
        turnoLabel.className = 'turno-label';
    } else if (data.es_tablas) {
        turnoLabel.textContent = 'Tablas';
        turnoLabel.className = 'turno-label';
    } else if (data.en_partida) {
        const esTuTurno = data.turno === estado.colorJugador;
        turnoLabel.textContent = esTuTurno ? '¡Tu turno!' : 'Pensando...';
        turnoLabel.className = `turno-label ${esTuTurno ? 'tu-turno' : ''}`;
    }

    // Botones
    const enPartida = data.en_partida !== false;
    document.getElementById('btn-deshacer').disabled = !enPartida || !data.puede_deshacer;
    document.getElementById('btn-consejo').disabled = !enPartida;
    document.getElementById('btn-rendirse').disabled = !enPartida;

    estado.enPartida = enPartida;

    // Panel de jugadas
    if (data.historial_san !== undefined) {
        actualizarJugadas(data.historial_san);
    }
}

function marcarCasilla(nombre, clase) {
    const el = document.querySelector(`[data-casilla="${nombre}"]`);
    if (el) el.classList.add(clase);
}

function limpiarSeleccion() {
    document.querySelectorAll('.casilla').forEach(el => {
        el.classList.remove('seleccionada', 'mov-valido', 'mov-valido-captura');
    });
    estado.casillaSeleccionada = null;
    estado.movimientosValidos = [];
}

// ---- Interacción ----

async function clickCasilla(nombre) {
    if (!estado.enPartida || estado.esperandoRespuesta) return;

    // Si hay casilla seleccionada y clickeamos un destino válido → mover
    if (estado.casillaSeleccionada) {
        const movValido = estado.movimientosValidos.find(m => m.destino === nombre);
        if (movValido) {
            await moverPieza(estado.casillaSeleccionada, nombre);
            return;
        }
    }

    // Seleccionar nueva casilla (solo si tiene pieza propia)
    limpiarSeleccion();

    const resp = await fetch(`/api/movimientos_validos?casilla=${nombre}`);
    const data = await resp.json();

    if (data.movimientos && data.movimientos.length > 0) {
        estado.casillaSeleccionada = nombre;
        estado.movimientosValidos = data.movimientos;

        marcarCasilla(nombre, 'seleccionada');

        for (const mov of data.movimientos) {
            const clase = mov.es_captura ? 'mov-valido-captura' : 'mov-valido';
            marcarCasilla(mov.destino, clase);
        }
    }
}

async function moverPieza(origen, destino) {
    estado.esperandoRespuesta = true;
    limpiarSeleccion();

    try {
        const resp = await fetch('/api/mover', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ origen, destino }),
        });

        const data = await resp.json();
        if (data.error) {
            console.error(data.error);
            estado.esperandoRespuesta = false;
            return;
        }

        // Fase 1: aplicar movimiento del jugador en el DOM (instantáneo)
        aplicarMovimientoJugador(origen, destino);

        // Comentario del profesor
        if (data.comentario_profesor) {
            agregarMensajeProfesor(data.comentario_profesor);
        }

        // Fase 2: animar movimiento del oponente
        if (data.movimiento_oponente) {
            await delay(350);
            await animarMovimientoOponente(data.movimiento_oponente);
        }

        // Fase 3: refresh completo para quedar en sync con el servidor
        actualizarEstadoVisual(data.estado);

        // Fin de partida
        if (data.fin_partida) {
            mostrarFinPartida(data.fin_partida);
        }

    } catch (err) {
        console.error('Error al mover:', err);
    }

    estado.esperandoRespuesta = false;
}

// Mueve la pieza del jugador en el DOM sin redibujar todo
function aplicarMovimientoJugador(origen, destino) {
    const casOrigen = document.querySelector(`[data-casilla="${origen}"]`);
    const casDestino = document.querySelector(`[data-casilla="${destino}"]`);
    if (!casOrigen || !casDestino) return;

    // Remover pieza capturada en destino (si hay)
    const capturada = casDestino.querySelector('.pieza');
    if (capturada) capturada.remove();

    // Mover la pieza del jugador
    const pieza = casOrigen.querySelector('.pieza');
    if (pieza) casDestino.appendChild(pieza);

    // Marcar último movimiento visualmente
    document.querySelectorAll('.casilla.ultimo-mov').forEach(el => el.classList.remove('ultimo-mov'));
    casOrigen.classList.add('ultimo-mov');
    casDestino.classList.add('ultimo-mov');
}

// Anima el movimiento del oponente con slide suave
async function animarMovimientoOponente(movimiento) {
    const { origen, destino } = movimiento;
    const casOrigen = document.querySelector(`[data-casilla="${origen}"]`);
    const casDestino = document.querySelector(`[data-casilla="${destino}"]`);
    if (!casOrigen || !casDestino) return;

    const pieza = casOrigen.querySelector('.pieza');
    if (!pieza) return;

    const origenRect = casOrigen.getBoundingClientRect();
    const destinoRect = casDestino.getBoundingClientRect();
    const dx = destinoRect.left - origenRect.left;
    const dy = destinoRect.top - origenRect.top;

    const duracion = CONFIG.velocidadMovimiento === 'lenta' ? 1200 : 500;

    // Si captura: fade out la pieza capturada cuando la animación llega
    const capturada = casDestino.querySelector('.pieza');
    if (capturada) {
        setTimeout(() => {
            capturada.style.transition = `opacity ${duracion * 0.3}ms ease-out`;
            capturada.style.opacity = '0';
        }, duracion * 0.6);
    }

    // Setup y lanzar animación
    pieza.style.position = 'relative';
    pieza.style.zIndex = '10';
    pieza.style.transition = `transform ${duracion}ms cubic-bezier(0.25, 0.1, 0.25, 1)`;
    void pieza.offsetWidth; // forzar reflow
    pieza.style.transform = `translate(${dx}px, ${dy}px)`;

    await delay(duracion + 80);

    // Limpiar estilos de animación (el refresh completo viene después)
    pieza.style.transition = '';
    pieza.style.transform = '';
    pieza.style.position = '';
    pieza.style.zIndex = '';
}

// ---- Acciones ----

async function deshacer() {
    if (estado.esperandoRespuesta) return;

    const resp = await fetch('/api/deshacer', { method: 'POST' });
    const data = await resp.json();

    if (data.ok) {
        actualizarEstadoVisual(data.estado);
        agregarMensajeSistema('Movimiento deshecho');
    }
}

async function pedirConsejo() {
    if (estado.esperandoRespuesta) return;
    estado.esperandoRespuesta = true;

    agregarMensajeJugador('¿Qué me recomendás?');

    const resp = await fetch('/api/consejo', { method: 'POST' });
    const data = await resp.json();

    agregarMensajeProfesor(data.consejo);
    estado.esperandoRespuesta = false;
}

async function enviarChat() {
    const input = document.getElementById('chat-input');
    const mensaje = input.value.trim();
    if (!mensaje || estado.esperandoRespuesta) return;

    input.value = '';
    agregarMensajeJugador(mensaje);
    estado.esperandoRespuesta = true;

    const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje }),
    });
    const data = await resp.json();

    agregarMensajeProfesor(data.respuesta);
    estado.esperandoRespuesta = false;
}

async function rendirse() {
    if (!confirm('¿Seguro que querés rendirte?')) return;

    const resp = await fetch('/api/rendirse', { method: 'POST' });
    const data = await resp.json();

    if (data.ok) {
        mostrarFinPartida(data.fin_partida);
        estado.enPartida = false;
        document.getElementById('btn-deshacer').disabled = true;
        document.getElementById('btn-consejo').disabled = true;
        document.getElementById('btn-rendirse').disabled = true;
        document.getElementById('turno-label').textContent = 'Partida terminada';
        document.getElementById('turno-label').className = 'turno-label';
    }
}

function toggleVelocidad() {
    CONFIG.velocidadMovimiento = CONFIG.velocidadMovimiento === 'normal' ? 'lenta' : 'normal';
    const label = document.getElementById('velocidad-label');
    if (label) {
        label.textContent = CONFIG.velocidadMovimiento === 'lenta' ? '🐢 Lento' : '⚡ Normal';
    }
}

// ---- Panel de jugadas anotadas ----

function toggleJugadas() {
    const panel = document.getElementById('panel-jugadas');
    const btnMostrar = document.getElementById('btn-mostrar-jugadas');
    const colapsado = panel.classList.toggle('colapsado');
    btnMostrar.classList.toggle('oculto', !colapsado);
}

function actualizarJugadas(historialSan) {
    const lista = document.getElementById('jugadas-lista');
    if (!historialSan || historialSan.length === 0) {
        lista.innerHTML = '<p class="jugadas-vacio">Las jugadas van a aparecer acá</p>';
        return;
    }

    let html = '';
    for (let i = 0; i < historialSan.length; i += 2) {
        const num = Math.floor(i / 2) + 1;
        const blanca = historialSan[i] || '';
        const negra = historialSan[i + 1] || '';
        const esUltima = (i + 1 >= historialSan.length - 1);
        html += `<div class="jugada-fila${esUltima ? ' ultima-jugada' : ''}">
            <span class="jugada-num">${num}.</span>
            <span class="jugada-blanca">${blanca}</span>
            <span class="jugada-negra">${negra}</span>
        </div>`;
    }
    lista.innerHTML = html;
    // Scroll al final
    lista.scrollTop = lista.scrollHeight;
}

async function toggleEnsenanza() {
    const resp = await fetch('/api/toggle_ensenanza', { method: 'POST' });
    const data = await resp.json();
    estado.modoEnsenanza = data.modo_ensenanza;
    agregarMensajeSistema(
        data.modo_ensenanza ? 'Modo enseñanza: ON' : 'Modo enseñanza: OFF'
    );
}

// ---- Nueva partida ----

function mostrarMenuNueva() {
    document.getElementById('modal-nueva').classList.remove('oculto');
}

function cerrarModal() {
    document.getElementById('modal-nueva').classList.add('oculto');
}

function seleccionarNivel(nivel) {
    estado.nivelSeleccionado = nivel;
    document.querySelectorAll('[data-nivel]').forEach(btn => {
        btn.classList.toggle('nivel-seleccionado', parseInt(btn.dataset.nivel) === nivel);
    });
}

function seleccionarColor(color) {
    estado.colorSeleccionado = color;
    document.querySelectorAll('[data-color]').forEach(btn => {
        btn.classList.toggle('color-seleccionado', btn.dataset.color === color);
    });
}

function seleccionarVelocidad(vel) {
    CONFIG.velocidadMovimiento = vel;
    document.querySelectorAll('[data-vel]').forEach(btn => {
        btn.classList.toggle('vel-seleccionado', btn.dataset.vel === vel);
    });
    const label = document.getElementById('velocidad-label');
    if (label) label.textContent = vel === 'lenta' ? '🐢 Lento' : '⚡ Normal';
}

async function iniciarDesdeModal() {
    const nombre = document.getElementById('bienvenida-nombre').value.trim() || 'Jugador';
    document.getElementById('modal-bienvenida').classList.add('oculto');

    estado.colorJugador = estado.colorSeleccionado;
    estado.esperandoRespuesta = true;

    const chatMsgs = document.getElementById('chat-mensajes');
    chatMsgs.innerHTML = '';
    actualizarJugadas([]);
    agregarMensajeSistema('Iniciando partida...');

    const resp = await fetch('/api/iniciar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            nombre,
            nivel: estado.nivelSeleccionado,
            color: estado.colorSeleccionado,
            velocidad: CONFIG.velocidadMovimiento,
        }),
    });

    const data = await resp.json();

    // Actualizar nombre en header
    document.getElementById('nombre-profesor').textContent = 'El Profe';

    const niveles = { 1: '🌱 Aprendiz', 2: '🤝 Compañero', 3: '⚔️ Desafío' };
    document.getElementById('nivel-label').textContent = niveles[estado.nivelSeleccionado] || '';

    estado.enPartida = true;
    data.en_partida = true;
    data.color_jugador = estado.colorJugador;
    actualizarEstadoVisual(data);

    if (data.saludo_profesor) agregarMensajeProfesor(data.saludo_profesor);

    estado.esperandoRespuesta = false;
}

async function iniciarPartida() {
    cerrarModal();
    estado.colorJugador = estado.colorSeleccionado;
    estado.esperandoRespuesta = true;

    // Limpiar chat y jugadas
    const chatMsgs = document.getElementById('chat-mensajes');
    chatMsgs.innerHTML = '';
    actualizarJugadas([]);

    agregarMensajeSistema('Iniciando partida...');

    const resp = await fetch('/api/nueva_partida', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            nivel: estado.nivelSeleccionado,
            color: estado.colorSeleccionado,
        }),
    });

    const data = await resp.json();

    // Nivel label
    const niveles = { 1: '🌱 Aprendiz', 2: '🤝 Compañero', 3: '⚔️ Desafío' };
    document.getElementById('nivel-label').textContent = niveles[estado.nivelSeleccionado] || '';

    estado.enPartida = true;
    data.en_partida = true;
    data.color_jugador = estado.colorJugador;
    actualizarEstadoVisual(data);

    // Saludo del profesor
    if (data.saludo_profesor) {
        agregarMensajeProfesor(data.saludo_profesor);
    }

    estado.esperandoRespuesta = false;
}

// ---- Mensajes del chat ----

function agregarMensajeProfesor(texto) {
    agregarMensaje(texto, 'mensaje-profesor');
}

function agregarMensajeJugador(texto) {
    agregarMensaje(texto, 'mensaje-jugador');
}

function agregarMensajeSistema(texto) {
    agregarMensaje(texto, 'mensaje-sistema');
}

function agregarMensaje(texto, clase) {
    const container = document.getElementById('chat-mensajes');
    const msg = document.createElement('div');
    msg.className = `mensaje ${clase}`;
    msg.innerHTML = `<p>${texto}</p>`;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

function mostrarFinPartida(data) {
    const resultados = {
        'victoria': '🎉 ¡Ganaste!',
        'derrota': '😤 Perdiste esta vez...',
        'empate': '🤝 ¡Tablas!',
        'abandonada': '🏳️ Partida abandonada',
    };

    agregarMensajeSistema(resultados[data.resultado] || 'Partida terminada');

    if (data.resumen_profesor) {
        agregarMensajeProfesor(data.resumen_profesor);
    }

    if (data.duracion) {
        agregarMensajeSistema(`Duración: ${data.duracion} minutos`);
    }
}

// ---- Carga inicial ----

async function cargarEstado() {
    try {
        const resp = await fetch('/api/estado');
        const data = await resp.json();

        if (data.en_partida) {
            estado.colorJugador = data.color_jugador || 'blancas';
            actualizarEstadoVisual(data);
        }
    } catch (err) {
        console.log('Sin partida activa');
    }
}
