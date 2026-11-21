"""Analizador léxico de RFCLang.

Convierte el texto fuente en una lista de tokens con línea y columna.
Los errores léxicos no detienen el análisis: se acumulan y se devuelven
junto con los tokens.
"""

import re
from dataclasses import dataclass

PALABRAS_RESERVADAS = {"persona"}

# El orden es la prioridad: gana la primera alternativa que coincide.
ESPECIFICACION = [
    ("COMENTARIO", r"//[^\n]*"),
    ("FECHA", r"[0-9]{2}/[0-9]{2}/[0-9]{4}"),
    ("CADENA", r'"[^"\n]*"'),
    ("CADENA_ABIERTA", r'"[^"\n]*'),   # comilla sin cierre en la misma línea
    ("ID", r"[A-Za-z_]\w*"),
    ("ASIGNA", r"="),
    ("PYC", r";"),
    ("LLAVE_IZQ", r"\{"),
    ("LLAVE_DER", r"\}"),
    ("SALTO", r"\n"),
    ("ESPACIO", r"[ \t\r]+"),           # \r para archivos con saltos de Windows
    ("ERROR", r"."),
]

PATRON = re.compile("|".join(f"(?P<{nombre}>{patron})" for nombre, patron in ESPECIFICACION))


@dataclass(frozen=True)
class Token:
    tipo: str
    lexema: str
    linea: int
    columna: int


def tokenizar(fuente: str) -> tuple[list[Token], list[str]]:
    """Devuelve (tokens, errores léxicos). La lista de tokens termina en EOF."""
    tokens: list[Token] = []
    errores: list[str] = []
    linea = 1
    inicio_linea = 0  # posición donde empieza la línea actual

    for coincidencia in PATRON.finditer(fuente):
        tipo = coincidencia.lastgroup
        lexema = coincidencia.group()
        columna = coincidencia.start() - inicio_linea + 1

        if tipo == "SALTO":
            linea += 1
            inicio_linea = coincidencia.end()
        elif tipo in ("COMENTARIO", "ESPACIO"):
            continue
        elif tipo == "ERROR":
            errores.append(f"Línea {linea}, columna {columna}: carácter inesperado {lexema!r}")
        elif tipo == "CADENA_ABIERTA":
            errores.append(f"Línea {linea}, columna {columna}: cadena sin cerrar {lexema}")
        else:
            if tipo == "ID" and lexema in PALABRAS_RESERVADAS:
                tipo = "PALABRA_RESERVADA"
            tokens.append(Token(tipo, lexema, linea, columna))

    tokens.append(Token("EOF", "", linea, len(fuente) - inicio_linea + 1))
    return tokens, errores


def formatear_tokens(tokens: list[Token]) -> list[str]:
    """Tabla de tokens lista para imprimir."""
    lineas = [f"{'LÍN:COL':<9} {'TOKEN':<18} LEXEMA"]
    for t in tokens:
        lineas.append(f"{f'{t.linea}:{t.columna}':<9} {t.tipo:<18} {t.lexema!r}")
    return lineas
