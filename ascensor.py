import threading
import time
from queue import Queue, Empty
from edificio import locks_plantas, TIEMPO_ENTRE_PLANTAS, TIEMPO_PUERTAS
from estadisticas import registrar_atencion


class Ascensor(threading.Thread):
    def __init__(self, id_ascensor):
        super().__init__(daemon=True)
        self.id = id_ascensor
        self.planta_actual = 0
        self.paradas = Queue()
        self.evento = threading.Event()

    def asignar_parada(self, planta, solicitud=None):
        self.paradas.put((planta, solicitud))
        self.evento.set()

    def mover(self, destino):
        while self.planta_actual != destino:
            siguiente = self.planta_actual + (1 if destino > self.planta_actual else -1)
            locks_plantas[siguiente].acquire()
            locks_plantas[self.planta_actual].release()
            self.planta_actual = siguiente
            print(f"Ascensor {self.id} en planta {self.planta_actual}")
            time.sleep(TIEMPO_ENTRE_PLANTAS)

    def run(self):
        locks_plantas[self.planta_actual].acquire()

        while True:
            try:
                destino, solicitud = self.paradas.get(timeout=1)
                self.mover(destino)
                print(f"Ascensor {self.id} abre puertas en {self.planta_actual}")
                if solicitud:
                    registrar_atencion(solicitud.timestamp)
                time.sleep(TIEMPO_PUERTAS)
            except Empty:
                self.evento.clear()
                self.evento.wait()
