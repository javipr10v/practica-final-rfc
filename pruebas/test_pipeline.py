"""Pruebas de extremo a extremo: cada archivo de pruebas/ contra su salida esperada."""

import unittest
from pathlib import Path

from main import procesar

CARPETA = Path(__file__).parent

ESPERADO = {
    # Casos válidos del documento (P1 a P5)
    "valido1.rfc": ["alumno1 -> PELJ900517   [AFD: ACEPTA]"],
    "valido2.rfc": ["alumno1 -> CUNG851103   [AFD: ACEPTA]"],
    "valido3.rfc": ["alumno1 -> HELU000229   [AFD: ACEPTA]"],
    "valido4.rfc": ["alumno1 -> PEDX951208   [AFD: ACEPTA]"],
    "valido5.rfc": ["alumno1 -> XASP030915   [AFD: ACEPTA]"],
    # Casos propios
    "propio_paterno_corto.rfc": ["alumno1 -> EMAN990101   [AFD: ACEPTA]"],
    "propio_particulas.rfc": ["alumno1 -> GAHJ921010   [AFD: ACEPTA]"],
    "propio_varios_registros.rfc": [
        "alumno1 -> PELJ900517   [AFD: ACEPTA]",
        "alumno2 -> CUNG851103   [AFD: ACEPTA]",
        "alumno3 -> HELU000229   [AFD: ACEPTA]",
    ],
    # Casos con error (E1 a E4)
    "error_lexico.rfc": ["Línea 4, columna 13: carácter inesperado '#'"],
    "error_sintactico.rfc": ["Línea 3: falta PYC, se esperaba ';' después de \"Juan\""],
    "error_fecha.rfc": ["Línea 5: fecha inválida 30/02/1998 (febrero de 1998 tiene 28 días)"],
    "error_sin_paterno.rfc": ["Registro 'alumno1': falta 'paterno'"],
    "error_duplicado.rfc": ["Línea 4: 'nombre' ya declarado (línea 3)"],
    "error_varios.rfc": [
        "Línea 3: 'Ju4n' contiene caracteres no válidos",
        "Línea 5: campo 'edad' desconocido",
        "Línea 6: fecha_nac espera FECHA, recibió CADENA",
        "Línea 8: 'alumno1' ya declarado (línea 2)",
        "Línea 10: fecha inválida 29/02/1999 (febrero de 1999 tiene 28 días)",
        "Registro 'alumno1': falta 'paterno'",
    ],
}


class PruebasPipeline(unittest.TestCase):
    def test_archivos_de_prueba(self):
        for nombre, esperado in ESPERADO.items():
            with self.subTest(archivo=nombre):
                fuente = (CARPETA / nombre).read_text(encoding="utf-8")
                salida, correcto = procesar(fuente)
                self.assertEqual(salida, esperado)
                self.assertEqual(correcto, not nombre.startswith("error_"))

    def test_no_falta_ningun_archivo_en_la_lista(self):
        en_disco = {p.name for p in CARPETA.glob("*.rfc")}
        self.assertEqual(en_disco, set(ESPERADO))


if __name__ == "__main__":
    unittest.main()
