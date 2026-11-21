# Práctica final integradora: generador del RFC sin homoclave

Procesador de **RFCLang**, un lenguaje pequeño que describe personas físicas.
Analiza el archivo (léxico, sintáctico y semántico), calcula las 10 primeras
posiciones del RFC (4 letras + AAMMDD) y valida el resultado con un autómata
finito determinista.

Materia: Compiladores · Universidad Autónoma de Chiapas

## Requisitos

- Python 3.10 o superior
- Solo biblioteca estándar (no hay nada que instalar)

## Cómo ejecutar

Desde la carpeta del proyecto:

```
python main.py pruebas/valido2.rfc
alumno1 -> CUNG851103   [AFD: ACEPTA]

python main.py pruebas/error_fecha.rfc
Línea 5: fecha inválida 30/02/1998 (febrero de 1998 tiene 28 días)
```

Opciones para ver el trabajo de cada fase:

```
python main.py pruebas/valido2.rfc --tokens     # salida del analizador léxico
python main.py pruebas/valido2.rfc --ast        # árbol de sintaxis
python main.py pruebas/valido2.rfc --simbolos   # tabla de símbolos
```

En Windows, si `python` no funciona, usar `py`.

## Pruebas

```
python -m unittest pruebas.test_rfc pruebas.test_afd pruebas.test_lexer pruebas.test_parser pruebas.test_semantico pruebas.test_pipeline pruebas.test_servidor -v
```

Los archivos `.rfc` de `pruebas/` son los casos del documento (P1 a P5 y E1 a E4)
más los casos propios del equipo. `test_pipeline.py` verifica la salida
esperada de cada uno.

## Interfaz web local (extra opcional)

Además de la línea de comandos, hay una interfaz en el navegador para la
demostración. Es un complemento: el alcance de la práctica es la línea de
comandos, y la web solo reutiliza los mismos módulos.

```
python servidor.py
```

Abre `http://127.0.0.1:8000` en el navegador (si no se abre solo). El servidor
escucha únicamente en la propia computadora y usa solo la biblioteca estándar.
Opciones: `--puerto 8001` si el 8000 está ocupado y `--sin-navegador`.
Ctrl+C para detenerlo.

La página muestra el estado de cada fase, el RFC con el veredicto del AFD,
errores por fase, los tokens, el AST, la tabla de símbolos y el recorrido del
autómata estado por estado, con un probador de cadenas para el AFD.

## Estructura

```
practica_final_rfc/
├── lexer.py        análisis léxico (tokens con línea y columna)
├── parser.py       análisis sintáctico LL(1) por descenso recursivo y AST
├── semantico.py    tabla de símbolos y reglas S1 a S7
├── rfc.py          generador del RFC (reglas R1 a R8)
├── afd.py          autómata que valida el formato del RFC
├── main.py         une todas las fases
├── servidor.py     interfaz web local (opcional)
├── web/            página de la interfaz web
├── datos/          lista de palabras inconvenientes (sección 5.5)
├── pruebas/        archivos .rfc y pruebas unitarias
└── docs/           gramática, FIRST/FOLLOW y diseño del AFD
```

La carpeta `datos/` debe viajar junto con el código: `rfc.py` lee de ahí
la lista de palabras inconvenientes.

## Decisiones de diseño

- **Errores acumulados.** Cada fase devuelve todos sus errores en lugar de
  detenerse en el primero. Si una fase tiene errores, el procesamiento termina
  ahí y no se genera ningún RFC.
- **Modo pánico en el parser.** Tras un error se descartan tokens hasta un
  token de sincronía (`;`, `}` o `persona`) y se continúa. Un `;` omitido se
  informa y se sigue como si estuviera.
- **Ñ antes de NFD.** En la normalización la Ñ se cambia por X antes de quitar
  acentos; si no, quedaría como N.
- **Paterno corto sin materno.** Se aplica R6, porque R5 necesita la inicial
  del materno.
- **Apellido formado solo por partículas.** Se conserva la última palabra.
- **Guiones, puntos y apóstrofos** se eliminan sin dejar espacio
  (`Pérez-Gil` pasa a `PEREZGIL`).
- **AFD con tabla explícita.** Valida formato y rangos (mes 01-12, día 01-31).
  Los días por mes y los años bisiestos los valida la fase semántica.
- La lista de palabras inconvenientes vive en un archivo externo para separar
  los datos de la lógica.

> El algoritmo es una versión didáctica. Para uso oficial debe consultarse
> la documentación vigente del SAT.
