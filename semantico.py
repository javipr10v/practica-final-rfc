"""Análisis semántico de RFCLang: tabla de símbolos y reglas S1 a S7.

Recorre el AST, valida el significado del programa y decora cada valor
con su forma normalizada. No se detiene en el primer error: los acumula
todos y los devuelve juntos.
"""

import datetime
import re
from dataclasses import dataclass, field

from parser import Programa, Registro
from rfc import normalizar

TIPOS_CAMPO = {
    "nombre": "CADENA",
    "paterno": "CADENA",
    "materno": "CADENA",
    "fecha_nac": "FECHA",
}
OBLIGATORIOS = ("nombre", "paterno", "fecha_nac")
ANIO_MINIMO = 1900

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

# Letras (con acentos, Ñ y Ü), espacios, guion, punto y apóstrofo.
CARACTERES_VALIDOS = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ .'\-]+")


# ------------------------------------------------------ tabla de símbolos

@dataclass
class Simbolo:
    nombre: str
    tipo: str
    valor: object      # texto normalizado, (dia, mes, anio) o None si es inválido
    linea: int


@dataclass
class Ambito:
    """Un registro 'persona' y los campos que declara."""
    nombre: str
    linea: int
    simbolos: dict[str, Simbolo] = field(default_factory=dict)

    def declarar(self, simbolo: Simbolo) -> Simbolo | None:
        """Registra el símbolo. Si ya existía, devuelve el anterior."""
        previo = self.simbolos.get(simbolo.nombre)
        if previo is None:
            self.simbolos[simbolo.nombre] = simbolo
        return previo


class TablaSimbolos:
    def __init__(self):
        self.ambitos: dict[str, Ambito] = {}

    def agregar(self, ambito: Ambito) -> None:
        self.ambitos[ambito.nombre] = ambito

    def buscar_ambito(self, nombre: str) -> Ambito | None:
        return self.ambitos.get(nombre)


# ------------------------------------------------------------ validaciones

def es_bisiesto(anio: int) -> bool:
    return anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0)


def dias_del_mes(mes: int, anio: int) -> int:
    if mes == 2:
        return 29 if es_bisiesto(anio) else 28
    return 30 if mes in (4, 6, 9, 11) else 31


def validar_fecha(texto: str, hoy: datetime.date) -> tuple[tuple[int, int, int] | None, str | None]:
    """S6. Devuelve ((dia, mes, anio), None) o (None, motivo del error)."""
    dia, mes, anio = (int(parte) for parte in texto.split("/"))

    if not 1 <= mes <= 12:
        return None, f"el mes {mes} no existe"
    if dia < 1:
        return None, f"el día {dia} no existe"
    maximo = dias_del_mes(mes, anio)
    if dia > maximo:
        return None, f"{MESES[mes - 1]} de {anio} tiene {maximo} días"
    if anio < ANIO_MINIMO:
        return None, f"el año {anio} es anterior a {ANIO_MINIMO}"
    if datetime.date(anio, mes, dia) > hoy:
        return None, "la fecha es futura"
    return (dia, mes, anio), None


def validar_cadena(nombre_campo: str, texto: str) -> str | None:
    """S5. Devuelve el motivo del error o None si la cadena es válida."""
    if not texto.strip():
        return f"{nombre_campo} no puede estar vacío"
    if not CARACTERES_VALIDOS.fullmatch(texto):
        return f"'{texto}' contiene caracteres no válidos"
    if not normalizar(texto):
        return f"'{texto}' no contiene letras"
    return None


# ----------------------------------------------------------------- análisis

def analizar(programa: Programa, hoy: datetime.date | None = None) -> tuple[TablaSimbolos, list[str]]:
    """Devuelve (tabla de símbolos, errores semánticos)."""
    hoy = hoy or datetime.date.today()
    tabla = TablaSimbolos()
    errores: list[str] = []
    for registro in programa.registros:
        _analizar_registro(registro, tabla, errores, hoy)
    return tabla, errores


def _analizar_registro(registro: Registro, tabla: TablaSimbolos,
                       errores: list[str], hoy: datetime.date) -> None:
    ambito = Ambito(registro.id, registro.linea)

    # S7: identificador único. El cuerpo se revisa igual para reportar todo.
    previo = tabla.buscar_ambito(registro.id)
    if previo is not None:
        errores.append(f"Línea {registro.linea}: '{registro.id}' ya declarado (línea {previo.linea})")
    else:
        tabla.agregar(ambito)

    for campo in registro.campos:
        esperado = TIPOS_CAMPO.get(campo.nombre)

        # S2: solo campos conocidos
        if esperado is None:
            errores.append(f"Línea {campo.linea}: campo '{campo.nombre}' desconocido")
            continue

        # S1: sin campos repetidos
        simbolo = Simbolo(campo.nombre, campo.valor.tipo, None, campo.linea)
        anterior = ambito.declarar(simbolo)
        if anterior is not None:
            errores.append(f"Línea {campo.linea}: '{campo.nombre}' ya declarado (línea {anterior.linea})")
            continue

        # S3: tipo del valor
        valor = campo.valor
        if valor.tipo != esperado:
            errores.append(f"Línea {campo.linea}: {campo.nombre} espera {esperado}, recibió {valor.tipo}")
            continue

        if esperado == "CADENA":
            motivo = validar_cadena(campo.nombre, valor.texto)         # S5
            normalizado = " ".join(normalizar(valor.texto)) if motivo is None else None
        else:
            normalizado, motivo = validar_fecha(valor.texto, hoy)      # S6

        if motivo is not None:
            if esperado == "FECHA":
                errores.append(f"Línea {campo.linea}: fecha inválida {valor.texto} ({motivo})")
            else:
                errores.append(f"Línea {campo.linea}: {motivo}")
        valor.normalizado = normalizado
        simbolo.valor = normalizado

    # S4: campos obligatorios
    for obligatorio in OBLIGATORIOS:
        if obligatorio not in ambito.simbolos:
            errores.append(f"Registro '{registro.id}': falta '{obligatorio}'")


def _texto_valor(valor: object) -> str:
    if valor is None:
        return "(inválido)"
    if isinstance(valor, tuple):
        dia, mes, anio = valor
        return f"{dia:02d}/{mes:02d}/{anio:04d}"
    return str(valor)


def formatear_tabla(tabla: TablaSimbolos) -> list[str]:
    """Tabla de símbolos lista para imprimir."""
    lineas = []
    for ambito in tabla.ambitos.values():
        lineas.append(f"Ámbito {ambito.nombre} (línea {ambito.linea})")
        for s in ambito.simbolos.values():
            lineas.append(f"  {s.nombre:<10} {s.tipo:<7} {_texto_valor(s.valor):<18} línea {s.linea}")
    return lineas
