# Informe Técnico: Simulador Concurrente de Ascensores

## 1. Descripción del Proyecto
Este proyecto es una simulación interactiva y en tiempo real del funcionamiento de una batería de ascensores dentro de un edificio. Permite configurar dinámicamente la cantidad de plantas, el número de ascensores y la capacidad máxima de cada cabina. El sistema recrea fielmente las restricciones del mundo real, incluyendo tiempos de apertura de puertas, tiempos de traslado entre plantas, y la lógica direccional a la hora de recoger a múltiples pasajeros. 

## 2. Qué problema resuelve
El sistema busca resolver el clásico problema de **enrutamiento y asignación de recursos** (Elevator Scheduling Problem), minimizando el tiempo medio de espera de los usuarios y optimizando los viajes. En lugar de procesar peticiones individualmente de origen a destino (comportamiento ineficiente), se emplea una variante del **algoritmo SCAN/LOOK**: el ascensor adopta un sentido de marcha, recoge a todos los pasajeros posibles en su ruta sin superar su capacidad máxima y solo invierte su dirección cuando no quedan peticiones en su trayectoria actual. 

## 3. Estructura del Proyecto
El software sigue una arquitectura modular separando claramente las responsabilidades:
- **`main.py`**: Punto de entrada del programa. Maneja la configuración inicial, inicializa los hilos y gestiona la interfaz interactiva REPL (Read-Eval-Print Loop) que permite comandos del usuario y renderiza la vista en arte ASCII.
- **`edificio.py`**: Almacena el estado global del sistema: la clase `Config`, las colas compartidas direccionales (listas de espera para subir/bajar por cada planta) y los bloqueos globales.
- **`ascensor.py`**: Contiene la clase `Ascensor` (hereda de `threading.Thread`). Maneja la lógica física y algorítmica individual (moverse, abrir puertas, embarcar pasajeros).
- **`planificador.py`**: Evalúa todas las solicitudes entrantes y decide cuál es el ascensor óptimo para la tarea basándose en distancia direccional.
- **`persona.py`**: Un hilo generador que actúa como "productor" creando peticiones aleatorias.
- **`estadisticas.py` / Logs**: Llevan un registro contable y un trazado silencioso de todos los eventos (`simulacion.log`) para evitar la saturación de la consola interactiva.

## 4. Técnicas de Concurrencia y Distribución
El simulador se basa fuertemente en el **modelo multihilo (Multithreading)** para lograr concurrencia. Al ser Python, se aprovecha este modelo no tanto para el cálculo paralelo intensivo (limitado por el GIL de Python), sino para la correcta simulación de procesos inherentemente asíncronos en el tiempo (I/O y temporizadores).

Las técnicas utilizadas son:
- **Hilos (`threading.Thread`)**: Cada entidad independiente (cada uno de los ascensores, el planificador y el generador de personas) es un hilo. Esto permite que el tiempo transcurra para cada ascensor de forma paralela respecto a la perspectiva del usuario. Un ascensor puede estar parado 1 segundo abriendo puertas (`time.sleep()`), sin bloquear al resto de ascensores que siguen moviéndose, ni al hilo principal que está esperando el `input()` del usuario.
- **Cerrojos o Exclusión Mutua (`threading.Lock`)**: Para evitar **condiciones de carrera (Race Conditions)**. Cuando un ascensor recoge pasajeros de la planta, o el usuario inyecta una nueva petición, varios hilos intentan modificar las listas compartidas de `personas_esperando` o el estado interno del ascensor. `lock_estado` y `lock_ascensor` garantizan operaciones atómicas de lectura/escritura en dichas estructuras, evitando la corrupción de memoria.
- **Colas Seguras (`queue.Queue`)**: Se emplea como canal de comunicación (Thread-safe) implementando el patrón Productor-Consumidor. El hilo generador y el hilo principal introducen solicitudes en la cola, y el planificador las extrae secuencialmente para procesarlas sin perder ninguna solicitud cruzada.
- **Señalización por Eventos (`threading.Event`)**: En lugar de hacer *Busy Waiting* (bucles `while True` iterando sin fin, lo cual satura la CPU), los ascensores inactivos entran en estado suspendido llamando a `evento.wait()`. Cuando el planificador les asigna una nueva planta, dispara `evento.set()`, despertando al hilo instantáneamente. Esta técnica de sincronización garantiza alta eficiencia de recursos.

### Por qué usamos Concurrencia
La concurrencia es **obligatoria** para esta simulación. Si el programa fuera secuencial puro, un simple comando como trasladar el ascensor de la planta 0 a la 10 (con sus respectivos `time.sleep()`) bloquearía la ejecución entera; no podríamos registrar nuevas llamadas en otros pisos ni mover otro ascensor hasta que el primero haya completado su recorrido íntegro.

