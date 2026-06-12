"""
test_verificador.py - Pruebas unitarias para el verificador semantico de GenLen.

Cubre:
  - Identificadores declarados antes de uso
  - Inferencia y compatibilidad de tipos
  - Firmas de protocolos en la tabla de simbolos
  - Aridad de mecanismos biologicos
  - Decorado basico del AST
"""

import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analizador import Analizador
from src.explorador import Explorador
from src.verificador import Verificador


def verificar(codigo: str):
    exp = Explorador(codigo)
    tokens = exp.escanear()
    par = Analizador(tokens)
    ast = par.analizar()

    assert not exp.errores, exp.errores
    assert not par.errores, par.errores

    ver = Verificador()
    with redirect_stdout(StringIO()):
        ver.verificar(ast)
    return ast, ver


def programa(cuerpo: str) -> str:
    return f"lab L /\\\n{cuerpo}\n\\/"


class TestVerificadorSemantico(unittest.TestCase):
    def test_programa_valido_decora_tipos_y_definiciones(self):
        ast, ver = verificar(
            programa(
                """
                muestra gen : adn = adn 'ATGCT';
                muestra arn1 : arn;
                arn1 = gen->transcribir();
                """
            )
        )

        self.assertFalse(ver.errores)
        asignacion = ast.hijos[0].hijos[2]
        llamada = asignacion.hijos[0]
        receptor = llamada.hijos[0]

        self.assertEqual(asignacion.tipo_dato, "arn")
        self.assertEqual(llamada.tipo_dato, "arn")
        self.assertEqual(receptor.tipo_dato, "adn")
        self.assertIsNotNone(receptor.definicion)

    def test_identificador_no_declarado(self):
        _, ver = verificar(programa("x = 10;"))

        self.assertEqual(len(ver.errores), 1)
        self.assertIn("Variable 'x' no declarada", ver.errores[0])

    def test_declaracion_con_tipo_incompatible(self):
        _, ver = verificar(programa("muestra x : num = V;"))

        self.assertEqual(len(ver.errores), 1)
        self.assertIn("'x' es 'num'", ver.errores[0])
        self.assertIn("'bool'", ver.errores[0])

    def test_llamada_protocolo_valida_argumentos(self):
        _, ver = verificar(
            programa(
                """
                protocolo p(x: num, flag: bool)
                /\\
                    muestra copia : num = x;
                \\/
                p(V, 1);
                """
            )
        )

        self.assertEqual(len(ver.errores), 2)
        self.assertIn("Argumento 1 de 'p'", ver.errores[0])
        self.assertIn("Argumento 2 de 'p'", ver.errores[1])

    def test_llamada_protocolo_valida_cantidad_argumentos(self):
        _, ver = verificar(
            programa(
                """
                protocolo p(x: num, flag: bool)
                /\\
                    muestra copia : num = x;
                \\/
                p(1);
                """
            )
        )

        self.assertEqual(len(ver.errores), 1)
        self.assertIn("espera 2 argumento(s)", ver.errores[0])
        self.assertIn("1", ver.errores[0])

    def test_parametro_repetido_en_protocolo(self):
        _, ver = verificar(
            programa(
                """
                protocolo p(x: num, x: bool)
                /\\
                \\/
                """
            )
        )

        self.assertEqual(len(ver.errores), 1)
        self.assertIn("'x' ya declarado", ver.errores[0])

    def test_mecanismo_valida_aridad(self):
        _, ver = verificar(
            programa(
                """
                muestra gen : adn = adn 'ATGCT';
                muestra corte : adn = adn 'AT';
                muestra arn1 : arn;
                arn1 = gen->transcribir(corte);
                """
            )
        )

        self.assertEqual(len(ver.errores), 1)
        self.assertIn("'transcribir()' espera 0 argumento(s)", ver.errores[0])

    def test_protocolo_void_no_se_puede_asignar(self):
        _, ver = verificar(
            programa(
                """
                protocolo p()
                /\\
                \\/
                muestra x : num = p();
                """
            )
        )

        self.assertEqual(len(ver.errores), 1)
        self.assertIn("'void'", ver.errores[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
