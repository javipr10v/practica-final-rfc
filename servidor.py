"""Interfaz web local para RFCLang (extra opcional, no sustituye a main.py).

Levanta un servidor en 127.0.0.1 con la biblioteca estándar y abre el
navegador. Toda la lógica sigue estando en los módulos del compilador;
aquí solo se exponen sus resultados por fase.

Uso:
    python servidor.py [--puerto 8000] [--sin-navegador]
"""

import argparse
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from afd import acepta, trazar
from lexer import tokenizar
from main import rfc_del_ambito
from parser import formatear_ast, parsear
from semantico import analizar, formatear_tabla

RAIZ = Path(__file__).parent
LIMITE_BYTES = 100_000
FASES = ("lexico", "sintactico", "semantico", "generador")


def analizar_fuente(fuente: str) -> dict:
    """Ejecuta el pipeline y devuelve el resultado de cada fase."""
    respuesta = {
        "fases": {fase: "pendiente" for fase in FASES},
        "fase_con_error": None,
        "errores": [],
        "tokens": [],
        "ast": [],
        "simbolos": [],
        "resultados": [],
    }
    fases = respuesta["fases"]

    def fallar(fase: str, errores: list[str]) -> dict:
        fases[fase] = "error"
        respuesta["fase_con_error"] = fase
        respuesta["errores"] = errores
        for posterior in FASES[FASES.index(fase) + 1:]:
            fases[posterior] = "omitida"
        return respuesta

    tokens, errores = tokenizar(fuente)
    respuesta["tokens"] = [
        {"linea": t.linea, "columna": t.columna, "tipo": t.tipo, "lexema": t.lexema}
        for t in tokens
    ]
    if errores:
        return fallar("lexico", errores)
    fases["lexico"] = "ok"

    programa, errores = parsear(tokens)
    if programa.registros:
        respuesta["ast"] = formatear_ast(programa)
    if errores:
        return fallar("sintactico", errores)
    fases["sintactico"] = "ok"

    tabla, errores = analizar(programa)
    respuesta["simbolos"] = formatear_tabla(tabla)
    if errores:
        return fallar("semantico", errores)
    fases["semantico"] = "ok"

    for ambito in tabla.ambitos.values():
        rfc = rfc_del_ambito(ambito)
        respuesta["resultados"].append({
            "id": ambito.nombre,
            "rfc": rfc,
            "acepta": acepta(rfc),
            "traza": trazar(rfc),
        })
    fases["generador"] = "ok"
    return respuesta


def probar_afd(cadena: str) -> dict:
    """Pasa una cadena cualquiera por el AFD y devuelve su recorrido."""
    cadena = cadena[:60]
    return {"cadena": cadena, "acepta": acepta(cadena), "traza": trazar(cadena)}


def leer_ejemplos() -> list[dict]:
    carpeta = RAIZ / "pruebas"
    return [
        {"nombre": archivo.name, "contenido": archivo.read_text(encoding="utf-8-sig")}
        for archivo in sorted(carpeta.glob("*.rfc"))
    ]


class Manejador(BaseHTTPRequestHandler):
    def _responder(self, codigo: int, tipo: str, cuerpo: bytes) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, datos, codigo: int = 200) -> None:
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self._responder(codigo, "application/json; charset=utf-8", cuerpo)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            pagina = (RAIZ / "web" / "index.html").read_bytes()
            self._responder(200, "text/html; charset=utf-8", pagina)
        elif self.path == "/ejemplos":
            self._json(leer_ejemplos())
        else:
            self._json({"error": "no encontrado"}, 404)

    def do_POST(self):
        largo = int(self.headers.get("Content-Length") or 0)
        if largo > LIMITE_BYTES:
            self._json({"error": "entrada demasiado grande"}, 413)
            return
        try:
            datos = json.loads(self.rfile.read(largo) or b"{}")
        except json.JSONDecodeError:
            self._json({"error": "JSON inválido"}, 400)
            return

        if self.path == "/analizar":
            self._json(analizar_fuente(str(datos.get("fuente", ""))))
        elif self.path == "/afd":
            self._json(probar_afd(str(datos.get("cadena", ""))))
        else:
            self._json({"error": "no encontrado"}, 404)

    def log_message(self, formato, *args):
        pass  # consola limpia durante la demo


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Interfaz web local de RFCLang")
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--sin-navegador", action="store_true", help="no abrir el navegador")
    args = ap.parse_args(argv)

    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", args.puerto), Manejador)
    except OSError:
        print(f"No se pudo usar el puerto {args.puerto}. Prueba con --puerto 8001")
        return 1

    url = f"http://127.0.0.1:{args.puerto}"
    print(f"RFCLang disponible en {url}  (Ctrl+C para salir)")
    if not args.sin_navegador:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
