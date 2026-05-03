"""
test_analizador.py - Pruebas unitarias para el analizador sintáctico de GenLen.

Cubre:
  - Programa mínimo (lab con cuerpo vacío)
  - Declaraciones con y sin inicializador
  - Asignaciones simples
  - Llamadas a mecanismos (simples y encadenadas)
  - Definición de protocolo con parámetros
  - Llamada a protocolo como expresión
  - Expresiones aritméticas (precedencia)
  - Expresiones de comparación y booleanas
  - Constant folding
  - Recuperación ante errores sintácticos (modo pánico)

GenLen - Lenguaje Genético
Curso: Compiladores e Intérpretes
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

        GenLen - Pruebas Unitarias del Analizador Sintáctico (LL1)
"""
print(BANNER)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from src.explorador  import Explorador
from src.analizador  import Analizador, doblar_constantes
from src.nodo        import TipoNodo
from src.token       import TipoToken


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def parsear(codigo: str):
    """
    Escanea y analiza `codigo`.
    Retorna (ast_raiz, errores_lexicos, errores_sintacticos).
    """
    exp    = Explorador(codigo)
    tokens = exp.escanear()
    par    = Analizador(tokens)
    ast    = par.analizar()
    return ast, exp.errores, par.errores


def cuerpo_de(ast):
    """Retorna el nodo CUERPO (primer hijo del PROGRAMA)."""
    return ast.hijos[0]


# ---------------------------------------------------------------------------
# 1. Estructura básica
# ---------------------------------------------------------------------------

class TestEstructuraBasica(unittest.TestCase):
    """Programa mínimo y estructura del nodo raíz."""

    def test_programa_vacio(self):
        ast, el, es = parsear("lab MiLab /\\\n\\/")
        self.assertEqual(ast.tipo, TipoNodo.PROGRAMA)
        self.assertEqual(ast.contenido, "MiLab")
        self.assertFalse(el, "No deben haber errores léxicos")
        self.assertFalse(es, "No deben haber errores sintácticos")

    def test_cuerpo_es_primer_hijo(self):
        ast, _, _ = parsear("lab L /\\\n\\/")
        self.assertEqual(len(ast.hijos), 1)
        self.assertEqual(ast.hijos[0].tipo, TipoNodo.CUERPO)

    def test_nombre_programa(self):
        ast, _, _ = parsear("lab GenEjemplo /\\\n\\/")
        self.assertEqual(ast.contenido, "GenEjemplo")


# ---------------------------------------------------------------------------
# 2. Declaraciones
# ---------------------------------------------------------------------------

class TestDeclaraciones(unittest.TestCase):
    """Nodo DECLARACION con distintos tipos e inicializadores."""

    def _declaracion(self, codigo: str):
        ast, el, es = parsear(f"lab L /\\\n{codigo}\n\\/")
        self.assertFalse(el)
        self.assertFalse(es)
        return cuerpo_de(ast).hijos[0]

    def test_declaracion_sin_inicializador(self):
        d = self._declaracion("muestra x : num;")
        self.assertEqual(d.tipo, TipoNodo.DECLARACION)
        self.assertEqual(d.contenido, "x")
        self.assertEqual(len(d.hijos), 1)              # solo TIPO
        self.assertEqual(d.hijos[0].tipo, TipoNodo.TIPO)
        self.assertEqual(d.hijos[0].contenido, "num")

    def test_declaracion_con_numero(self):
        d = self._declaracion("muestra n : num = 42;")
        self.assertEqual(d.tipo, TipoNodo.DECLARACION)
        self.assertEqual(len(d.hijos), 2)              # TIPO + NUMERO
        self.assertEqual(d.hijos[1].tipo, TipoNodo.NUMERO)
        self.assertEqual(d.hijos[1].contenido, "42")

    def test_declaracion_con_cadena_adn(self):
        d = self._declaracion("muestra g : adn = adn 'ATGCT';")
        self.assertEqual(len(d.hijos), 2)
        self.assertEqual(d.hijos[0].contenido, "adn")
        self.assertEqual(d.hijos[1].tipo, TipoNodo.CADENA_ADN)
        self.assertEqual(d.hijos[1].contenido, "ATGCT")

    def test_declaracion_con_cadena_arn(self):
        d = self._declaracion("muestra m : arn = arn 'AUCG';")
        self.assertEqual(d.hijos[1].tipo, TipoNodo.CADENA_ARN)

    def test_declaracion_con_cadena_proteina(self):
        d = self._declaracion("muestra p : prot = prot 'MKLV';")
        self.assertEqual(d.hijos[1].tipo, TipoNodo.CADENA_PROTEINA)

    def test_declaracion_bool(self):
        d = self._declaracion("muestra activo : bool;")
        self.assertEqual(d.hijos[0].contenido, "bool")

    def test_declaracion_con_booleano(self):
        d = self._declaracion("muestra activo : num = V;")
        self.assertEqual(d.hijos[1].tipo, TipoNodo.BOOLEANO)
        self.assertEqual(d.hijos[1].contenido, "V")


