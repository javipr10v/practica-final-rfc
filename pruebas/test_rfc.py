import unittest

from rfc import (INCONVENIENTES, normalizar, primera_vocal_interna,
                 quitar_particulas, rfc_sin_homoclave)


class PruebasNormalizacion(unittest.TestCase):
    def test_acentos_y_enie(self):
        self.assertEqual(normalizar("Núñez"), ["NUXEZ"])
        self.assertEqual(normalizar("Güereca"), ["GUERECA"])

    def test_signos_se_eliminan(self):
        self.assertEqual(normalizar("O'Connor"), ["OCONNOR"])
        self.assertEqual(normalizar("Pérez-Gil"), ["PEREZGIL"])

    def test_particulas(self):
        self.assertEqual(quitar_particulas(normalizar("De la Cruz")), ["CRUZ"])
        self.assertEqual(quitar_particulas(["DE", "LA"]), ["LA"])

    def test_vocal_interna(self):
        self.assertEqual(primera_vocal_interna("CRUZ"), "U")
        self.assertEqual(primera_vocal_interna("AVILA"), "I")
        self.assertEqual(primera_vocal_interna("BRR"), "X")


class PruebasRFC(unittest.TestCase):
    def test_p1_caso_general(self):
        self.assertEqual(rfc_sin_homoclave("Juan", "Pérez", "López", 17, 5, 1990), "PELJ900517")

    def test_p2_particulas_y_nombre_compuesto(self):
        self.assertEqual(
            rfc_sin_homoclave("María Guadalupe", "De la Cruz", "Núñez", 3, 11, 1985),
            "CUNG851103")

    def test_p3_sin_materno(self):
        self.assertEqual(rfc_sin_homoclave("José Luis", "Hernández", None, 29, 2, 2000), "HELU000229")

    def test_p4_palabra_inconveniente(self):
        self.assertEqual(rfc_sin_homoclave("Óscar", "Pérez", "Díaz", 8, 12, 1995), "PEDX951208")

    def test_p5_enie(self):
        self.assertEqual(rfc_sin_homoclave("Pedro", "Ñáñez", "Sosa", 15, 9, 2003), "XASP030915")

    def test_paterno_corto(self):
        self.assertEqual(rfc_sin_homoclave("Ana", "Ek", "Mena", 1, 1, 1999), "EMAN990101")

    def test_lista_inconvenientes_completa(self):
        self.assertEqual(len(INCONVENIENTES), 80)


if __name__ == "__main__":
    unittest.main()
