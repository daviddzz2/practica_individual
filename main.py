import time
from ascensor import Ascensor
from planificador import Planificador
from persona import GeneradorPersonas
from estadisticas import imprimir_estadisticas
from edificio import NUM_ASCENSORES

SIMULACION_SEGUNDOS = 60


def main():
    ascensores = [Ascensor(i) for i in range(NUM_ASCENSORES)]

    for a in ascensores:
        a.start()

    planificador = Planificador(ascensores)
    planificador.start()

    generador = GeneradorPersonas()
    generador.daemon = True
    generador.start()

    time.sleep(SIMULACION_SEGUNDOS)
    imprimir_estadisticas()


if __name__ == "__main__":
    main()
