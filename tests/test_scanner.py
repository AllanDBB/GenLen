"""
test_scanner.py - Pruebas unitarias para el explorador léxico de GenLen.

Cubre:
  - Palabras clave y tipos
  - Identificadores
  - Literales numéricos (entero y decimal)
  - Cadenas genéticas (ADN, ARN, PROTEÍNA) y su validación
  - Operadores de uno y dos caracteres
  - Delimitadores de bloque /\ y \/
  - Comentarios (deben ser ignorados)
  - Booleanos V y F
  - Mecanismos biológicos
  - Manejo de errores léxicos

GenLen - Lenguaje Genético
Curso: Compiladores e Intérpretes
"""

import sys
import os

# Agregar el directorio raíz al path para poder importar src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from src.explorador import Explorador
from src.token import TipoToken


def escanear(codigo: str):
    """Ayudante: escanea `codigo` y retorna (tokens_sin_eof, errores)."""
    exp = Explorador(codigo)
    tokens = exp.escanear()
    sin_eof = [t for t in tokens if t.tipo != TipoToken.EOF]
    return sin_eof, exp.errores


class TestPalabrasClaveYTipos(unittest.TestCase):
    """Pruebas para palabras clave: lab, muestra, protocolo, y, o."""

    def test_lab(self):
        tokens, errores = escanear("lab")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].tipo, TipoToken.PALABRA_CLAVE)
        self.assertEqual(tokens[0].lexema, "lab")
        self.assertFalse(errores)

    def test_muestra(self):
        tokens, _ = escanear("muestra")
        self.assertEqual(tokens[0].tipo, TipoToken.PALABRA_CLAVE)
        self.assertEqual(tokens[0].lexema, "muestra")

    def test_protocolo(self):
        tokens, _ = escanear("protocolo")
        self.assertEqual(tokens[0].tipo, TipoToken.PALABRA_CLAVE)

    def test_operadores_logicos_y_o(self):
        tokens, _ = escanear("y o")
        self.assertEqual(tokens[0].tipo, TipoToken.PALABRA_CLAVE)
        self.assertEqual(tokens[0].lexema, "y")
        self.assertEqual(tokens[1].tipo, TipoToken.PALABRA_CLAVE)
        self.assertEqual(tokens[1].lexema, "o")

    def test_tipos(self):
        for tipo_kw in ("adn", "arn", "prot", "num", "bool"):
            with self.subTest(tipo=tipo_kw):
                tokens, _ = escanear(tipo_kw)
                self.assertEqual(tokens[0].tipo, TipoToken.TIPO)
                self.assertEqual(tokens[0].lexema, tipo_kw)


class TestBooleanos(unittest.TestCase):
    """Pruebas para los literales booleanos V y F."""

    def test_verdadero(self):
        tokens, errores = escanear("V")
        self.assertEqual(tokens[0].tipo, TipoToken.BOOLEANO)
        self.assertEqual(tokens[0].lexema, "V")
        self.assertFalse(errores)

    def test_falso(self):
        tokens, errores = escanear("F")
        self.assertEqual(tokens[0].tipo, TipoToken.BOOLEANO)
        self.assertEqual(tokens[0].lexema, "F")
        self.assertFalse(errores)

    def test_v_mayuscula_en_identificador_no_es_booleano(self):
        # 'Va' es identificador, no booleano
        tokens, _ = escanear("Va")
        self.assertEqual(tokens[0].tipo, TipoToken.IDENTIFICADOR)
        self.assertEqual(tokens[0].lexema, "Va")


class TestMecanismos(unittest.TestCase):
    """Pruebas para los mecanismos biológicos."""

    def test_todos_los_mecanismos(self):
        mecanismos = [
            "transcribir", "traducir", "mutar",
            "cas9", "alinear", "modelar", "docking",
        ]
        for m in mecanismos:
            with self.subTest(mecanismo=m):
                tokens, _ = escanear(m)
                self.assertEqual(tokens[0].tipo, TipoToken.MECANISMO)
                self.assertEqual(tokens[0].lexema, m)