# ---------------------------------------------------------------------------
# 3. Asignaciones
# ---------------------------------------------------------------------------

class TestAsignaciones(unittest.TestCase):
    """Nodo ASIGNACION: variable = expresión."""

    def _asignacion(self, codigo: str):
        prog = f"lab L /\\\n{codigo}\n\\/"
        ast, el, es = parsear(prog)
        self.assertFalse(el)
        self.assertFalse(es)
        return cuerpo_de(ast).hijos[0]

    def test_asignacion_simple(self):
        a = self._asignacion("x = 10;")
        self.assertEqual(a.tipo, TipoNodo.ASIGNACION)
        self.assertEqual(a.contenido, "x")
        self.assertEqual(a.hijos[0].tipo, TipoNodo.NUMERO)

    def test_asignacion_expresion_aritmetica(self):
        a = self._asignacion("r = a + b;")
        self.assertEqual(a.hijos[0].tipo, TipoNodo.BINARIA)
        self.assertEqual(a.hijos[0].contenido, "+")

    def test_asignacion_booleano_literal(self):
        a = self._asignacion("flag = F;")
        self.assertEqual(a.hijos[0].tipo, TipoNodo.BOOLEANO)
        self.assertEqual(a.hijos[0].contenido, "F")


# ---------------------------------------------------------------------------
# 4. Llamadas a mecanismos
# ---------------------------------------------------------------------------

class TestLlamadasMecanismo(unittest.TestCase):
    """Nodo LLAMADA_MECANISMO: receptor->mecanismo(args)."""

    def _instruccion(self, codigo: str):
        ast, el, es = parsear(f"lab L /\\\n{codigo}\n\\/")
        self.assertFalse(el)
        self.assertFalse(es)
        return cuerpo_de(ast).hijos[0]

    def test_mecanismo_sin_args_standalone(self):
        i = self._instruccion("gen->transcribir();")
        self.assertEqual(i.tipo, TipoNodo.LLAMADA_MECANISMO)
        self.assertEqual(i.contenido, "transcribir")
        # hijos[0] = receptor (IDENTIFICADOR)
        self.assertEqual(i.hijos[0].tipo, TipoNodo.IDENTIFICADOR)
        self.assertEqual(i.hijos[0].contenido, "gen")

    def test_mecanismo_como_asignacion(self):
        i = self._instruccion("arn1 = gen1->transcribir();")
        self.assertEqual(i.tipo, TipoNodo.ASIGNACION)
        llamada = i.hijos[0]
        self.assertEqual(llamada.tipo, TipoNodo.LLAMADA_MECANISMO)
        self.assertEqual(llamada.contenido, "transcribir")

    def test_mecanismo_con_args(self):
        i = self._instruccion("ed = g->cas9(corte);")
        llamada = i.hijos[0]
        self.assertEqual(llamada.contenido, "cas9")
        # hijos[1] = LISTA_ARGS con un hijo
        self.assertEqual(llamada.hijos[1].tipo, TipoNodo.LISTA_ARGS)
        self.assertEqual(len(llamada.hijos[1].hijos), 1)

    def test_cadena_mecanismos(self):
        codigo = "res = gen->transcribir()->traducir();"
        ast, _, es = parsear(f"lab L /\\\n{codigo}\n\\/")
        self.assertFalse(es)
        asig    = cuerpo_de(ast).hijos[0]
        traducir = asig.hijos[0]
        self.assertEqual(traducir.contenido, "traducir")
        transcribir = traducir.hijos[0]
        self.assertEqual(transcribir.contenido, "transcribir")

    def test_cadena_larga(self):
        codigo = "r = g->cas9(c)->mutar()->transcribir()->traducir();"
        ast, _, es = parsear(f"lab L /\\\n{codigo}\n\\/")
        self.assertFalse(es)
        # Nodo más externo debe ser "traducir"
        nodo = cuerpo_de(ast).hijos[0].hijos[0]
        self.assertEqual(nodo.contenido, "traducir")


