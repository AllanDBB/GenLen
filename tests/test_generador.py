"""
test_generador.py - Pruebas unitarias para el generador de codigo Python.

Cubre:
  - Declaraciones de todos los tipos (num, bool, adn, arn, prot)
  - Asignaciones y expresiones aritmeticas/logicas
  - Protocolos como funciones Python
  - Mecanismos biologicos como llamadas de runtime
  - Booleanos (V -> True, F -> False)
  - Ejecucion del codigo generado sin errores
  - Validez del codigo Python generado

GenLen - Lenguaje Genetico
Curso: Compiladores e Interpretes
"""

import sys
import os
import subprocess
import tempfile

# Banner
BANNER = r"""
                                _.-;;-._
                        '-..-'|   ||   |
                        '-..-'|_.-;;-._|
                        '-..-'|   ||   |
                        '-..-'|_.-''-._|

        GenLen - Pruebas Unitarias del Generador de Codigo
"""
print(BANNER)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from src.explorador  import Explorador
from src.analizador  import Analizador
from src.verificador import Verificador
from src.generador   import Generador
from src.nodo        import TipoNodo


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def compilar_y_generar(codigo_genlen: str) -> str:
    """
    Compila codigo GenLen a traves de todas las etapas.
    Retorna el codigo Python generado.
    """
    exp = Explorador(codigo_genlen)
    tokens = exp.escanear()

    par = Analizador(tokens)
    ast = par.analizar()

    ver = Verificador(verbose=False)
    ast_decorado = ver.verificar(ast)

    gen = Generador()
    codigo_python = gen.generar(ast_decorado)

    return codigo_python


def ejecutar_codigo_python(codigo_python: str) -> str:
    """
    Ejecuta codigo Python en un archivo temporal.
    Retorna stdout + stderr.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(codigo_python)
        f.flush()
        temp_file = f.name

    try:
        resultado = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return resultado.stdout + resultado.stderr
    finally:
        os.unlink(temp_file)


# ---------------------------------------------------------------------------
# 1. Declaraciones basicas
# ---------------------------------------------------------------------------

class TestGeneradorBasico(unittest.TestCase):
    """Generacion de codigo para declaraciones de cada tipo."""

    def test_declaracion_num_sin_inicializador(self):
        """Declaracion de numero sin valor inicial genera Python valido."""
        codigo = "lab Test /\\\nmuestra x : num;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("x = 0", python)
        ejecutar_codigo_python(python)

    def test_declaracion_num_con_inicializador(self):
        """Declaracion de numero con valor inicial."""
        codigo = "lab Test /\\\nmuestra x : num = 42;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("x = 42", python)
        ejecutar_codigo_python(python)

    def test_declaracion_bool(self):
        """Declaracion booleana (V -> True)."""
        codigo = "lab Test /\\\nmuestra flag : bool = V;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("flag = True", python)
        ejecutar_codigo_python(python)

    def test_declaracion_adn(self):
        """Declaracion de ADN (cadena genetica)."""
        codigo = "lab Test /\\\nmuestra gen : adn = adn 'ATGC';\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn('gen = "ATGC"', python)
        ejecutar_codigo_python(python)

    def test_declaracion_arn(self):
        """Declaracion de ARN."""
        codigo = "lab Test /\\\nmuestra mrna : arn = arn 'AUCG';\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn('mrna = "AUCG"', python)
        ejecutar_codigo_python(python)

    def test_declaracion_prot(self):
        """Declaracion de proteina."""
        codigo = "lab Test /\\\nmuestra proteina : prot = prot 'MKL';\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn('proteina = "MKL"', python)
        ejecutar_codigo_python(python)


# ---------------------------------------------------------------------------
# 2. Asignaciones y expresiones
# ---------------------------------------------------------------------------

class TestGeneradorAsignacion(unittest.TestCase):
    """Generacion de asignaciones y expresiones."""

    def test_asignacion_simple_numero(self):
        """Asignacion de numero."""
        codigo = "lab Test /\\\nmuestra x : num;\nx = 10;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("x = 10", python)
        ejecutar_codigo_python(python)

    def test_asignacion_variable(self):
        """Asignacion de variable a variable."""
        codigo = "lab Test /\\\nmuestra x : num = 5;\nmuestra y : num;\ny = x;\n\\/"
        python = compilar_y_generar(codigo)
        ejecutar_codigo_python(python)

    def test_expresion_suma(self):
        """Expresion aritmetica (suma)."""
        codigo = "lab Test /\\\nmuestra res : num = 3 + 4;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("res =", python)
        self.assertIn("+", python)
        ejecutar_codigo_python(python)

    def test_expresion_multiplicacion(self):
        """Expresion aritmetica (multiplicacion)."""
        codigo = "lab Test /\\\nmuestra res : num = 3 * 4;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("*", python)
        ejecutar_codigo_python(python)

    def test_expresion_comparacion(self):
        """Expresion de comparacion."""
        codigo = "lab Test /\\\nmuestra b : bool = 5 > 3;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn(">", python)
        ejecutar_codigo_python(python)

    def test_expresion_logica_y(self):
        """Operador logico 'y' mapea a 'and'."""
        codigo = "lab Test /\\\nmuestra b : bool = V y F;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("and", python)
        ejecutar_codigo_python(python)

    def test_expresion_logica_o(self):
        """Operador logico 'o' mapea a 'or'."""
        codigo = "lab Test /\\\nmuestra b : bool = V o F;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("or", python)
        ejecutar_codigo_python(python)


# ---------------------------------------------------------------------------
# 3. Protocolos
# ---------------------------------------------------------------------------

class TestGeneradorProtocolo(unittest.TestCase):
    """Generacion de protocolos como funciones Python."""

    def test_protocolo_sin_parametros(self):
        """Protocolo sin parametros -> funcion sin args."""
        codigo = """lab Test /\\
    protocolo doble()
    /\\
        muestra res : num = 2;
    \\/
