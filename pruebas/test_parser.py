import unittest

from lexer import tokenizar
from parser import formatear_ast, parsear


def analizar_sintaxis(fuente):
    tokens, _ = tokenizar(fuente)
    return parsear(tokens)


VALIDO = '''persona alumno1 {
    nombre = "María Guadalupe";
    paterno = "De la Cruz";
    fecha_nac = 03/11/1985;
}
'''


class PruebasParser(unittest.TestCase):
    def test_construye_el_ast_del_ejemplo(self):
        programa, errores = analizar_sintaxis(VALIDO)
        self.assertEqual(errores, [])
        self.assertEqual(len(programa.registros), 1)
        registro = programa.registros[0]
        self.assertEqual(registro.id, "alumno1")
        self.assertEqual([c.nombre for c in registro.campos], ["nombre", "paterno", "fecha_nac"])
        self.assertEqual(registro.campos[0].valor.texto, "María Guadalupe")
        self.assertEqual(registro.campos[2].valor.tipo, "FECHA")

    def test_varios_registros(self):
        programa, errores = analizar_sintaxis(VALIDO + VALIDO.replace("alumno1", "alumno2"))
        self.assertEqual(errores, [])
        self.assertEqual([r.id for r in programa.registros], ["alumno1", "alumno2"])

    def test_falta_punto_y_coma(self):
        _, errores = analizar_sintaxis('persona a {\n nombre = "Juan"\n}')
        self.assertEqual(len(errores), 1)
        self.assertTrue(errores[0].startswith("Línea 2: falta PYC"))

    def test_falta_igual(self):
        _, errores = analizar_sintaxis('persona a {\n nombre "Juan";\n}')
        self.assertEqual(len(errores), 1)
        self.assertIn("se esperaba '=' (ASIGNA)", errores[0])

    def test_falta_llave_de_cierre(self):
        _, errores = analizar_sintaxis('persona a {\n nombre = "Juan";\n')
        self.assertEqual(len(errores), 1)
        self.assertIn("'}'", errores[0])

    def test_registro_sin_campos(self):
        _, errores = analizar_sintaxis("persona a { }")
        self.assertEqual(len(errores), 1)
        self.assertIn("identificador", errores[0])

    def test_programa_vacio(self):
        _, errores = analizar_sintaxis("// nada\n")
        self.assertEqual(len(errores), 1)
        self.assertIn("vacío", errores[0])

    def test_modo_panico_reporta_varios_errores(self):
        fuente = (
            'persona a {\n nombre "Juan";\n paterno = ;\n}\n'
            'persona b {\n nombre = "Ana"\n fecha_nac = 01/01/2000;\n}\n'
        )
        programa, errores = analizar_sintaxis(fuente)
        self.assertEqual(len(errores), 3)
        # tras recuperarse, el segundo registro sí queda en el AST
        self.assertEqual([r.id for r in programa.registros], ["a", "b"])

    def test_texto_basura_entre_registros(self):
        programa, errores = analizar_sintaxis(VALIDO + "basura basura\n" + VALIDO.replace("alumno1", "alumno2"))
        self.assertEqual(len(errores), 1)
        self.assertEqual(len(programa.registros), 2)

    def test_formato_del_ast(self):
        programa, _ = analizar_sintaxis(VALIDO)
        lineas = formatear_ast(programa)
        self.assertEqual(lineas[0], "Programa")
        self.assertIn("Registro alumno1", lineas[1])
        self.assertTrue(lineas[-1].endswith("[FECHA]"))


if __name__ == "__main__":
    unittest.main()