class TestIdentificadores(unittest.TestCase):
    """Pruebas para identificadores definidos por el usuario."""

    def test_identificador_simple(self):
        tokens, _ = escanear("gen1")
        self.assertEqual(tokens[0].tipo, TipoToken.IDENTIFICADOR)
        self.assertEqual(tokens[0].lexema, "gen1")

    def test_identificador_con_guion_bajo(self):
        tokens, _ = escanear("gen_base")
        self.assertEqual(tokens[0].tipo, TipoToken.IDENTIFICADOR)
        self.assertEqual(tokens[0].lexema, "gen_base")

    def test_identificador_empieza_guion_bajo(self):
        tokens, _ = escanear("_aux")
        self.assertEqual(tokens[0].tipo, TipoToken.IDENTIFICADOR)
        self.assertEqual(tokens[0].lexema, "_aux")

    def test_identificador_mixto(self):
        tokens, _ = escanear("MiniLab")
        self.assertEqual(tokens[0].tipo, TipoToken.IDENTIFICADOR)
        self.assertEqual(tokens[0].lexema, "MiniLab")


class TestNumeros(unittest.TestCase):
    """Pruebas para literales numéricos."""

    def test_entero(self):
        tokens, errores = escanear("42")
        self.assertEqual(tokens[0].tipo, TipoToken.NUMERO)
        self.assertEqual(tokens[0].lexema, "42")
        self.assertFalse(errores)

    def test_decimal(self):
        tokens, errores = escanear("3.14")
        self.assertEqual(tokens[0].tipo, TipoToken.NUMERO)
        self.assertEqual(tokens[0].lexema, "3.14")
        self.assertFalse(errores)

    def test_cero(self):
        tokens, _ = escanear("0")
        self.assertEqual(tokens[0].lexema, "0")

    def test_numero_largo(self):
        tokens, _ = escanear("1234567890")
        self.assertEqual(tokens[0].lexema, "1234567890")


class TestCadenasGeneticas(unittest.TestCase):
    """Pruebas para cadenas genéticas ADN, ARN y PROTEÍNA."""

    def test_cadena_adn_con_contexto(self):
        tokens, errores = escanear("adn 'ATGCGT'")
        self.assertFalse(errores)
        self.assertEqual(tokens[1].tipo, TipoToken.CADENA_ADN)
        self.assertEqual(tokens[1].lexema, "ATGCGT")

    def test_cadena_arn_con_contexto(self):
        tokens, errores = escanear("arn 'AUGCAU'")
        self.assertFalse(errores)
        self.assertEqual(tokens[1].tipo, TipoToken.CADENA_ARN)
        self.assertEqual(tokens[1].lexema, "AUGCAU")

    def test_cadena_proteina_con_contexto(self):
        tokens, errores = escanear("prot 'MCHHHHH'")
        self.assertFalse(errores)
        self.assertEqual(tokens[1].tipo, TipoToken.CADENA_PROTEINA)
        self.assertEqual(tokens[1].lexema, "MCHHHHH")

    def test_cadena_adn_sin_contexto_infiere_adn(self):
        # Sin contexto, 'ATGCGT' solo tiene A/T/G/C -> infiere ADN
        tokens, errores = escanear("'ATGCGT'")
        self.assertFalse(errores)
        self.assertEqual(tokens[0].tipo, TipoToken.CADENA_ADN)

    def test_cadena_arn_sin_contexto_infiere_arn(self):
        # 'AUGCAU' tiene U -> infiere ARN
        tokens, errores = escanear("'AUGCAU'")
        self.assertFalse(errores)
        self.assertEqual(tokens[0].tipo, TipoToken.CADENA_ARN)

    def test_cadena_adn_normaliza_a_mayusculas(self):
        # La entrada en minúsculas se normaliza
        tokens, errores = escanear("adn 'atgcgt'")
        self.assertFalse(errores)
        self.assertEqual(tokens[1].lexema, "ATGCGT")

    def test_error_adn_con_caracter_invalido(self):
        _, errores = escanear("adn 'ATXYZ'")
        self.assertTrue(errores)
        self.assertIn("inválidos", errores[0])

    def test_error_arn_con_t(self):
        # T no es válido en ARN
        _, errores = escanear("arn 'ATGCGT'")
        self.assertTrue(errores)

    def test_error_cadena_vacia(self):
        _, errores = escanear("adn ''")
        self.assertTrue(errores)
        self.assertIn("vacía", errores[0])

    def test_error_cadena_no_cerrada(self):
        _, errores = escanear("adn 'ATGCGT\n")
        self.assertTrue(errores)
        self.assertIn("no cerrada", errores[0])


