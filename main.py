"""Procesador de RFCLang: genera el RFC sin homoclave y lo valida con un AFD.

Uso:
    python main.py archivo.rfc [--tokens] [--ast] [--simbolos]
"""

import argparse
import sys
from pathlib import Path

from afd import acepta
from lexer import formatear_tokens, tokenizar
from parser import formatear_ast, parsear
from rfc import rfc_sin_homoclave
from semantico import Ambito, analizar, formatear_tabla


def rfc_del_ambito(ambito: Ambito) -> str:
    s = ambito.simbolos
    dia, mes, anio = s["fecha_nac"].valor
    materno = s["materno"].valor if "materno" in s else None
    return rfc_sin_homoclave(s["nombre"].valor, s["paterno"].valor, materno, dia, mes, anio)


def procesar(fuente: str, mostrar_tokens: bool = False, mostrar_ast: bool = False,
             mostrar_simbolos: bool = False) -> tuple[list[str], bool]:
    """Ejecuta todo el pipeline. Devuelve (líneas de salida, ¿sin errores?)."""
    salida: list[str] = []

    tokens, errores = tokenizar(fuente)
    if mostrar_tokens:
        salida += formatear_tokens(tokens)
    if errores:
        return salida + errores, False

    programa, errores = parsear(tokens)
    if mostrar_ast and programa.registros:
        salida += formatear_ast(programa)
    if errores:
        return salida + errores, False

    tabla, errores = analizar(programa)
    if mostrar_simbolos:
        salida += formatear_tabla(tabla)
    if errores:
        return salida + errores, False

    for ambito in tabla.ambitos.values():
        rfc = rfc_del_ambito(ambito)
        veredicto = "ACEPTA" if acepta(rfc) else "RECHAZA"
        salida.append(f"{ambito.nombre} -> {rfc}   [AFD: {veredicto}]")
    return salida, True


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="Generador del RFC sin homoclave a partir de RFCLang")
    ap.add_argument("archivo", help="archivo .rfc a procesar")
    ap.add_argument("--tokens", action="store_true", help="muestra los tokens")
    ap.add_argument("--ast", action="store_true", help="muestra el árbol de sintaxis")
    ap.add_argument("--simbolos", action="store_true", help="muestra la tabla de símbolos")
    args = ap.parse_args(argv)

    try:
        fuente = Path(args.archivo).read_text(encoding="utf-8-sig")
    except OSError as error:
        print(f"No se pudo leer '{args.archivo}': {error.strerror}")
        return 2

    salida, correcto = procesar(fuente, args.tokens, args.ast, args.simbolos)
    print("\n".join(salida))
    return 0 if correcto else 1


if __name__ == "__main__":
    sys.exit(main())