\\/"""
        python = compilar_y_generar(codigo)
        self.assertIn("def doble():", python)
        ejecutar_codigo_python(python)

    def test_protocolo_con_parametros(self):
        """Protocolo con parametros -> funcion con args."""
        codigo = """lab Test /\\
    protocolo suma(a: num, b: num)
    /\\
        muestra res : num = a;
    \\/
\\/"""
        python = compilar_y_generar(codigo)
        self.assertIn("def suma(a, b):", python)
        ejecutar_codigo_python(python)

    def test_protocolo_con_cuerpo(self):
        """Protocolo con declaraciones en el cuerpo."""
        codigo = """lab Test /\\
    protocolo test()
    /\\
        muestra x : num = 10;
        muestra resultado : num = 20;
    \\/
\\/"""
        python = compilar_y_generar(codigo)
        self.assertIn("def test():", python)
        self.assertIn("x = 10", python)
        self.assertIn("resultado = 20", python)
        ejecutar_codigo_python(python)

    def test_llamada_protocolo(self):
        """Llamada a protocolo usuario desde el cuerpo."""
        codigo = """lab Test /\\
    protocolo doble()
    /\\
        muestra r : num = 2;
    \\/
    doble();
\\/"""
        python = compilar_y_generar(codigo)
        self.assertIn("doble()", python)
        ejecutar_codigo_python(python)


# ---------------------------------------------------------------------------
# 4. Mecanismos biologicos
# ---------------------------------------------------------------------------

class TestGeneradorMecanismo(unittest.TestCase):
    """Generacion de llamadas a mecanismos."""

    def test_mecanismo_transcribir(self):
        """Mecanismo transcribir mapea a _transcribir()."""
        codigo = """lab Test /\\
    muestra dna : adn = adn 'ATGC';
    muestra rna : arn;
    rna = dna->transcribir();
\\/"""
        python = compilar_y_generar(codigo)
        self.assertIn("_transcribir(", python)
        ejecutar_codigo_python(python)

    def test_mecanismo_traducir(self):
        """Mecanismo traducir mapea a _traducir()."""
        codigo = """lab Test /\\
    muestra rna : arn = arn 'AUGC';
    muestra prot : prot;
    prot = rna->traducir();
\\/"""
        python = compilar_y_generar(codigo)
        self.assertIn("_traducir(", python)
        ejecutar_codigo_python(python)

    def test_mecanismo_mutar(self):
        """Mecanismo mutar mapea a _mutar()."""
        codigo = """lab Test /\\
    muestra seq : adn = adn 'ATGC';
    muestra mut : adn;
    mut = seq->mutar();