class TestOperadores(unittest.TestCase):
    """Pruebas para todos los operadores del lenguaje."""

    def test_operadores_aritmeticos(self):
        for op in ("+", "-", "*", "/", "%"):
            with self.subTest(op=op):
                tokens, errores = escanear(op)
                self.assertFalse(errores)
                self.assertEqual(tokens[0].tipo, TipoToken.OPERADOR)
                self.assertEqual(tokens[0].lexema, op)

    def test_operadores_comparacion(self):
        for op in ("==", "!=", "<", "<=", ">", ">="):
            with self.subTest(op=op):
                tokens, errores = escanear(op)
                self.assertFalse(errores)
                self.assertEqual(tokens[0].tipo, TipoToken.OPERADOR)
                self.assertEqual(tokens[0].lexema, op)

    def test_asignacion(self):
        tokens, _ = escanear("=")
        self.assertEqual(tokens[0].tipo, TipoToken.OPERADOR)
        self.assertEqual(tokens[0].lexema, "=")

    def test_flecha_mecanismo(self):
        tokens, errores = escanear("->")
        self.assertFalse(errores)
        self.assertEqual(tokens[0].tipo, TipoToken.OPERADOR)
        self.assertEqual(tokens[0].lexema, "->")

    def test_menos_solo_no_es_flecha(self):
        # '-' solo es operador aritmético, no flecha
        tokens, _ = escanear("- 5")
        self.assertEqual(tokens[0].lexema, "-")
        self.assertEqual(tokens[1].lexema, "5")


class TestDelimitadoresBloques(unittest.TestCase):
    """Pruebas para los delimitadores de bloque /\\ y \\/."""

    def test_bloque_abre(self):
        tokens, errores = escanear("/\\")
        self.assertFalse(errores)
        self.assertEqual(tokens[0].tipo, TipoToken.BLOQUE_ABRE)
        self.assertEqual(tokens[0].lexema, "/\\")

    def test_bloque_cierra(self):
        tokens, errores = escanear("\\/")
        self.assertFalse(errores)
        self.assertEqual(tokens[0].tipo, TipoToken.BLOQUE_CIERRA)
        self.assertEqual(tokens[0].lexema, "\\/")

    def test_bloque_abre_y_cierra(self):
        tokens, errores = escanear("/\\ \\/")
        self.assertFalse(errores)
        self.assertEqual(tokens[0].tipo, TipoToken.BLOQUE_ABRE)
        self.assertEqual(tokens[1].tipo, TipoToken.BLOQUE_CIERRA)


class TestPuntuacion(unittest.TestCase):
    """Pruebas para la puntuación del lenguaje."""

    def test_todos_los_signos(self):
        signos = {"(": "(", ")": ")", ":": ":", ";": ";", ",": ","}
        for sig, esperado in signos.items():
            with self.subTest(signo=sig):
                tokens, errores = escanear(sig)
                self.assertFalse(errores)
                self.assertEqual(tokens[0].tipo, TipoToken.PUNTUACION)
                self.assertEqual(tokens[0].lexema, esperado)


