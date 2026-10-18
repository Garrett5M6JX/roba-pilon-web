<ElicitationsGroup>
Aquí tienes el archivo `server.py` completo y actualizado, con el bloque conflictivo de FastAPI eliminado para que solo Socket.io maneje los permisos de CORS de forma limpia y sin duplicidades:

```python
import random
import socketio
from fastapi import FastAPI

# Socket.io maneja los orígenes permitidos directamente para evitar duplicar cabeceras
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()

# Eliminamos CORSMiddleware de FastAPI para evitar el conflicto de múltiples valores

app.mount("/", socketio.ASGIApp(sio))

partidas = {}

class Carta:
    def __init__(self, palo, valor):
        self.palo = palo  # 'basto', 'oro', 'espada', 'copa' en minúsculas
        self.valor = valor

    def obtener_siguiente(self):
        if self.valor == 7:
            return 10
        elif self.valor == 12:
            return None
        return self.valor + 1

    def to_dict(self):
        return {"palo": self.palo, "valor": self.valor}

class Mazo:
    def __init__(self):
        self.cartas = []
        # Nombres en minúsculas para que coincidan con tus archivos: basto_1.png, etc.
        palos = ["basto", "oro", "espada", "copa"]
        valores = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
        self.cartas = [Carta(palo, valor) for palo in palos for valor in valores]
        random.shuffle(self.cartas)

    def robar(self):
        if self.cartas:
            return self.cartas.pop()
        return None

class PartidaJuego:
    def __init__(self, room_id, num_jugadores, usar_ia):
        self.room_id = room_id
        self.num_jugadores = num_jugadores
        self.usar_ia = usar_ia
        self.jugadores = []
        self.mazo = Mazo()
        self.mesa = []
        self.turno_idx = 0
        self.ultimo_en_capturar = None
        self.juego_terminado = False

    def inicializar(self):
        valores_en_mesa = set()
        while len(self.mesa) < 4 and len(self.mazo.cartas) > 0:
            c = self.mazo.robar()
            if c.valor not in valores_en_mesa:
                self.mesa.append(c)
                valores_en_mesa.add(c.valor)
            else:
                self.mazo.cartas.insert(0, c)
                random.shuffle(self.mazo.cartas)

        for j in self.jugadores:
            for _ in range(3):
                c = self.mazo.robar()
                if c:
                    j["mano"].append(c)

    def obtener_estado(self):
        return {
            "mesa": [c.to_dict() for c in self.mesa],
            "mazo_restantes": len(self.mazo.cartas),
            "turno_idx": self.turno_idx,
            "juego_terminado": self.juego_terminado,
            "jugadores": [
                {
                    "id": j["id"],
                    "nombre": j["nombre"],
                    "es_ia": j["es_ia"],
                    "mano_count": len(j["mano"]),
                    "mano": [c.to_dict() for c in j["mano"]] if not j["es_ia"] else [],
                    "pilon_count": len(j["pilon"]),
                    "pilon_cima": j["pilon"][-1].to_dict() if j["pilon"] else None
                }
                for j in self.jugadores
            ]
        }

@sio.event
async def connect(sid, environ):
    pass

@sio.event
async def disconnect(sid):
    pass

@sio.event
async def crear_o_unirse(sid, data):
    nombre = data.get("nombre", "Jugador")
    num_jugadores = int(data.get("num_jugadores", 2))
    usar_ia = data.get("usar_ia", True)
    
    room_id = "sala_principal"
    if room_id not in partidas:
        partidas[room_id] = PartidaJuego(room_id, num_jugadores, usar_ia)
        
    partida = partidas[room_id]
    
    # Evitar duplicar conexión si el usuario recarga
    partida.jugadores = [j for j in partida.jugadores if j["id"] != sid]
    
    partida.jugadores.append({
        "id": sid,
        "nombre": nombre,
        "es_ia": False,
        "mano": [],
        "pilon": []
    })
    
    sio.enter_room(sid, room_id)
    
    if len(partida.jugadores) < num_jugadores and partida.usar_ia:
        while len(partida.jugadores) < num_jugadores:
            idx_ia = len(partida.jugadores) + 1
            partida.jugadores.append({
                "id": f"ia_{idx_ia}",
                "nombre": f"Computadora {idx_ia}",
                "es_ia": True,
                "mano": [],
                "pilon": []
            })
            
    if len(partida.jugadores) >= num_jugadores and not partida.mesa and len(partida.mazo.cartas) == 40:
        partida.inicializar()
        
    await sio.emit('actualizar_estado', partida.obtener_estado(), room=room_id)

@sio.event
async def jugar_carta(sid, data):
    room_id = "sala_principal"
    partida = partidas.get(room_id)
    if not partida or partida.juego_terminado:
        return

    jugador_actual = partida.jugadores[partida.turno_idx]
    if jugador_actual["id"] != sid:
        return

    carta_idx = data.get("carta_idx")
    if carta_idx < 0 or carta_idx >= len(jugador_actual["mano"]):
        return

    carta_jugada_dict = jugador_actual["mano"].pop(carta_idx)
    carta_jugada = Carta(carta_jugada_dict["palo"], carta_jugada_dict["valor"])

    coincidencias_mesa = [c for c in partida.mesa if c.valor == carta_jugada.valor]
    botin = [carta_jugada]

    if coincidencias_mesa:
        for c_mesa in coincidencias_mesa:
            partida.mesa.remove(c_mesa)
            botin.append(c_mesa)

        for rival in partida.jugadores:
            if rival["id"] != jugador_actual["id"] and rival["pilon"]:
                cima = rival["pilon"][-1]
                if cima.valor == carta_jugada.valor:
                    botin.extend(rival["pilon"])
                    rival["pilon"] = []

        valor_buscado = carta_jugada.obtener_siguiente()
        while valor_buscado is not None:
            encontrado = False
            for c_mesa in list(partida.mesa):
                if c_mesa.valor == valor_buscado:
                    partida.mesa.remove(c_mesa)
                    botin.append(c_mesa)
                    valor_buscado = c_mesa.obtener_siguiente()
                    encontrado = True
                    break
            if encontrado:
                continue

            rival_encontrado = None
            for rival in partida.jugadores:
                if rival["id"] != jugador_actual["id"] and rival["pilon"]:
                    cima = rival["pilon"][-1]
                    if cima.valor == valor_buscado:
                        rival_encontrado = rival
                        break
            if rival_encontrado:
                botin.extend(rival_encontrado["pilon"])
                rival_encontrado["pilon"] = []
                valor_buscado = botin[-1].obtener_siguiente()
                encontrado = True

            if not encontrado:
                break

        jugador_actual["pilon"].extend(botin)
        partida.ultimo_en_capturar = jugador_actual
    else:
        partida.mesa.append(carta_jugada)

    if all(len(j["mano"]) == 0 for j in partida.jugadores):
        if len(partida.mazo.cartas) > 0:
            for j in partida.jugadores:
                for _ in range(3):
                    c = partida.mazo.robar()
                    if c:
                        j["mano"].append(c)
        else:
            partida.juego_terminado = True
            if partida.mesa and partida.ultimo_en_capturar:
                partida.ultimo_en_capturar["pilon"].extend(partida.mesa)
                partida.mesa = []

    partida.turno_idx = (partida.turno_idx + 1) % len(partida.jugadores)
    await sio.emit('actualizar_estado', partida.obtener_estado(), room=room_id)

    while not partida.juego_terminado and partida.jugadores[partida.turno_idx]["es_ia"]:
        await sio.sleep(1)
        ia = partida.jugadores[partida.turno_idx]
        if ia["mano"]:
            carta_ia = ia["mano"].pop(0)
            c_obj = Carta(carta_ia["palo"], carta_ia["valor"])
            coincidencias = [c for c in partida.mesa if c.valor == c_obj.valor]
            botin_ia = [c_obj]
            if coincidencias:
                for cm in coincidencias:
                    partida.mesa.remove(cm)
                    botin_ia.append(cm)
                ia["pilon"].extend(botin_ia)
            else:
                partida.mesa.append(c_obj)
        
        if all(len(j["mano"]) == 0 for j in partida.jugadores):
            if len(partida.mazo.cartas) > 0:
                for j in partida.jugadores:
                    for _ in range(3):
                        c = partida.mazo.robar()
                        if c: j["mano"].append(c)
            else:
                partida.juego_terminado = True

        partida.turno_idx = (partida.turno_idx + 1) % len(partida.jugadores)
        await sio.emit('actualizar_estado', partida.obtener_estado(), room=room_id)
