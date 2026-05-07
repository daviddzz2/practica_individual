import threading
import logging
from edificio import config, cola_solicitudes, lock_estado


class Planificador(threading.Thread):
    def __init__(self, ascensores):
        super().__init__(daemon=True)
        self.ascensores = ascensores

    def mejor_ascensor(self, origen, destino):
        direccion_solicitud = 1 if destino > origen else -1
        mejor = None
        min_distancia = float('inf')

        for a in self.ascensores:
            with a.lock_ascensor:
                distancia = abs(a.planta_actual - origen)
                
                if a.direccion == 0:
                    score = distancia
                elif a.direccion == direccion_solicitud:
                    if (a.direccion == 1 and a.planta_actual <= origen) or \
                       (a.direccion == -1 and a.planta_actual >= origen):
                        score = distancia
                    else:
                        score = distancia + config.NUM_PLANTAS * 2
                else:
                    score = distancia + config.NUM_PLANTAS
                    
                if score < min_distancia:
                    min_distancia = score
                    mejor = a
        return mejor

    def run(self):
        while True:
            solicitud = cola_solicitudes.get()
            ascensor = self.mejor_ascensor(solicitud.origen, solicitud.destino)
            if ascensor:
                logging.info(f"Planificador asigna ascensor {ascensor.id} a planta {solicitud.origen}")
                ascensor.asignar_parada(solicitud.origen)