## 5. Análisis de Rendimiento: Secuencial vs Concurrente
Imaginemos una situación con 3 ascensores y 5 peticiones simultáneas, donde cada piso tarda 0.5s en recorrerse y las puertas tardan 1.0s en gestionarse.
- **Versión Secuencial**: El único hilo de ejecución tendría que procesar las peticiones en serie. Para un viaje promedio de 5s, procesar 5 viajes independientes tardaría aprox. 25s. El programa "se congela" durante ese tiempo. No admite entradas.
- **Versión Concurrente (actual)**: Los 3 ascensores se mueven simultáneamente. El tiempo que percibe el usuario es casi igual al viaje más largo (aprox 5s a 7s), logrando un factor de mejora del rendimiento del 300% al 400%. Además, la interfaz principal responde a los comandos del usuario con latencia cero (inmediatamente), ya que la espera física ocurre en el contexto local de cada hilo derivado.

## 6. Problemas Encontrados y Solución
Durante el desarrollo se experimentó un bloqueo grave provocado por una falla de referencias compartidas (una excepción de tipo `KeyError`).
**Problema**: Al inicializar las variables dinámicas de la simulación desde el menú, el método `inicializar_edificio()` creaba y asignaba un *nuevo diccionario* (`{}`) a la variable global `personas_esperando`. Sin embargo, debido al ciclo de importaciones de Python, los hilos de los ascensores ya poseían una referencia apuntando a la dirección de memoria original del diccionario, el cual había quedado obsoleto y vacío. Al intentar buscar a las personas de la planta 6, estallaba con `KeyError: 6`.
**Solución**: Se eliminó la reasignación destructiva. En lugar de reescribir la variable global apuntando a otro objeto en memoria, se solucionó aplicando la técnica de mutación *in-place*: ejecutando `personas_esperando.clear()` y rellenando nuevamente las claves del mismo objeto, garantizando que todos los hilos interactuaran con el mismo espacio de memoria compartido.

## 7. Instrucciones de Ejecución
### Requisitos
El proyecto requiere **Python 3.6 o superior** utilizando exclusivamente bibliotecas del núcleo estándar de Python (Standard Library), por lo que **no se necesitan dependencias externas** (`pip install`).

### Ejecución
1. Abre tu consola y navega al directorio del proyecto.
2. Ejecuta el archivo principal:
   ```bash
   python main.py
   ```
3. El programa solicitará el número de plantas, ascensores y capacidad. Presiona `Enter` para usar las opciones recomendadas por defecto.

### Comandos de la Interfaz (REPL)
- `auto on` / `auto off`: Enciende o apaga el hilo generador de personas aleatorias.
- `[origen] [destino]`: (Ej: `2 9`) Introduce manualmente una persona que quiere viajar de la planta 2 a la 9.
- `estado`: Dibuja un esquema completo del edificio por consola (mostrando pasajeros y sentido de la marcha de los ascensores `^` y `v`).
- `salir`: Termina los procesos elegantemente e imprime el compendio de las estadísticas finales.

## 8. Ejemplos de Ejecución (Logs e Interfaz)

### Interfaz del Edificio (comando `estado`)
```text
==================================================
              ESTADO DEL EDIFICIO               
==================================================
P09: [     ] [     ] [     ] 
P08: [     ] [A1:v1] [     ] 
P07: [     ] [     ] [A2:^3] 
P06: [     ] [     ] [     ] 
P05: [A0:^2] [     ] [     ] 
P04: [     ] [     ] [     ] 
P03: [     ] [     ] [     ] 
P02: [     ] [     ] [     ] 
P01: [     ] [     ] [     ] 
P00: [     ] [     ] [     ] 
==================================================
```
*(Se observa al Ascensor 1 bajando con 1 pasajero y al Ascensor 2 subiendo completamente cargado).*

### Trazabilidad de Eventos (`simulacion.log`)
```text
2026-05-07 22:54:00,268 [INFO] Persona solicita manual: 4 -> 5
2026-05-07 22:54:00,268 [INFO] Planificador asigna ascensor 0 a planta 4
2026-05-07 22:54:01,769 [INFO] Ascensor 0 abre puertas en planta 4
2026-05-07 22:54:02,769 [INFO] Ascensor 0: pasajero sube en 4 con destino 5
2026-05-07 22:54:03,270 [INFO] Ascensor 0 abre puertas en planta 5
2026-05-07 22:54:04,271 [INFO] Ascensor 0: pasajero baja en 5
```