# ---------------------------------------------------------------------------
# 5. Definición de protocolo
# ---------------------------------------------------------------------------

class TestProtocolo(unittest.TestCase):
    """Nodo PROTOCOLO con parámetros y cuerpo."""

    PROTOCOLO_SIMPLE = """
lab L /\\
    protocolo doble(x: num)
    /\\
        muestra r : num = x;
    \\/
\\/
"""

    PROTOCOLO_DOS_PARAMS = """
lab L /\\
    protocolo editar(g: adn, c: adn)
    /\\
        muestra ed : adn;
        ed = g->cas9(c);
    \\/
\\/
"""

    def test_protocolo_existe_en_cuerpo(self):
        ast, el, es = parsear(self.PROTOCOLO_SIMPLE)
        self.assertFalse(el)
        self.assertFalse(es)
        p = cuerpo_de(ast).hijos[0]
        self.assertEqual(p.tipo, TipoNodo.PROTOCOLO)
        self.assertEqual(p.contenido, "doble")

    def test_protocolo_tiene_lista_params(self):
        ast, _, _ = parsear(self.PROTOCOLO_SIMPLE)
        p = cuerpo_de(ast).hijos[0]
        self.assertEqual(p.hijos[0].tipo, TipoNodo.LISTA_PARAMS)

    def test_protocolo_param_nombre_y_tipo(self):
        ast, _, _ = parsear(self.PROTOCOLO_SIMPLE)
        params = cuerpo_de(ast).hijos[0].hijos[0]
        param  = params.hijos[0]
        self.assertEqual(param.tipo, TipoNodo.PARAM)
        self.assertEqual(param.contenido, "x")
        self.assertEqual(param.hijos[0].contenido, "num")

    def test_protocolo_dos_params(self):
        ast, _, _ = parsear(self.PROTOCOLO_DOS_PARAMS)
        params = cuerpo_de(ast).hijos[0].hijos[0]
        self.assertEqual(len(params.hijos), 2)

    def test_protocolo_cuerpo(self):
        ast, _, _ = parsear(self.PROTOCOLO_SIMPLE)
        p = cuerpo_de(ast).hijos[0]
        cuerpo = p.hijos[1]
        self.assertEqual(cuerpo.tipo, TipoNodo.CUERPO)
        self.assertGreater(len(cuerpo.hijos), 0)


# ---------------------------------------------------------------------------
# 6. Expresiones aritméticas y de comparación
# ---------------------------------------------------------------------------

