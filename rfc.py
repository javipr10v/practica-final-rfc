"""Generador de las 10 primeras posiciones del RFC de una persona física.

Implementa las reglas R1 a R8 de la práctica (versión didáctica del
algoritmo del SAT). La homoclave y el dígito verificador quedan fuera.
"""

import unicodedata
from pathlib import Path

PARTICULAS = {
    "DA", "DAS", "DE", "DEL", "DER", "DI", "DIE", "DD", "EL", "LA", "LOS",
    "LAS", "LE", "LES", "MAC", "MC", "VAN", "VON", "Y",
}

# Primeros nombres que se ignoran cuando el nombre es compuesto (R3).
OMITIBLES = {"JOSE", "MARIA", "MA", "J"}


def _cargar_inconvenientes() -> frozenset[str]:
    """Lee la lista de la sección 5.5 desde datos/inconvenientes.txt."""
    ruta = Path(__file__).parent / "datos" / "inconvenientes.txt"
    return frozenset(ruta.read_text(encoding="utf-8").split())


INCONVENIENTES = _cargar_inconvenientes()

VOCALES = "AEIOU"


def normalizar(texto: str) -> list[str]:
    """R1: mayúsculas, sin acentos, Ñ -> X y sin signos. Devuelve palabras."""
    # La Ñ se cambia antes de descomponer; si no, NFD la convertiría en N.
    texto = texto.upper().replace("Ñ", "X")
    descompuesto = unicodedata.normalize("NFD", texto)
    sin_marcas = "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
    # Guiones, puntos y apóstrofos se eliminan (no se sustituyen por espacio).
    limpio = "".join(c for c in sin_marcas if c.isalpha() or c.isspace())
    return limpio.split()


def quitar_particulas(palabras: list[str]) -> list[str]:
    """R2: elimina partículas de un apellido, dejando al menos una palabra."""
    restantes = [p for p in palabras if p not in PARTICULAS]
    return restantes if restantes else palabras[-1:]


def elegir_nombre(palabras: list[str]) -> str:
    """R3: en nombres compuestos se omite JOSE, MARIA, MA o J al inicio."""
    if len(palabras) > 1 and palabras[0] in OMITIBLES:
        return palabras[1]
    return palabras[0]


def primera_vocal_interna(palabra: str) -> str:
    """Primera vocal después de la letra inicial; 'X' si no hay."""
    for letra in palabra[1:]:
        if letra in VOCALES:
            return letra
    return "X"


def _primeras(palabra: str, cantidad: int) -> str:
    """Primeras letras de la palabra, completando con 'X' si faltan."""
    return palabra[:cantidad].ljust(cantidad, "X")


def rfc_sin_homoclave(nombre: str, paterno: str, materno: str | None,
                      dia: int, mes: int, anio: int) -> str:
    """Calcula las 10 primeras posiciones del RFC (4 letras + AAMMDD)."""
    palabras_nombre = normalizar(nombre)
    palabras_paterno = quitar_particulas(normalizar(paterno))
    palabras_materno = quitar_particulas(normalizar(materno)) if materno else []

    if not palabras_nombre or not palabras_paterno:
        raise ValueError("El nombre y el apellido paterno no pueden estar vacíos")

    nom = elegir_nombre(palabras_nombre)
    pat = palabras_paterno[0]
    mat = palabras_materno[0] if palabras_materno else ""

    if not mat:
        # R6. También cubre el paterno corto sin materno, ya que R5 requiere
        # la inicial del materno.
        letras = _primeras(pat, 2) + _primeras(nom, 2)
    elif len(pat) <= 2:
        # R5
        letras = pat[0] + mat[0] + _primeras(nom, 2)
    else:
        # R4
        letras = pat[0] + primera_vocal_interna(pat) + mat[0] + nom[0]

    # R7
    if letras in INCONVENIENTES:
        letras = letras[:3] + "X"

    # R8
    return f"{letras}{anio % 100:02d}{mes:02d}{dia:02d}"
