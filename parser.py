"""Analizador sintáctico de RFCLang (descenso recursivo LL(1)).

Gramática (EBNF):
    programa → registro+ EOF
    registro → 'persona' ID '{' campo+ '}'
    campo    → ID '=' valor ';'
    valor    → CADENA | FECHA

Cada regla es un método. Los errores se acumulan y el parser se recupera
con modo pánico: descarta tokens hasta uno de sincronía y continúa.
"""

from dataclasses import dataclass

from lexer import Token


# ---------------------------------------------------------------- AST

@dataclass
class Valor:
    tipo: str            # "CADENA" o "FECHA"
    texto: str           # sin comillas en el caso de las cadenas
    linea: int
    columna: int
    normalizado: object = None   # lo decora el análisis semántico


@dataclass
class Campo:
    nombre: str
    valor: Valor
    linea: int
    columna: int


@dataclass
class Registro:
    id: str
    campos: list[Campo]
    linea: int


@dataclass
class Programa:
    registros: list[Registro]


# ------------------------------------------------------------- Parser

DESCRIPCION = {
    "PALABRA_RESERVADA": "'persona' (PALABRA_RESERVADA)",
    "ID": "un identificador (ID)",
    "ASIGNA": "'=' (ASIGNA)",
    "PYC": "';' (PYC)",
    "LLAVE_IZQ": "'{' (LLAVE_IZQ)",
    "LLAVE_DER": "'}' (LLAVE_DER)",
}

# Tokens en los que el parser retoma el análisis tras un error dentro de un campo.
SINCRONIA_CAMPO = {"PYC", "LLAVE_DER", "PALABRA_RESERVADA", "EOF"}


class ErrorSintactico(Exception):
    """Señal interna para activar la recuperación; el mensaje ya quedó registrado."""


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errores: list[str] = []

    # --- utilidades -------------------------------------------------

    @property
    def actual(self) -> Token:
        return self.tokens[self.pos]

    def _anterior(self) -> Token:
        return self.tokens[max(self.pos - 1, 0)]

    def _avanzar(self) -> Token:
        token = self.tokens[self.pos]
        if token.tipo != "EOF":
            self.pos += 1
        return token

    @staticmethod
    def _describir(token: Token) -> str:
        return "fin de archivo" if token.tipo == "EOF" else f"'{token.lexema}'"

    def _registrar_esperado(self, descripcion: str) -> None:
        t = self.actual
        self.errores.append(
            f"Línea {t.linea}, columna {t.columna}: se esperaba {descripcion} "
            f"y se encontró {self._describir(t)}"
        )

    def _fallar(self, descripcion: str) -> None:
        self._registrar_esperado(descripcion)
        raise ErrorSintactico

    def _consumir(self, tipo: str) -> Token:
        if self.actual.tipo == tipo:
            return self._avanzar()
        self._fallar(DESCRIPCION[tipo])

    def _saltar_hasta(self, sincronia: set[str]) -> None:
        while self.actual.tipo != "EOF" and self.actual.tipo not in sincronia:
            self._avanzar()

    # --- reglas de la gramática ------------------------------------

    def programa(self) -> Programa:
        registros = []
        if self.actual.tipo == "EOF":
            self.errores.append(
                f"Línea {self.actual.linea}: el programa está vacío, "
                "se esperaba al menos un registro 'persona'"
            )
        while self.actual.tipo != "EOF":
            if self.actual.tipo == "PALABRA_RESERVADA":
                registro = self.registro()
                if registro is not None:
                    registros.append(registro)
            else:
                self._registrar_esperado(DESCRIPCION["PALABRA_RESERVADA"])
                self._saltar_hasta({"PALABRA_RESERVADA"})
        return Programa(registros)

    def registro(self) -> Registro | None:
        self._consumir("PALABRA_RESERVADA")

        id_token = None
        try:
            id_token = self._consumir("ID")
        except ErrorSintactico:
            pass  # seguimos si viene la llave, para revisar el cuerpo
        try:
            self._consumir("LLAVE_IZQ")
        except ErrorSintactico:
            self._recuperar_registro()
            return None

        campos = []
        primero = True                      # campo+ : al menos uno
        while primero or self.actual.tipo == "ID":
            primero = False
            try:
                campos.append(self.campo())
            except ErrorSintactico:
                self._recuperar_campo()

        try:
            self._consumir("LLAVE_DER")
        except ErrorSintactico:
            self._recuperar_registro()

        if id_token is None:
            return None
        return Registro(id_token.lexema, campos, id_token.linea)

    def campo(self) -> Campo:
        nombre = self._consumir("ID")
        self._consumir("ASIGNA")
        valor = self.valor()
        if self.actual.tipo == "PYC":
            self._avanzar()
        else:
            # Se informa y se sigue como si el ';' estuviera, para no
            # perder el resto del registro por un solo olvido.
            ultimo = self._anterior()
            self.errores.append(
                f"Línea {ultimo.linea}: falta PYC, se esperaba ';' después de {ultimo.lexema}"
            )
        return Campo(nombre.lexema, valor, nombre.linea, nombre.columna)

    def valor(self) -> Valor:
        if self.actual.tipo in ("CADENA", "FECHA"):
            t = self._avanzar()
            texto = t.lexema[1:-1] if t.tipo == "CADENA" else t.lexema
            return Valor(t.tipo, texto, t.linea, t.columna)
        self._fallar("una cadena o una fecha (CADENA | FECHA)")

    # --- recuperación (modo pánico) --------------------------------

    def _recuperar_campo(self) -> None:
        self._saltar_hasta(SINCRONIA_CAMPO)
        if self.actual.tipo == "PYC":
            self._avanzar()

    def _recuperar_registro(self) -> None:
        self._saltar_hasta({"LLAVE_DER", "PALABRA_RESERVADA"})
        if self.actual.tipo == "LLAVE_DER":
            self._avanzar()


def parsear(tokens: list[Token]) -> tuple[Programa, list[str]]:
    """Devuelve (AST, errores sintácticos)."""
    parser = Parser(tokens)
    programa = parser.programa()
    return programa, parser.errores


def formatear_ast(programa: Programa) -> list[str]:
    """Árbol de sintaxis abstracta listo para imprimir."""
    lineas = ["Programa"]
    total = len(programa.registros)
    for i, registro in enumerate(programa.registros):
        ultimo_registro = i == total - 1
        rama = "└── " if ultimo_registro else "├── "
        sangria = "    " if ultimo_registro else "│   "
        lineas.append(f"{rama}Registro {registro.id} (línea {registro.linea})")
        for j, campo in enumerate(registro.campos):
            rama_campo = "└── " if j == len(registro.campos) - 1 else "├── "
            valor = f'"{campo.valor.texto}"' if campo.valor.tipo == "CADENA" else campo.valor.texto
            lineas.append(f"{sangria}{rama_campo}Campo {campo.nombre} = {valor} [{campo.valor.tipo}]")
    return lineas
