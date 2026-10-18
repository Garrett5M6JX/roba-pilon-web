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

    socket.emit("crear_o_unirse", { nombre, num_jugadores: parseInt(numJugadores), usar_ia: usarIa });
    pantallaLogin.classList.add("oculto");
    pantallaJuego.classList.remove("oculto");
});

socket.on("actualizar_estado", (estado) => {
    infoMazo.innerText = `Mazo: ${estado.mazo_restantes} cartas`;
    
    cartasMesa.innerHTML = "";
    estado.mesa.forEach(c => {
        const div = document.createElement("div");
        div.className = "carta";
        div.innerHTML = `<span>${c.valor}</span><small>${c.palo}</small>`;
        cartasMesa.appendChild(div);
    });

    areaOponentes.innerHTML = "";
    estado.jugadores.forEach((j, idx) => {
        if (j.id === miSocketId) {
            cartasMano.innerHTML = "";
            j.mano.forEach((c, index) => {
                const div = document.createElement("div");
                div.className = "carta";
                div.innerHTML = `<span>${c.valor}</span><small>${c.palo}</small>`;
                div.addEventListener("click", () => {
                    socket.emit("jugar_carta", { carta_idx: index });
                });
                cartasMano.appendChild(div);
            });
            if (estado.turno_idx === idx) {
                infoTurno.innerText = "¡Es tu turno!";
                infoTurno.style.color = "#64ff64";
            }
        } else {
            const opDiv = document.createElement("div");
            opDiv.style.border = "1px solid #777";
            opDiv.style.padding = "10px";
            opDiv.style.borderRadius = "8px";
            opDiv.innerHTML = `<strong>${j.nombre}</strong><br>Mano: ${j.mano_count} | Pilón: ${j.pilon_count}`;
            if (estado.turno_idx === idx) {
                opDiv.style.borderColor = "#f0be3c";
            }
            areaOponentes.appendChild(opDiv);
        }
    });

    if (estado.juego_terminado) {
        alert("¡Partida Finalizada!");
    }
});
