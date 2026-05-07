import time
import os
import sys
import logging
from ascensor import Ascensor
from planificador import Planificador
from persona import GeneradorPersonas, generar_solicitud_manual, generacion_activa
from estadisticas import imprimir_estadisticas
from edificio import config, inicializar_edificio

def configurar_logging():
    logging.basicConfig(
        filename='simulacion.log',
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        filemode='w'
    )
    # Reducimos los logs de threading si los hay
    logging.getLogger().setLevel(logging.INFO)

def dibujar_edificio(ascensores):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 50)
    print(" ESTADO DEL EDIFICIO ".center(50, " "))
    print("=" * 50)
    
    for planta in range(config.NUM_PLANTAS - 1, -1, -1):
        linea = f"P{planta:02d}: "
        for a in ascensores:
            with a.lock_ascensor:
                if a.planta_actual == planta:
                    dir_char = "^" if a.direccion == 1 else "v" if a.direccion == -1 else "-"
                    pax = len(a.pasajeros)
                    linea += f"[A{a.id}:{dir_char}{pax}] "
                else:
                    linea += "[     ] "
        print(linea)
    print("=" * 50)

def main():
    configurar_logging()
    print("Bienvenido al Simulador Avanzado de Ascensores")
    try:
        plantas_input = input(f"Número de plantas (Enter para {config.NUM_PLANTAS}): ")
        if plantas_input.strip(): config.NUM_PLANTAS = int(plantas_input)
        
        asc_input = input(f"Número de ascensores (Enter para {config.NUM_ASCENSORES}): ")
        if asc_input.strip(): config.NUM_ASCENSORES = int(asc_input)
        
        cap_input = input(f"Capacidad máxima (Enter para {config.CAPACIDAD_MAXIMA}): ")
        if cap_input.strip(): config.CAPACIDAD_MAXIMA = int(cap_input)
    except ValueError:
        print("Entrada inválida. Usando valores por defecto.")
        
    inicializar_edificio()

    ascensores = [Ascensor(i) for i in range(config.NUM_ASCENSORES)]
    for a in ascensores:
        a.start()

    planificador = Planificador(ascensores)
    planificador.start()

    generador = GeneradorPersonas()
    generador.daemon = True
    generador.start()
    
    print("\nSimulación iniciada. Usa 'auto on' para iniciar el generador de personas.")
    print("Comandos: 'origen destino' (ej. 3 8), 'estado', 'auto on', 'auto off', 'salir'")
    
    while True:
        try:
            cmd = input("> ").strip().lower()
            if cmd == "salir" or cmd == "exit":
                break
            elif cmd == "estado":
                dibujar_edificio(ascensores)
            elif cmd == "auto on":
                generacion_activa.set()
                print("Generador automático ACTIVADO.")
            elif cmd == "auto off":
                generacion_activa.clear()
                print("Generador automático DESACTIVADO.")
            else:
                partes = cmd.split()
                if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
                    origen = int(partes[0])
                    destino = int(partes[1])
                    if 0 <= origen < config.NUM_PLANTAS and 0 <= destino < config.NUM_PLANTAS and origen != destino:
                        generar_solicitud_manual(origen, destino)
                        print(f"Solicitud manual enviada: {origen} -> {destino}")
                    else:
                        print(f"Plantas inválidas. Deben estar entre 0 y {config.NUM_PLANTAS - 1}.")
                elif cmd:
                    print("Comando no reconocido.")
        except Exception as e:
            print(f"Error procesando comando: {e}")
        except KeyboardInterrupt:
            break

    print("\nFinalizando simulación...")
    imprimir_estadisticas()
    print("Consulta 'simulacion.log' para ver el historial detallado de eventos.")

if __name__ == "__main__":
    main()
