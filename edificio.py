import threading
from queue import Queue

class Config:
    NUM_PLANTAS = 10
    NUM_ASCENSORES = 3
    CAPACIDAD_MAXIMA = 4
    TIEMPO_ENTRE_PLANTAS = 0.5
    TIEMPO_PUERTAS = 1.0

config = Config()

# Para avisar al planificador de que hay nuevas peticiones
cola_solicitudes = Queue()

# Personas esperando en cada planta (listas de objetos Solicitud)
personas_esperando = {} # Se inicializará cuando sepamos NUM_PLANTAS

lock_estado = threading.Lock()

def inicializar_edificio():
    global personas_esperando
    personas_esperando = {i: {'subiendo': [], 'bajando': []} for i in range(config.NUM_PLANTAS)}
