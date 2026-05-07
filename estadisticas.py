import threading
import time

lock_stats = threading.Lock()

estadisticas = {
    "solicitudes_totales": 0,
    "solicitudes_atendidas": 0,
    "tiempo_espera_total": 0.0,
}


def registrar_solicitud():
    with lock_stats:
        estadisticas["solicitudes_totales"] += 1


def registrar_atencion(timestamp):
    with lock_stats:
        estadisticas["solicitudes_atendidas"] += 1
        estadisticas["tiempo_espera_total"] += time.time() - timestamp


def imprimir_estadisticas():
    with lock_stats:
        print("\n" + "="*40)
        print("          ESTADÍSTICAS FINALES          ")
        print("="*40)
        print(f" Solicitudes totales:   {estadisticas['solicitudes_totales']}")
        print(f" Solicitudes atendidas: {estadisticas['solicitudes_atendidas']}")
        if estadisticas["solicitudes_atendidas"] > 0:
            media = estadisticas["tiempo_espera_total"] / estadisticas["solicitudes_atendidas"]
            print(f" Tiempo medio espera:   {media:.2f}s")
        print("="*40 + "\n")