class TestExpresiones(unittest.TestCase):
    """Precedencia y asociatividad en expresiones."""

    def _expr(self, expr_str: str):
        """Parsea una asignación `res = <expr>` y retorna el nodo de expresión."""
        ast, el, es = parsear(f"lab L /\\\nres = {expr_str};\n\\/")
        self.assertFalse(el)
        self.assertFalse(es)
        return cuerpo_de(ast).hijos[0].hijos[0]

    def test_suma(self):
        n = self._expr("a + b")
        self.assertEqual(n.tipo, TipoNodo.BINARIA)
        self.assertEqual(n.contenido, "+")

    def test_precedencia_mult_sobre_suma(self):
        # a + b * c  →  +(a, *(b, c))
        n = self._expr("a + b * c")
        self.assertEqual(n.contenido, "+")
        self.assertEqual(n.hijos[1].contenido, "*")

    def test_parentesis(self):
        # (a + b) * c  →  *( +(a,b), c )
        n = self._expr("(a + b) * c")
        self.assertEqual(n.contenido, "*")
        self.assertEqual(n.hijos[0].contenido, "+")

    def test_unario_negativo(self):
        n = self._expr("-x")
        self.assertEqual(n.tipo, TipoNodo.UNARIA)
        self.assertEqual(n.contenido, "-")

    def test_comparacion_mayor(self):
        n = self._expr("a > b")
        self.assertEqual(n.tipo, TipoNodo.BINARIA)
        self.assertEqual(n.contenido, ">")

    def test_comparacion_igual(self):
        n = self._expr("a == b")
        self.assertEqual(n.contenido, "==")

    def test_operador_logico_y(self):
        n = self._expr("(a > 0) y (b > 0)")
        self.assertEqual(n.contenido, "y")

    def test_operador_logico_o(self):
        n = self._expr("(a > 0) o (b > 0)")
        self.assertEqual(n.contenido, "o")

    def test_modulo(self):
        n = self._expr("x % 3")
        self.assertEqual(n.contenido, "%")

    def test_llamada_protocolo_en_expresion(self):
        n = self._expr("doble(x)")
        self.assertEqual(n.tipo, TipoNodo.LLAMADA_PROTOCOLO)
        self.assertEqual(n.contenido, "doble")


# ---------------------------------------------------------------------------
# 7. Constant Folding
# ---------------------------------------------------------------------------

class TestConstantFolding(unittest.TestCase):
    """La función doblar_constantes evalúa operaciones entre literales."""

    def _fold(self, expr_str: str):
        ast, _, _ = parsear(f"lab L /\\\nres = {expr_str};\n\\/")
        ast = doblar_constantes(ast)
        return cuerpo_de(ast).hijos[0].hijos[0]

    def test_multiplicacion(self):
        n = self._fold("3 * 4")
        self.assertEqual(n.tipo, TipoNodo.NUMERO)
        self.assertEqual(n.contenido, "12")

    def test_suma(self):
        n = self._fold("10 + 5")
        self.assertEqual(n.contenido, "15")

    def test_resta(self):
        n = self._fold("10 - 3")
        self.assertEqual(n.contenido, "7")

    def test_division(self):
        n = self._fold("10 / 4")
        self.assertEqual(n.contenido, "2.5")

    def test_division_exacta(self):
        n = self._fold("10 / 2")
        self.assertEqual(n.contenido, "5")

    def test_modulo(self):
        n = self._fold("10 % 3")
        self.assertEqual(n.contenido, "1")

    def test_division_por_cero_no_pliega(self):
        n = self._fold("5 / 0")
        self.assertEqual(n.tipo, TipoNodo.BINARIA)  # no debe plegarse

    def test_plegado_anidado(self):
        # (2 + 3) * 4  →  5 * 4  →  20
        n = self._fold("(2 + 3) * 4")
        self.assertEqual(n.tipo, TipoNodo.NUMERO)
        self.assertEqual(n.contenido, "20")

    def test_no_pliega_variables(self):
        n = self._fold("a + b")
        self.assertEqual(n.tipo, TipoNodo.BINARIA)


# ---------------------------------------------------------------------------
# 8. Manejo de errores sintácticos
# ---------------------------------------------------------------------------

