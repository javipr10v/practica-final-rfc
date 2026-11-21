"""AFD que reconoce el formato del RFC sin homoclave: LLLL AAMMDD.

Alfabeto (clases de entrada):
    L    letra mayúscula A-Z
    0, 1, 2, 3    dígitos individuales
    4-9  dígitos del 4 al 9

Estados:
    q0-q4   cuatro letras
    q5-q6   año (dos dígitos)
    q7-q8   primer dígito del mes (0 o 1)
    q9      mes completo (01-12)
    q10-q12 primer dígito del día (0, 1-2 o 3)
    q13     RFC completo, único estado de aceptación

Lo que no aparece en DELTA va a un estado muerto implícito (rechazo).
El AFD solo revisa rangos (mes 01-12, día 01-31); que febrero tenga 28
o 29 días ya lo valida el análisis semántico.
"""

ESTADO_INICIAL = "q0"
ACEPTACION = {"q13"}

# (estado, clase) -> estado
DELTA: dict[tuple[str, str], str] = {
    # cuatro letras
    ("q0", "L"): "q1",
    ("q1", "L"): "q2",
    ("q2", "L"): "q3",
    ("q3", "L"): "q4",
    # año: cualquier dígito, dos veces
    ("q4", "0"): "q5", ("q4", "1"): "q5", ("q4", "2"): "q5",
    ("q4", "3"): "q5", ("q4", "4-9"): "q5",
    ("q5", "0"): "q6", ("q5", "1"): "q6", ("q5", "2"): "q6",
    ("q5", "3"): "q6", ("q5", "4-9"): "q6",
    # mes: 01-09 o 10-12
    ("q6", "0"): "q7",
    ("q6", "1"): "q8",
    ("q7", "1"): "q9", ("q7", "2"): "q9", ("q7", "3"): "q9", ("q7", "4-9"): "q9",
    ("q8", "0"): "q9", ("q8", "1"): "q9", ("q8", "2"): "q9",
    # día: 01-09, 10-29 o 30-31
    ("q9", "0"): "q10",
    ("q9", "1"): "q11", ("q9", "2"): "q11",
    ("q9", "3"): "q12",
    ("q10", "1"): "q13", ("q10", "2"): "q13", ("q10", "3"): "q13", ("q10", "4-9"): "q13",
    ("q11", "0"): "q13", ("q11", "1"): "q13", ("q11", "2"): "q13",
    ("q11", "3"): "q13", ("q11", "4-9"): "q13",
    ("q12", "0"): "q13", ("q12", "1"): "q13",
}


def clase(c: str) -> str | None:
    """Clase de entrada del carácter, o None si no pertenece al alfabeto."""
    if "A" <= c <= "Z":
        return "L"
    if c in "0123":
        return c
    if c in "456789":
        return "4-9"
    return None


def trazar(cadena: str) -> list[str]:
    """Estados que recorre el autómata. Termina en 'muerto' si rechaza antes."""
    estado = ESTADO_INICIAL
    recorrido = [estado]
    for c in cadena:
        siguiente = DELTA.get((estado, clase(c)))
        if siguiente is None:
            recorrido.append("muerto")
            return recorrido
        estado = siguiente
        recorrido.append(estado)
    return recorrido


def acepta(cadena: str) -> bool:
    """True si la cadena completa lleva al autómata a un estado de aceptación."""
    return trazar(cadena)[-1] in ACEPTACION
