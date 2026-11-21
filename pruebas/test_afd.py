import unittest

from afd import acepta, clase, trazar
from rfc import rfc_sin_homoclave


class PruebasAFD(unittest.TestCase):
    def test_acepta_formatos_validos(self):
        for rfc in ("CUNG851103", "HELU000229", "PEDX951208", "PELJ900517"):
            with self.subTest(rfc=rfc):
                self.assertTrue(acepta(rfc))

    def test_rechaza_mes_fuera_de_rango(self):
        self.assertFalse(acepta("CUNG851303"))  # mes 13
        self.assertFalse(acepta("CUNG850003"))  # mes 00

    def test_rechaza_dia_fuera_de_rango(self):
        self.assertFalse(acepta("CUNG851132"))  # día 32
        self.assertFalse(acepta("CUNG851100"))  # día 00

    def test_rechaza_longitud_incorrecta(self):
        self.assertFalse(acepta("CUNG8511031"))  # sobra un carácter
        self.assertFalse(acepta("CUNG85110"))    # falta un carácter
        self.assertFalse(acepta(""))

    def test_rechaza_caracteres_fuera_del_alfabeto(self):
        self.assertFalse(acepta("cung851103"))   # minúsculas
        self.assertFalse(acepta("CUÑG851103"))   # Ñ no es letra del alfabeto
        self.assertFalse(acepta("CU1G851103"))   # dígito donde va una letra
        self.assertFalse(acepta("CUNGA51103"))   # letra donde va un dígito

    def test_limitacion_no_valida_dias_por_mes(self):
        # El AFD acepta fechas imposibles; eso le toca al análisis semántico.
        self.assertTrue(acepta("CUNG850230"))  # 30 de febrero
        self.assertTrue(acepta("CUNG850431"))  # 31 de abril

    def test_clase(self):
        self.assertEqual(clase("A"), "L")
        self.assertEqual(clase("2"), "2")
        self.assertEqual(clase("7"), "4-9")
        self.assertIsNone(clase("#"))

    def test_trazar(self):
        self.assertEqual(trazar("CUNG851103")[-1], "q13")
        self.assertEqual(trazar("CUNG851303")[-1], "muerto")

    def test_acepta_la_salida_del_generador(self):
        casos = [
            ("Juan", "Pérez", "López", 17, 5, 1990),
            ("María Guadalupe", "De la Cruz", "Núñez", 3, 11, 1985),
            ("José Luis", "Hernández", None, 29, 2, 2000),
            ("Óscar", "Pérez", "Díaz", 8, 12, 1995),
            ("Pedro", "Ñáñez", "Sosa", 15, 9, 2003),
        ]
        for caso in casos:
            with self.subTest(caso=caso):
                self.assertTrue(acepta(rfc_sin_homoclave(*caso)))


if __name__ == "__main__":
    unittest.main()
