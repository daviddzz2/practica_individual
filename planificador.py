import threading
from edificio import cola_solicitudes, lock_estado


class Planificador(threading.Thread):
    def __init__(self, ascensores):
        super().__init__(daemon=True)
        self.ascensores = ascensores

    def mejor_ascensor(self, origen):
        with lock_estado:
            return min(self.ascensores, key=lambda a: abs(a.planta_actual - origen))

    def run(self):
        while True:
            solicitud = cola_solicitudes.get()
            ascensor = self.mejor_ascensor(solicitud.origen)
            print(
                f"Planificador asigna {solicitud.origen}->{solicitud.destino} al ascensor {ascensor.id}"
            )
            ascensor.asignar_parada(solicitud.origen)
            ascensor.asignar_parada(solicitud.destino, solicitud)
