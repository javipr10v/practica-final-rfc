import datetime
import unittest

from lexer import tokenizar
from parser import parsear
from semantico import analizar, es_bisiesto, validar_fecha

HOY = datetime.date(2026, 11, 12)


def revisar(fuente):
    tokens, _ = tokenizar(fuente)
    programa, _ = parsear(tokens)
    return analizar(programa, HOY)


def registro(nombre='"Juan"', paterno='"Pérez"', fecha="17/05/1990", extra="", id="alumno1"):
    return (f'persona {id} {{\n nombre = {nombre};\n paterno = {paterno};\n'
            f' fecha_nac = {fecha};\n{extra}}}\n')


class PruebasSemantico(unittest.TestCase):
    def test_programa_valido_sin_errores(self):
        tabla, errores = revisar(registro(extra=' materno = "López";\n'))
        self.assertEqual(errores, [])
        simbolos = tabla.buscar_ambito("alumno1").simbolos
        self.assertEqual(simbolos["fecha_nac"].valor, (17, 5, 1990))
        self.assertEqual(simbolos["nombre"].valor, "JUAN")

    def test_s1_campo_repetido(self):
        _, errores = revisar(registro(extra=' nombre = "Otro";\n'))
        self.assertEqual(errores, ["Línea 5: 'nombre' ya declarado (línea 2)"])

    def test_s2_campo_desconocido(self):
        _, errores = revisar(registro(extra=' edad = "veinte";\n'))
        self.assertEqual(errores, ["Línea 5: campo 'edad' desconocido"])

    def test_s3_tipo_incorrecto(self):
        _, errores = revisar(registro(fecha='"17/05/1990"'))
        self.assertEqual(errores, ["Línea 4: fecha_nac espera FECHA, recibió CADENA"])
        _, errores = revisar(registro(nombre="17/05/1990"))
        self.assertEqual(errores, ["Línea 2: nombre espera CADENA, recibió FECHA"])

    def test_s4_campos_obligatorios(self):
        _, errores = revisar('persona alumno1 {\n nombre = "Juan";\n}')
        self.assertEqual(errores, [
            "Registro 'alumno1': falta 'paterno'",
            "Registro 'alumno1': falta 'fecha_nac'",
        ])

    def test_s4_materno_es_opcional(self):
        _, errores = revisar(registro())
        self.assertEqual(errores, [])

    def test_s5_caracteres_no_validos(self):
        _, errores = revisar(registro(nombre='"Ju4n"'))
        self.assertEqual(errores, ["Línea 2: 'Ju4n' contiene caracteres no válidos"])

    def test_s5_cadena_vacia(self):
        _, errores = revisar(registro(paterno='""'))
        self.assertEqual(errores, ["Línea 3: paterno no puede estar vacío"])

    def test_s5_acepta_acentos_apostrofo_guion_y_punto(self):
        _, errores = revisar(registro(nombre='"Ana-Lucía"', paterno="\"O'Connor Jr.\""))
        self.assertEqual(errores, [])

    def test_s6_febrero_no_bisiesto(self):
        _, errores = revisar(registro(fecha="30/02/1998"))
        self.assertEqual(errores, ["Línea 4: fecha inválida 30/02/1998 (febrero de 1998 tiene 28 días)"])

    def test_s6_anios_bisiestos(self):
        self.assertTrue(es_bisiesto(2000))
        self.assertFalse(es_bisiesto(1900))
        self.assertTrue(es_bisiesto(2024))
        self.assertIsNone(validar_fecha("29/02/2000", HOY)[1])
        self.assertIsNotNone(validar_fecha("29/02/1900", HOY)[1])
        self.assertIsNotNone(validar_fecha("29/02/2001", HOY)[1])

    def test_s6_mes_y_dia_fuera_de_rango(self):
        self.assertIn("mes 13", validar_fecha("10/13/1990", HOY)[1])
        self.assertIn("día 0", validar_fecha("00/05/1990", HOY)[1])
        self.assertIn("30 días", validar_fecha("31/04/1990", HOY)[1])

    def test_s6_anio_minimo_y_fecha_futura(self):
        self.assertIn("anterior a 1900", validar_fecha("01/01/1899", HOY)[1])
        self.assertIn("futura", validar_fecha("13/11/2026", HOY)[1])
        self.assertIsNone(validar_fecha("12/11/2026", HOY)[1])

    def test_s7_registro_repetido(self):
        _, errores = revisar(registro() + registro())
        self.assertEqual(errores, ["Línea 6: 'alumno1' ya declarado (línea 1)"])

    def test_acumula_todos_los_errores(self):
        fuente = registro(nombre='"Ju4n"', fecha="30/02/1998", extra=' edad = "x";\n')
        _, errores = revisar(fuente)
        self.assertEqual(len(errores), 3)

    def test_decora_el_ast(self):
        tokens, _ = tokenizar(registro(paterno='"De la Cruz"'))
        programa, _ = parsear(tokens)
        analizar(programa, HOY)
        valores = {c.nombre: c.valor.normalizado for c in programa.registros[0].campos}
        self.assertEqual(valores["paterno"], "DE LA CRUZ")


if __name__ == "__main__":
    unittest.main()