\\/"""
        python = compilar_y_generar(codigo)
        self.assertIn("_mutar(", python)
        ejecutar_codigo_python(python)

    def test_mecanismo_con_argumentos(self):
        """Mecanismo con argumentos (cas9)."""
        codigo = """lab Test /\\
    muestra gen : adn = adn 'ATGCATGC';
    muestra guia : adn = adn 'ATG';
    muestra editado : adn;
    editado = gen->cas9(guia);
\\/"""
        python = compilar_y_generar(codigo)
        self.assertIn("_cas9(", python)
        ejecutar_codigo_python(python)

    def test_cadena_mecanismos(self):
        """Encadenamiento de mecanismos."""
        codigo = """lab Test /\\
    muestra gen : adn = adn 'ATGC';
    muestra prot : prot;
    prot = gen->transcribir()->traducir();
\\/"""
        python = compilar_y_generar(codigo)
        self.assertIn("_traducir(", python)
        self.assertIn("_transcribir(", python)
        ejecutar_codigo_python(python)


# ---------------------------------------------------------------------------
# 5. Booleanos
# ---------------------------------------------------------------------------

class TestGeneradorBooleanos(unittest.TestCase):
    """Generacion de booleanos."""

    def test_booleano_verdadero(self):
        """V -> True en Python."""
        codigo = "lab Test /\\\nmuestra t : bool = V;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("t = True", python)
        ejecutar_codigo_python(python)

    def test_booleano_falso(self):
        """F -> False en Python."""
        codigo = "lab Test /\\\nmuestra f : bool = F;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("f = False", python)
        ejecutar_codigo_python(python)


# ---------------------------------------------------------------------------
# 6. Ejecucion del codigo generado
# ---------------------------------------------------------------------------

class TestGeneradorEjecucion(unittest.TestCase):
    """Verificar que el codigo generado sea ejecutable sin errores."""

    def test_ejecucion_declaraciones(self):
        """Codigo con solo declaraciones ejecuta sin error."""
        codigo = """lab Test /\\
    muestra x : num = 10;
    muestra y : adn = adn 'ATGC';
    muestra z : bool = V;
\\/"""
        python = compilar_y_generar(codigo)
        salida = ejecutar_codigo_python(python)
        self.assertNotIn("Traceback", salida)
        self.assertNotIn("Error", salida)

    def test_ejecucion_con_protocolo(self):
        """Codigo con protocolo ejecuta sin error."""
        codigo = """lab Test /\\
    protocolo test(x: num)
    /\\
        muestra r : num = x;
    \\/
    test(42);
\\/"""
        python = compilar_y_generar(codigo)
        salida = ejecutar_codigo_python(python)
        self.assertNotIn("Traceback", salida)
        self.assertNotIn("Error", salida)

    def test_ejecucion_con_mecanismos(self):
        """Codigo con mecanismos ejecuta sin error."""
        codigo = """lab Test /\\
    muestra gen : adn = adn 'ATGCTA';
    muestra arn : arn;
    arn = gen->transcribir();
\\/"""
        python = compilar_y_generar(codigo)
        salida = ejecutar_codigo_python(python)
        self.assertNotIn("Traceback", salida)


# ---------------------------------------------------------------------------
# 7. Validez del codigo generado
# ---------------------------------------------------------------------------

class TestGeneradorCodigoValido(unittest.TestCase):
    """Verifica que el codigo generado sea Python valido."""

    def test_tiene_runtime(self):
        """El codigo generado debe incluir la tabla de codones."""
        codigo = "lab Test /\\\nmuestra x : num = 1;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("_CODON_TABLE", python)
        self.assertIn("def _transcribir", python)
        self.assertIn("def _traducir", python)
        self.assertIn("def _mutar", python)

    def test_tiene_encabezado(self):
        """El codigo generado tiene comentario del programa."""
        codigo = "lab MiPrograma /\\\nmuestra x : num = 1;\n\\/"
        python = compilar_y_generar(codigo)
        self.assertIn("# Programa: MiPrograma", python)

    def test_sintaxis_python_valida(self):
        """El codigo generado tiene sintaxis Python valida."""
        codigo = """lab Test /\\
    muestra a : num = 1;
    muestra b : num = 2;
    muestra c : num = a + b;
\\/"""
        python = compilar_y_generar(codigo)
        try:
            compile(python, "<generated>", "exec")
        except SyntaxError as e:
            self.fail(f"Codigo Python generado tiene error de sintaxis: {e}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
