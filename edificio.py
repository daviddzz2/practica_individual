import threading
from queue import Queue

NUM_PLANTAS = 17
NUM_ASCENSORES = 4

TIEMPO_ENTRE_PLANTAS = 0.5
TIEMPO_PUERTAS = 1.0

# Locks: exclusión por planta (recurso crítico)
locks_plantas = [threading.Lock() for _ in range(NUM_PLANTAS)]

# Cola global de solicitudes
cola_solicitudes = Queue()

# Lock para estado global compartido
lock_estado = threading.Lock()
