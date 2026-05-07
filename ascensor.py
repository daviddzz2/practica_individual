import threading
import time
import logging
from edificio import config, personas_esperando, lock_estado
from estadisticas import registrar_atencion


class Ascensor(threading.Thread):
    def __init__(self, id_ascensor):
        super().__init__(daemon=True)
        self.id = id_ascensor
        self.planta_actual = 0
        self.direccion = 0  # 1 subiendo, -1 bajando, 0 parado
        self.destinos = set()
        self.pasajeros = []  # lista de objetos Solicitud
        self.evento = threading.Event()
        self.lock_ascensor = threading.Lock()

    def asignar_parada(self, planta):
        with self.lock_ascensor:
            self.destinos.add(planta)
            if self.direccion == 0:
                self.direccion = 1 if planta > self.planta_actual else -1
        self.evento.set()

    def _parar_en_planta(self):
        logging.info(f"Ascensor {self.id} abre puertas en planta {self.planta_actual}")
        time.sleep(config.TIEMPO_PUERTAS)

        with lock_estado:
            # 1. Bajar pasajeros
            bajan = [p for p in self.pasajeros if p.destino == self.planta_actual]
            for p in bajan:
                self.pasajeros.remove(p)
                logging.info(f"Ascensor {self.id}: pasajero baja en {self.planta_actual}")

            with self.lock_ascensor:
                if self.planta_actual in self.destinos:
                    self.destinos.remove(self.planta_actual)

            # 2. Subir pasajeros
            dir_str = 'subiendo' if self.direccion == 1 else 'bajando'
            if self.direccion == 0:
                dir_str = None

            if dir_str:
                esperando = personas_esperando[self.planta_actual][dir_str]
                while esperando and len(self.pasajeros) < config.CAPACIDAD_MAXIMA:
                    solicitud = esperando.pop(0)
                    self.pasajeros.append(solicitud)
                    registrar_atencion(solicitud.timestamp)
                    with self.lock_ascensor:
                        self.destinos.add(solicitud.destino)
                    logging.info(f"Ascensor {self.id}: pasajero sube en {self.planta_actual} con destino {solicitud.destino}")

    def run(self):
        while True:
            self.evento.wait()

            with self.lock_ascensor:
                if not self.destinos and not self.pasajeros:
                    self.direccion = 0
                    self.evento.clear()
                    continue

                # Invertir dirección si no hay destinos más adelante
                if self.direccion == 1 and not any(d >= self.planta_actual for d in self.destinos):
                    self.direccion = -1
                elif self.direccion == -1 and not any(d <= self.planta_actual for d in self.destinos):
                    self.direccion = 1

                # Extremos
                if self.planta_actual == config.NUM_PLANTAS - 1 and self.direccion == 1:
                    self.direccion = -1
                elif self.planta_actual == 0 and self.direccion == -1:
                    self.direccion = 1

            if self.direccion != 0:
                with self.lock_ascensor:
                    debe_parar = self.planta_actual in self.destinos
                
                if debe_parar:
                    self._parar_en_planta()
                    
                with self.lock_ascensor:
                    if not self.destinos and not self.pasajeros:
                        self.direccion = 0
                        self.evento.clear()
                        continue
                
                self.planta_actual += self.direccion
                logging.debug(f"Ascensor {self.id} pasando por {self.planta_actual}")
                time.sleep(config.TIEMPO_ENTRE_PLANTAS)
