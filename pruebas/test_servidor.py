import unittest

from servidor import analizar_fuente, leer_ejemplos, probar_afd

VALIDO = '''persona alumno1 {
    nombre = "María Guadalupe";
    paterno = "De la Cruz";
    materno = "Núñez";
    fecha_nac = 03/11/1985;
}
'''


class PruebasServidor(unittest.TestCase):
    def test_programa_valido(self):
        d = analizar_fuente(VALIDO)
        self.assertEqual(set(d["fases"].values()), {"ok"})
        self.assertEqual(d["resultados"][0]["rfc"], "CUNG851103")
        self.assertTrue(d["resultados"][0]["acepta"])
        self.assertEqual(d["resultados"][0]["traza"][-1], "q13")

    def test_error_lexico_omite_las_fases_siguientes(self):
        d = analizar_fuente("persona a { # }")
        self.assertEqual(d["fase_con_error"], "lexico")
        self.assertEqual(d["fases"]["lexico"], "error")
        self.assertEqual(d["fases"]["sintactico"], "omitida")
        self.assertTrue(d["tokens"])  # los tokens se siguen mostrando

    def test_error_semantico_conserva_ast_y_simbolos(self):
        d = analizar_fuente(VALIDO.replace("03/11/1985", "30/02/1998"))
        self.assertEqual(d["fase_con_error"], "semantico")
        self.assertEqual(d["fases"]["sintactico"], "ok")
        self.assertTrue(d["ast"])
        self.assertTrue(d["simbolos"])
        self.assertEqual(d["resultados"], [])

    def test_probar_afd(self):
        self.assertTrue(probar_afd("CUNG850230")["acepta"])
        self.assertFalse(probar_afd("CUNG851303")["acepta"])

    def test_ejemplos_disponibles(self):
        nombres = {e["nombre"] for e in leer_ejemplos()}
        self.assertIn("valido2.rfc", nombres)


if __name__ == "__main__":
    unittest.main()
