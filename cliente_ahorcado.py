import asyncio
import sys

class ClienteAhorcadoAsync:
    async def jugar(self, host='localhost', port=8888):
        try:
            reader, writer = await asyncio.open_connection(host, port)
            print("✅ Conectado al servidor del ahorcado")
            print("💡 Escribe 'salir' para abandonar la partida\n")
            
            while True:
                try:
                    data = await asyncio.wait_for(reader.readline(), timeout=60.0)
                    if not data:
                        break
                    
                    mensaje = data.decode().strip()
                    print(mensaje)
                    
                    if "TU TURNO" in mensaje or "Ingresa una letra" in mensaje or "tu turno" in mensaje.lower():
                        respuesta = await asyncio.get_event_loop().run_in_executor(None, input, ">>> ")
                        
                        if respuesta.lower() == 'salir':
                            print("👋 Saliendo de la partida...")
                            writer.write(b"salir\n")
                            await writer.drain()
                            break
                        
                        writer.write(f"{respuesta}\n".encode())
                        await writer.drain()
                    
                    if "VICTORIA" in mensaje or "DERROTA" in mensaje:
                        print("\n🏁 Partida terminada. Presiona Enter para salir...")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Servidor inactivo...")
                    break
                    
        except ConnectionRefusedError:
            print("❌ No se pudo conectar al servidor. ¿Está el servidor ejecutándose?")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

async def main():
    # Cambia el host/port si el servidor está en otra máquina
    cliente = ClienteAhorcadoAsync()
    await cliente.jugar()

if __name__ == "__main__":
    asyncio.run(main())