class TestComentarios(unittest.TestCase):
    """Los comentarios deben ser ignorados por el explorador."""

    def test_comentario_genera_cero_tokens(self):
        tokens, errores = escanear("// esto es un comentario")
        self.assertFalse(errores)
        self.assertEqual(len(tokens), 0)

    def test_comentario_no_afecta_siguiente_linea(self):
        tokens, errores = escanear("// ignorar\nlab")
        self.assertFalse(errores)
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].lexema, "lab")


class TestPosicion(unittest.TestCase):
    """Pruebas de tracking de línea y columna."""

    def test_columna_inicial(self):
        tokens, _ = escanear("lab")
        self.assertEqual(tokens[0].linea, 1)
        self.assertEqual(tokens[0].columna, 1)

    def test_segunda_linea(self):
        tokens, _ = escanear("lab\nMiniLab")
        # 'MiniLab' está en la línea 2
        self.assertEqual(tokens[1].linea, 2)
        self.assertEqual(tokens[1].columna, 1)

    def test_columna_despues_de_espacio(self):
        tokens, _ = escanear("lab MiniLab")
        # 'MiniLab' empieza en columna 5 (lab=col1, espacio=col4, M=col5)
        self.assertEqual(tokens[1].columna, 5)


class TestErrores(unittest.TestCase):
    """Pruebas para el manejo de errores léxicos."""

    def test_caracter_desconocido_arroba(self):
        _, errores = escanear("@")
        self.assertTrue(errores)
        self.assertIn("@", errores[0])

    def test_exclamacion_sola(self):
        _, errores = escanear("!")
        self.assertTrue(errores)
        self.assertIn("!", errores[0])

    def test_error_no_detiene_escaneo(self):
        # Después de un error, el scanner sigue y emite los tokens válidos
        tokens, errores = escanear("@ lab")
        self.assertTrue(errores)
        tipos = [t.tipo for t in tokens]
        self.assertIn(TipoToken.ERROR, tipos)
        self.assertIn(TipoToken.PALABRA_CLAVE, tipos)

    def test_posicion_en_error(self):
        _, errores = escanear("lab\n@ algo")
        # El '@' está en línea 2, columna 1
        self.assertIn("Línea 2", errores[0])
        self.assertIn("columna 1", errores[0])


class TestProgramaCompleto(unittest.TestCase):
    """Prueba de integración con un programa GenLen real."""

    CODIGO = """\
// Declaración y transcripción
lab Ejemplo1
/\\
    muestra gen1 : adn = adn 'ATGCGT';
    muestra arn1 : arn;
    arn1 = gen1->transcribir();
\\/
"""

    def test_sin_errores(self):
        _, errores = escanear(self.CODIGO)
        self.assertFalse(errores, f"No se esperaban errores: {errores}")

    def test_estructura_de_tokens(self):
        tokens, _ = escanear(self.CODIGO)
        tipos = [t.tipo for t in tokens]
        # Debe haber: PALABRA_CLAVE(lab), IDENTIFICADOR(Ejemplo1), BLOQUE_ABRE, ...
        self.assertIn(TipoToken.PALABRA_CLAVE, tipos)
        self.assertIn(TipoToken.IDENTIFICADOR, tipos)
        self.assertIn(TipoToken.BLOQUE_ABRE, tipos)
        self.assertIn(TipoToken.BLOQUE_CIERRA, tipos)
        self.assertIn(TipoToken.CADENA_ADN, tipos)
        self.assertIn(TipoToken.OPERADOR, tipos)
        self.assertIn(TipoToken.MECANISMO, tipos)

    def test_cantidad_tokens(self):
        tokens, _ = escanear(self.CODIGO)
        # lab, Ejemplo1, /\, muestra, gen1, :, adn, =, adn, ATGCGT, ;,
        # muestra, arn1, :, arn, ;,
        # arn1, =, gen1, ->, transcribir, (, ), ;, \/
        self.assertEqual(len(tokens), 25)


if __name__ == "__main__":
    unittest.main(verbosity=2)