class TestErroresSintacticos(unittest.TestCase):
    """El parser detecta errores y los acumula; intenta recuperarse."""

    def test_falta_bloque_abre(self):
        # Sin /\ después del nombre del programa
        _, _, es = parsear("lab L muestra x : num;")
        self.assertTrue(len(es) > 0, "Debe haber al menos un error sintáctico")

    def test_declaracion_sin_dos_puntos(self):
        _, _, es = parsear("lab L /\\\nmuestra x num;\n\\/")
        self.assertTrue(len(es) > 0)

    def test_declaracion_sin_punto_coma(self):
        _, _, es = parsear("lab L /\\\nmuestra x : num\n\\/")
        self.assertTrue(len(es) > 0)

    def test_asignacion_sin_expresion(self):
        _, _, es = parsear("lab L /\\\nx = ;\n\\/")
        self.assertTrue(len(es) > 0)

    def test_recuperacion_continua_despues_de_error(self):
        # Error en la primera instrucción; la segunda debe parsearse.
        # Nota: 'y' es palabra clave en GenLen, se usa 'z' como identificador.
        codigo = "lab L /\\\nmuestra x num;\nmuestra z : num;\n\\/"
        ast, _, es = parsear(codigo)
        self.assertTrue(len(es) > 0, "Debe registrar el error")
        # El cuerpo aún contiene la declaración válida de z
        cuerpo = cuerpo_de(ast)
        nombres = [h.contenido for h in cuerpo.hijos if h.tipo == TipoNodo.DECLARACION]
        self.assertIn("z", nombres)


# ---------------------------------------------------------------------------
# 9. Integración con ejemplos reales
# ---------------------------------------------------------------------------

class TestEjemplosReales(unittest.TestCase):
    """Parseo sin errores de los archivos .gl de ejemplo."""

    EJEMPLOS_DIR = os.path.join(os.path.dirname(__file__), "..", "ejemplos")

    def _parsear_archivo(self, nombre: str):
        ruta = os.path.join(self.EJEMPLOS_DIR, nombre)
        with open(ruta, encoding="utf-8") as f:
            fuente = f.read()
        exp    = Explorador(fuente)
        tokens = exp.escanear()
        par    = Analizador(tokens)
        ast    = par.analizar()
        return exp.errores, par.errores, ast

    def test_ejemplo1_sin_errores(self):
        el, es, _ = self._parsear_archivo("ejemplo1.gl")
        self.assertFalse(el, f"Errores léxicos: {el}")
        self.assertFalse(es, f"Errores sintácticos: {es}")

    def test_ejemplo2_sin_errores(self):
        el, es, _ = self._parsear_archivo("ejemplo2.gl")
        self.assertFalse(el)
        self.assertFalse(es)

    def test_ejemplo3_sin_errores(self):
        el, es, _ = self._parsear_archivo("ejemplo3.gl")
        self.assertFalse(el)
        self.assertFalse(es)

    def test_ejemplo4_sin_errores(self):
        el, es, _ = self._parsear_archivo("ejemplo4.gl")
        self.assertFalse(el)
        self.assertFalse(es)

    def test_ejemplo5_sin_errores(self):
        el, es, _ = self._parsear_archivo("ejemplo5.gl")
        self.assertFalse(el)
        self.assertFalse(es)

    def test_ejemplo6_sin_errores(self):
        el, es, _ = self._parsear_archivo("ejemplo6.gl")
        self.assertFalse(el)
        self.assertFalse(es)

    def test_ejemplo7_sin_errores(self):
        el, es, _ = self._parsear_archivo("ejemplo7.gl")
        self.assertFalse(el)
        self.assertFalse(es)

    def test_ejemplo8_sin_errores(self):
        el, es, _ = self._parsear_archivo("ejemplo8.gl")
        self.assertFalse(el)
        self.assertFalse(es)

    def test_ejemplo1_ast_es_programa(self):
        _, _, ast = self._parsear_archivo("ejemplo1.gl")
        self.assertEqual(ast.tipo, TipoNodo.PROGRAMA)
        self.assertEqual(ast.contenido, "Ejemplo1")

    def test_ejemplo2_tiene_protocolo(self):
        _, _, ast = self._parsear_archivo("ejemplo2.gl")
        cuerpo = cuerpo_de(ast)
        tipos = [h.tipo for h in cuerpo.hijos]
        self.assertIn(TipoNodo.PROTOCOLO, tipos)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
