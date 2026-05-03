import asyncio
import random

class AhorcadoServidorAsync:
    def __init__(self, host='localhost', port=8888, num_jugadores=3, palabra=None):
        self.host = host
        self.port = port
        self.num_jugadores = num_jugadores
        self.palabra = palabra or random.choice(["PYTHON", "PROGRAMACION", "PARALELA", "CONCURRENCIA", "AHORCADO"])
        self.progreso = ['_'] * len(self.palabra)
        self.intentos_restantes = 6
        self.jugadores = []  # lista de (writer, id)
        self.turno_actual = 0
        self.fin_juego = False
        self.barrera = None
        self.event_turno = None
        self.lock = None
        self.falladas = []
        
    async def broadcast(self, mensaje, excluir=None):
        for writer, jugador_id in self.jugadores:
            if writer != excluir:
                try:
                    writer.write(f"{mensaje}\n".encode())
                    await writer.drain()
                except:
                    pass
    
    async def enviar_a_jugador(self, writer, mensaje):
        try:
            writer.write(f"{mensaje}\n".encode())
            await writer.drain()
        except:
            pass
    
    async def manejar_turno(self, writer, jugador_id, reader):
        while self.turno_actual != jugador_id and not self.fin_juego:
            try:
                await asyncio.wait_for(self.event_turno.wait(), timeout=1.0)
                self.event_turno.clear()
            except asyncio.TimeoutError:
                pass
        
        if self.fin_juego:
            return
        
        estado_actual = ''.join(self.progreso)
        await self.enviar_a_jugador(writer, f"\n{'='*50}")
        await self.enviar_a_jugador(writer, f"🎮 ¡TU TURNO Jugador {jugador_id+1}!")
        await self.enviar_a_jugador(writer, f"📝 Palabra: {estado_actual}")
        await self.enviar_a_jugador(writer, f"❤️ Intentos restantes: {self.intentos_restantes}")
        await self.enviar_a_jugador(writer, f"❌ Letras falladas: {', '.join(self.falladas) if self.falladas else 'ninguna'}")
        await self.enviar_a_jugador(writer, "🔤 Ingresa una letra o la palabra completa: ")
        
        try:
            data = await asyncio.wait_for(reader.readline(), timeout=30.0)
            respuesta = data.decode().strip().upper()
        except asyncio.TimeoutError:
            await self.enviar_a_jugador(writer, "⏰ ¡TIEMPO AGOTADO! Pierdes un intento.")
            async with self.lock:
                self.intentos_restantes -= 1
            await self.broadcast(f"⚠️ Jugador {jugador_id+1} se quedó sin tiempo. Intentos restantes: {self.intentos_restantes}")
            await self.broadcast(f"📊 Estado actual: {''.join(self.progreso)}")
            return
        
        await self.procesar_respuesta(jugador_id, respuesta, writer)
        
        async with self.lock:
            self.turno_actual = (self.turno_actual + 1) % self.num_jugadores
        
        self.event_turno.set()
        await self.barrera.wait()
    
    async def procesar_respuesta(self, jugador_id, respuesta, writer):
        async with self.lock:
            if len(respuesta) == 1 and respuesta.isalpha():
                if respuesta in self.palabra:
                    for i, c in enumerate(self.palabra):
                        if c == respuesta:
                            self.progreso[i] = respuesta
                    mensaje = f"✅ ¡{respuesta} es correcta!"
                    await self.broadcast(mensaje)
                    await self.broadcast(f"📊 Estado actual: {''.join(self.progreso)}")
                    
                    if '_' not in self.progreso:
                        self.fin_juego = True
                        await self.broadcast(f"\n{'='*50}")
                        await self.broadcast(f"🎉 ¡VICTORIA! La palabra era {self.palabra}")
                        await self.broadcast(f"🏆 El Jugador {jugador_id+1} acertó la última letra")
                        await self.broadcast(f"{'='*50}")
                else:
                    self.intentos_restantes -= 1
                    self.falladas.append(respuesta)
                    mensaje = f"❌ {respuesta} no está en la palabra. Intentos restantes: {self.intentos_restantes}"
                    await self.broadcast(mensaje)
                    await self.broadcast(f"📊 Estado actual: {''.join(self.progreso)}")
                    
                    if self.intentos_restantes <= 0:
                        self.fin_juego = True
                        await self.broadcast(f"\n{'='*50}")
                        await self.broadcast(f"💀 ¡DERROTA! La palabra era {self.palabra}")
                        await self.broadcast(f"{'='*50}")
            
            elif len(respuesta) > 1:
                if respuesta == self.palabra:
                    self.fin_juego = True
                    await self.broadcast(f"\n{'='*50}")
                    await self.broadcast(f"🎉 ¡VICTORIA! {respuesta} es correcta")
                    await self.broadcast(f"🏆 El Jugador {jugador_id+1} adivinó la palabra completa")
                    await self.broadcast(f"{'='*50}")
                else:
                    self.intentos_restantes -= 2
                    await self.broadcast(f"❌ {respuesta} no es la palabra correcta. Intentos restantes: {self.intentos_restantes}")
                    await self.broadcast(f"📊 Estado actual: {''.join(self.progreso)}")
                    
                    if self.intentos_restantes <= 0:
                        self.fin_juego = True
                        await self.broadcast(f"\n{'='*50}")
                        await self.broadcast(f"💀 ¡DERROTA! La palabra era {self.palabra}")
                        await self.broadcast(f"{'='*50}")
    
    async def manejar_jugador(self, reader, writer):
        jugador_id = len(self.jugadores)
        addr = writer.get_extra_info('peername')
        self.jugadores.append((writer, jugador_id))
        print(f"✅ Jugador {jugador_id+1} conectado desde {addr}")
        
        await self.enviar_a_jugador(writer, f"\n{'='*50}")
        await self.enviar_a_jugador(writer, f"🎯 ¡Bienvenido Jugador {jugador_id+1}!")
        await self.enviar_a_jugador(writer, f"🎮 Partida con {self.num_jugadores} jugadores")
        await self.enviar_a_jugador(writer, f"📝 La palabra tiene {len(self.palabra)} letras")
        await self.enviar_a_jugador(writer, f"⏳ Esperando a que se unan {self.num_jugadores - len(self.jugadores)} jugador(es) más...")
        await self.enviar_a_jugador(writer, f"{'='*50}")
        
        if len(self.jugadores) == self.num_jugadores:
            self.barrera = asyncio.Barrier(self.num_jugadores)
            self.event_turno = asyncio.Event()
            self.lock = asyncio.Lock()
            self.falladas = []
            self.turno_actual = 0
            
            await self.broadcast(f"\n{'='*50}")
            await self.broadcast(f"🎮 ¡PARTIDA INICIADA con {self.num_jugadores} jugadores!")
            await self.broadcast(f"📝 Palabra oculta: {' '.join(self.progreso)}")
            await self.broadcast(f"🎲 Comienza el Jugador 1")
            await self.broadcast(f"{'='*50}\n")
            self.event_turno.set()
        
        while not self.fin_juego:
            await self.manejar_turno(writer, jugador_id, reader)
            await asyncio.sleep(0.1)
        
        await self.enviar_a_jugador(writer, "\n🏁 PARTIDA FINALIZADA")
        writer.close()
        await writer.wait_closed()
    
    async def iniciar(self):
        server = await asyncio.start_server(
            self.manejar_jugador, 
            self.host, 
            self.port
        )
        
        print(f"🚀 Servidor de Ahorcado Multijugador")
        print(f"📍 Corriendo en {self.host}:{self.port}")
        print(f"👥 Esperando {self.num_jugadores} jugadores...")
        print(f"{'='*50}\n")
        
        async with server:
            await server.serve_forever()

async def main():
    # Cambia num_jugadores según cuántos quieras (2, 3, 4...)
    servidor = AhorcadoServidorAsync(num_jugadores=3)
    await servidor.iniciar()

if __name__ == "__main__":
    asyncio.run(main())