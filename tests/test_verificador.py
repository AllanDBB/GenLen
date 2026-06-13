"""
test_verificador.py - Pruebas unitarias para el verificador semantico de GenLen.

Cubre:
  - Decorado del AST con tipos y definiciones
  - Identificadores declarados antes de uso
  - Inferencia y compatibilidad de tipos
  - Firmas de protocolos en la tabla de simbolos
  - Aridad de mecanismos biologicos
  - Alcances: global, local en protocolos, parametros

GenLen - Lenguaje Genetico
Curso: Compiladores e Interpretes
"""

import sys
import os

# Banner
BANNER = r"""
                                _.-;;-._
                        '-..-'|   ||   |
                        '-..-'|_.-;;-._|
                        '-..-'|   ||   |
                        '-..-'|_.-''-._|

        GenLen - Pruebas Unitarias del Verificador Semantico
"""
print(BANNER)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from src.explorador  import Explorador
from src.analizador  import Analizador
from src.verificador import Verificador


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def verificar(codigo: str):
    """
    Escanea, analiza y verifica `codigo`.
    Retorna (ast_decorado, verificador).
    """
    exp = Explorador(codigo)
    tokens = exp.escanear()
    par = Analizador(tokens)
    ast = par.analizar()

    assert not exp.errores, exp.errores
    assert not par.errores, par.errores

    ver = Verificador(verbose=False)
    ver.verificar(ast)
    return ast, ver


def programa(cuerpo: str) -> str:
    """Envuelve instrucciones en un programa GenLen minimo."""
    return f"lab L /\\\n{cuerpo}\n\\/"


# ---------------------------------------------------------------------------
# 1. Verificacion semantica basica
# ---------------------------------------------------------------------------

class TestVerificadorSemantico(unittest.TestCase):
    """Tipos, declaraciones, protocolos y mecanismos."""

    def test_programa_valido_decora_tipos_y_definiciones(self):
        """Programa valido decora el AST con tipos y definiciones."""
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
        """Usar variable sin declarar genera error."""
        _, ver = verificar(programa("x = 10;"))

        self.assertEqual(len(ver.errores), 1)
        self.assertIn("Variable 'x' no declarada", ver.errores[0])

    def test_declaracion_con_tipo_incompatible(self):
        """Asignar tipo incompatible en declaracion genera error."""
        _, ver = verificar(programa("muestra x : num = V;"))

        self.assertEqual(len(ver.errores), 1)
        self.assertIn("'x' es 'num'", ver.errores[0])
        self.assertIn("'bool'", ver.errores[0])

    def test_llamada_protocolo_valida_argumentos(self):
        """Tipos de argumentos incorrectos generan error."""
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
        """Cantidad de argumentos incorrecta genera error."""
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
        """Parametro duplicado en protocolo genera error."""
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
        """Mecanismo con aridad incorrecta genera error."""
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
        """Asignar resultado de protocolo void genera error."""
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


# ---------------------------------------------------------------------------
# 2. Alcances (scopes)
# ---------------------------------------------------------------------------

class TestVerificadorEscopos(unittest.TestCase):
    """Alcances: global, local en protocolos, parametros."""

    def test_variable_global_declarada_localmente_en_protocolo(self):
        """Variables globales son accesibles dentro de protocolos."""
        ast, ver = verificar(
            programa(
                """
                muestra x : num = 10;
                protocolo p()
                /\\
                    muestra copia : num = x;
                \\/
                """
            )
        )

        self.assertFalse(ver.errores)
        decl_x = ast.hijos[0].hijos[0]
        self.assertEqual(decl_x.tipo_dato, "num")

    def test_parametro_local_a_protocolo(self):
        """Parametros son accesibles dentro del protocolo."""
        ast, ver = verificar(
            programa(
                """
                protocolo doble(x: num)
                /\\
                    muestra resultado : num = x;
                \\/
                """
            )
        )

        self.assertFalse(ver.errores)

    def test_variable_local_protocolo_no_accesible_globalmente(self):
        """Variables locales en protocolo no son accesibles globalmente."""
        _, ver = verificar(
            programa(
                """
                protocolo p()
                /\\
                    muestra local_var : num = 5;
                \\/
                muestra copia : num = local_var;
                """
            )
        )

        self.assertEqual(len(ver.errores), 1)
        self.assertIn("Identificador 'local_var' no declarado", ver.errores[0])

    def test_parametro_protocolo_no_accesible_globalmente(self):
        """Parametros no son accesibles fuera del protocolo."""
        _, ver = verificar(
            programa(
                """
                protocolo p(x: num)
                /\\
                    muestra copia : num = x;
                \\/
                muestra resultado : num = x;
                """
            )
        )

        self.assertEqual(len(ver.errores), 1)
        self.assertIn("Identificador 'x' no declarado", ver.errores[0])

    def test_variable_local_sombrea_global(self):
        """Variable local en protocolo sombrea la global del mismo nombre."""
        ast, ver = verificar(
            programa(
                """
                muestra contador : num = 10;
                protocolo p()
                /\\
                    muestra contador : num = 20;
                    muestra local_result : num = contador;
                \\/
                """
            )
        )

        self.assertFalse(ver.errores)

    def test_variable_global_accesible_tras_salir_protocolo(self):
        """Variables globales son accesibles tras definir un protocolo."""
        ast, ver = verificar(
            programa(
                """
                muestra gen : adn = adn 'ATGC';
                protocolo p()
                /\\
                \\/
                muestra copia : adn = gen;
                """
            )
        )

        self.assertFalse(ver.errores)

    def test_protocolo_llamar_otro_protocolo(self):
        """Un protocolo puede llamar a otro protocolo definido globalmente."""
        ast, ver = verificar(
            programa(
                """
                protocolo a()
                /\\
                    muestra x : num = 5;
                \\/
                protocolo b()
                /\\
                    a();
                \\/
                """
            )
        )

        self.assertFalse(ver.errores)

    def test_identificador_en_alcance_anidado_se_decora(self):
        """Identificadores en alcance local reciben decoracion."""
        ast, ver = verificar(
            programa(
                """
                muestra gen : adn = adn 'ATGCT';
                protocolo transcribir_gen()
                /\\
                    muestra gen_rna : arn = gen->transcribir();
                \\/
                """
            )
        )

        self.assertFalse(ver.errores)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
