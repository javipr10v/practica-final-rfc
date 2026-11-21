import unittest

from lexer import tokenizar

EJEMPLO = '''// Registro de ejemplo
persona alumno1 {
    nombre = "María Guadalupe";
    fecha_nac = 03/11/1985;
}
'''


def tipos(fuente):
    tokens, _ = tokenizar(fuente)
    return [t.tipo for t in tokens]


class PruebasLexer(unittest.TestCase):
    def test_tokens_del_ejemplo_base(self):
        esperado = [
            "PALABRA_RESERVADA", "ID", "LLAVE_IZQ",
            "ID", "ASIGNA", "CADENA", "PYC",
            "ID", "ASIGNA", "FECHA", "PYC",
            "LLAVE_DER", "EOF",
        ]
        self.assertEqual(tipos(EJEMPLO), esperado)

    def test_descarta_comentarios_y_espacios(self):
        self.assertEqual(tipos("// solo un comentario\n   \t\n"), ["EOF"])

    def test_reclasifica_palabra_reservada(self):
        tokens, _ = tokenizar("persona personas")
        self.assertEqual([t.tipo for t in tokens[:2]], ["PALABRA_RESERVADA", "ID"])

    def test_linea_y_columna(self):
        tokens, _ = tokenizar(EJEMPLO)
        persona = tokens[0]
        self.assertEqual((persona.linea, persona.columna), (2, 1))
        fecha = next(t for t in tokens if t.tipo == "FECHA")
        self.assertEqual((fecha.linea, fecha.columna), (4, 17))

    def test_fecha_y_cadena_conservan_su_lexema(self):
        tokens, _ = tokenizar('"De la Cruz" 03/11/1985')
        self.assertEqual([t.lexema for t in tokens[:2]], ['"De la Cruz"', "03/11/1985"])

    def test_error_lexico_con_linea_y_columna(self):
        tokens, errores = tokenizar('persona a {\n  x # y\n}')
        self.assertEqual(errores, ["Línea 2, columna 5: carácter inesperado '#'"])
        # el análisis continúa después del error
        self.assertEqual(tokens[-1].tipo, "EOF")
        self.assertIn("LLAVE_DER", [t.tipo for t in tokens])

    def test_simbolo_dentro_de_cadena_no_es_error(self):
        _, errores = tokenizar('"a # b"')
        self.assertEqual(errores, [])

    def test_cadena_sin_cerrar(self):
        _, errores = tokenizar('nombre = "Juan;')
        self.assertEqual(len(errores), 1)
        self.assertIn("cadena sin cerrar", errores[0])

    def test_saltos_de_linea_de_windows(self):
        tokens, errores = tokenizar("persona a {\r\n}\r\n")
        self.assertEqual(errores, [])
        self.assertEqual(tokens[-2].linea, 2)

    def test_acumula_varios_errores(self):
        _, errores = tokenizar("@ $ %")
        self.assertEqual(len(errores), 3)


if __name__ == "__main__":
    unittest.main()
