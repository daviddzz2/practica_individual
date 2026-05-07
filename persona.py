import random
import time
import threading
import logging
from edificio import config, cola_solicitudes, personas_esperando, lock_estado
from estadisticas import registrar_solicitud

# Evento para pausar/reanudar la generación de personas
generacion_activa = threading.Event()

class Solicitud:
    def __init__(self, origen, destino):
        self.origen = origen
        self.destino = destino
        self.timestamp = time.time()
        self.direccion = 'subiendo' if destino > origen else 'bajando'


class GeneradorPersonas(threading.Thread):
    def run(self):
        while True:
            generacion_activa.wait() # Se detiene si el evento está "cleared"
            origen = random.randint(0, config.NUM_PLANTAS - 1)
            destino = random.randint(0, config.NUM_PLANTAS - 1)
            if origen != destino:
                s = Solicitud(origen, destino)
                
                try:
                    with lock_estado:
                        personas_esperando[origen][s.direccion].append(s)
                except KeyError as e:
                    logging.error(f"KeyError in personas_esperando: {e}, origen={origen}, NUM_PLANTAS={config.NUM_PLANTAS}")
                    continue
                
                cola_solicitudes.put(s)
                registrar_solicitud()
                logging.info(f"Persona solicita automático: {origen} -> {destino}")
                if abs(origen - destino) == 1:
                    logging.info(f"🤖 ¡ERES UN VAGO, USA LAS ESCALERAS! (automático de {origen} a {destino})")
            time.sleep(random.uniform(0.5, 3))

def generar_solicitud_manual(origen, destino):
    s = Solicitud(origen, destino)
    try:
        with lock_estado:
            personas_esperando[origen][s.direccion].append(s)
    except KeyError as e:
        logging.error(f"KeyError in personas_esperando: {e}, origen={origen}, NUM_PLANTAS={config.NUM_PLANTAS}")
        return
    cola_solicitudes.put(s)
    registrar_solicitud()
    logging.info(f"Persona solicita manual: {origen} -> {destino}")
    if abs(origen - destino) == 1:
        logging.info(f"🤖 ¡ERES UN VAGO, USA LAS ESCALERAS! (manual de {origen} a {destino})")
