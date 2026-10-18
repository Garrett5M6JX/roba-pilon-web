const socket = io("https://roba-pilon-web.onrender.com/");

const btnConectar = document.getElementById("btn-conectar");
const pantallaLogin = document.getElementById("pantalla-login");
const pantallaJuego = document.getElementById("pantalla-juego");
const cartasMesa = document.getElementById("cartas-mesa");
const cartasMano = document.getElementById("cartas-mano");
const infoTurno = document.getElementById("info-turno");
const infoMazo = document.getElementById("info-mazo");
const areaOponentes = document.getElementById("area-oponentes");

let miSocketId = null;

socket.on("connect", () => {
    miSocketId = socket.id;
});

btnConectar.addEventListener("click", () => {
    const nombre = document.getElementById("input-nombre").value;
    const numJugadores = document.getElementById("select-num-jugadores").value;
    const usarIa = document.getElementById("select-modo").value === "true";

    socket.emit("crear_o_unirse", { 
        nombre: nombre || "Jugador", 
        num_jugadores: parseInt(numJugadores), 
        usar_ia: usarIa 
    });

    pantallaLogin.classList.add("oculto");
    pantallaJuego.classList.remove("oculto");
});

function renderizarCartas(contenedor, listaCartas, esManoPropia = false) {
    contenedor.innerHTML = "";
    listaCartas.forEach((c, index) => {
        const div = document.createElement("div");
        div.className = "carta";
        
        div.innerHTML = `
            <span class="valor">${c.valor}</span>
            <span class="palo">${c.palo}</span>
        `;
        
        if (esManoPropia) {
            div.addEventListener("click", () => {
                socket.emit("jugar_carta", { carta_idx: index });
            });
        }
        contenedor.appendChild(div);
    });
}

socket.on("actualizar_estado", (estado) => {
    infoMazo.innerText = `Mazo: ${estado.mazo_restantes} cartas`;
    
    // Renderizar la Mesa
    cartasMesa.innerHTML = "";
    estado.mesa.forEach(c => {
        const div = document.createElement("div");
        div.className = "carta";
        div.innerHTML = `
            <span class="valor">${c.valor}</span>
            <span class="palo">${c.palo}</span>
        `;
        cartasMesa.appendChild(div);
    });

    // Renderizar Jugadores, Oponentes y Mano Propia
    areaOponentes.innerHTML = "";
    estado.jugadores.forEach((j, idx) => {
        if (j.id === miSocketId) {
            // Es nuestra mano
            renderizarCartas(cartasMano, j.mano, true);

            if (estado.turno_idx === idx) {
                infoTurno.innerText = "¡Es tu turno!";
                infoTurno.style.color = "#64ff64";
            } else {
                infoTurno.innerText = `Turno de: ${estado.jugadores[estado.turno_idx].nombre}`;
                infoTurno.style.color = "#f0be3c";
            }
        } else {
            // Es un oponente
            const opDiv = document.createElement("div");
            opDiv.className = "oponente-card";
            if (estado.turno_idx === idx) {
                opDiv.style.borderColor = "#64ff64";
                opDiv.style.boxShadow = "0 0 10px #64ff64";
            }
            opDiv.innerHTML = `<strong>${j.nombre}</strong><br>Mano: ${j.mano_count} cartas<br>Pilón: ${j.pilon_count} cartas`;
            areaOponentes.appendChild(opDiv);
        }
    });

    if (estado.juego_terminado) {
        alert("¡Partida Finalizada!");
    }
});
