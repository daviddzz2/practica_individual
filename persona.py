import random
import time
import threading
from edificio import cola_solicitudes, NUM_PLANTAS
from estadisticas import registrar_solicitud


class Solicitud:
    def __init__(self, origen, destino):
        self.origen = origen
        self.destino = destino
        self.timestamp = time.time()


class GeneradorPersonas(threading.Thread):
    def run(self):
        while True:
            origen = random.randint(0, NUM_PLANTAS - 1)
            destino = random.randint(0, NUM_PLANTAS - 1)
            if origen != destino:
                s = Solicitud(origen, destino)
                cola_solicitudes.put(s)
                registrar_solicitud()
                print(f"Persona solicita: {origen} -> {destino}")
            time.sleep(random.uniform(0.5, 2))
