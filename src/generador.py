"""
generador.py - Generador de código Python para GenLen.

Recorre el AST decorado usando el patrón Visitante y produce código Python 3.8+.
El archivo generado incluye un bloque de runtime con las funciones biológicas
y a continuación el código transpilado del programa GenLen.

GenLen - Lenguaje Genético
Curso: Compiladores e Intérpretes
"""

from __future__ import annotations

from .nodo import Nodo, TipoNodo


# ---------------------------------------------------------------------------
# Runtime embebido — se escribe al inicio de cada archivo generado
# ---------------------------------------------------------------------------

_RUNTIME = '''\
# ─────────────────────────────────────────────────────────────────────────────
# GenLen Runtime  ·  funciones biológicas integradas
# ─────────────────────────────────────────────────────────────────────────────
import random as _random

_CODON_TABLE = {
    "AUU": "I", "AUC": "I", "AUA": "I",
    "AUG": "M",
    "ACU": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "AAU": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "AGU": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "CUU": "L", "CUC": "L", "CUA": "L", "CUG": "L",
    "CCU": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "CAU": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "CGU": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "GUU": "V", "GUC": "V", "GUA": "V", "GUG": "V",
    "GCU": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "GAU": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "GGU": "G", "GGC": "G", "GGA": "G", "GGG": "G",
    "UUU": "F", "UUC": "F", "UUA": "L", "UUG": "L",
    "UCU": "S", "UCC": "S", "UCA": "S", "UCG": "S",
    "UAU": "Y", "UAC": "Y", "UAA": "*", "UAG": "*",
    "UGU": "C", "UGC": "C", "UGA": "*", "UGG": "W",
}

_ADN_BASES  = list("AGCT")
_ARN_BASES  = list("AGCU")
_PROT_AA    = list("ACDEFGHIKLMNPQRSTVWY")


def _transcribir(seq: str) -> str:
    return seq.replace("T", "U")


def _traducir(seq: str) -> str:
    aa = []
    for i in range(0, len(seq) - 2, 3):
        codon = seq[i : i + 3]
        residuo = _CODON_TABLE.get(codon, "?")
        if residuo == "*":
            break
        aa.append(residuo)
    return "".join(aa) or "M"


def _mutar(seq: str) -> str:
    if not seq:
        return seq
    chars = set(seq)
    if chars <= set("AGCT"):
        pool = _ADN_BASES
    elif chars <= set("AGCU"):
        pool = _ARN_BASES
    else:
        pool = _PROT_AA
    idx    = _random.randint(0, len(seq) - 1)
    nuevas = [b for b in pool if b != seq[idx]]
    nueva  = _random.choice(nuevas) if nuevas else seq[idx]
    return seq[:idx] + nueva + seq[idx + 1 :]


def _cas9(seq: str, guia: str) -> str:
    idx = seq.find(guia)
    if idx >= 0:
        return seq[:idx] + seq[idx + len(guia) :]
    return seq


def _alinear(s1: str, s2: str) -> str:
    score = sum(a == b for a, b in zip(s1, s2))
    return s1 if score >= len(s1) // 2 else s2


def _modelar(seq: str) -> str:
    return seq


def _docking(p1: str, p2: str) -> str:
    mitad1 = p1[: max(1, len(p1) // 2)]
    mitad2 = p2[: max(1, len(p2) // 2)]
    return mitad1 + mitad2


def _mostrar(val):
    print(val)
    return val


# ─────────────────────────────────────────────────────────────────────────────
# Código generado por GenLen
# ─────────────────────────────────────────────────────────────────────────────
'''


# ---------------------------------------------------------------------------
# Generador de código — patrón Visitante
# ---------------------------------------------------------------------------

class Generador:
    """
    Generador de código Python para GenLen.

    Uso:
        gen    = Generador()
        codigo = gen.generar(ast)
        with open("salida.py", "w", encoding="utf-8") as f:
            f.write(codigo)
    """

    # Mapeo de operadores GenLen → Python
    _OP_PY = {
        "y": "and",  "o": "or",
        "+": "+",    "-": "-",  "*": "*",  "/": "/",  "%": "%",
        "==": "==",  "!=": "!=",
        "<":  "<",   "<=": "<=",
        ">":  ">",   ">=": ">=",
    }

    # Valores por defecto según el tipo
    _DEFAULT = {
        "num":  "0",
        "bool": "False",
        "adn":  '""',
        "arn":  '""',
        "prot": '""',
    }

    def __init__(self) -> None:
        self._lineas: list[str] = []
        self._nivel: int = 0

    # -----------------------------------------------------------------------
    # Interfaz pública
    # -----------------------------------------------------------------------

    def generar(self, ast: Nodo) -> str:
        self._lineas = []
        self._nivel  = 0
        self._visitar(ast)
        return "\n".join(self._lineas) + "\n"

    # -----------------------------------------------------------------------
    # Helpers de emisión
    # -----------------------------------------------------------------------

    def _emit(self, linea: str) -> None:
        self._lineas.append("    " * self._nivel + linea)

    def _emit_raw(self, linea: str) -> None:
        self._lineas.append(linea)

    # -----------------------------------------------------------------------
    # Despacho
    # -----------------------------------------------------------------------

    def _visitar(self, nodo: Nodo) -> str:
        nombre_metodo = "_visitar_" + nodo.tipo.value.lower()
        metodo = getattr(self, nombre_metodo, lambda n: "")
        return metodo(nodo)

    # -----------------------------------------------------------------------
    # Estructura del programa
    # -----------------------------------------------------------------------

    def _visitar_programa(self, nodo: Nodo) -> str:
        self._emit_raw(_RUNTIME)
        self._emit_raw(f"# Programa: {nodo.contenido}")
        self._emit_raw("")
        self._visitar(nodo.hijos[0])
        return ""

    def _visitar_cuerpo(self, nodo: Nodo) -> str:
        for hijo in nodo.hijos:
            # Llamadas como sentencias deben emitirse directamente
            if hijo.tipo in (TipoNodo.LLAMADA_PROTOCOLO, TipoNodo.LLAMADA_MECANISMO):
                expr = self._visitar(hijo)
                self._emit(expr)
            else:
                self._visitar(hijo)
        return ""

    # -----------------------------------------------------------------------
    # Declaración
    # -----------------------------------------------------------------------

    def _visitar_declaracion(self, nodo: Nodo) -> str:
        nombre = nodo.contenido
        tipo   = nodo.hijos[0].contenido

        if len(nodo.hijos) > 1:
            valor = self._visitar(nodo.hijos[1])
        else:
            valor = self._DEFAULT.get(tipo, "None")

        self._emit(f"{nombre} = {valor}  # {tipo}")
        return ""

    # -----------------------------------------------------------------------
    # Protocolo → función Python
    # -----------------------------------------------------------------------

    def _visitar_protocolo(self, nodo: Nodo) -> str:
        nombre = nodo.contenido
        params = nodo.hijos[0]
        cuerpo = nodo.hijos[1]

        param_strs = [p.contenido for p in params.hijos]
        self._emit(f"def {nombre}({', '.join(param_strs)}):")

        self._nivel += 1
        if not cuerpo.hijos:
            self._emit("pass")
        else:
            self._visitar(cuerpo)
        self._nivel -= 1
        self._emit_raw("")
        return ""

    # -----------------------------------------------------------------------
    # Asignación
    # -----------------------------------------------------------------------

    def _visitar_asignacion(self, nodo: Nodo) -> str:
        nombre = nodo.contenido
        valor  = self._visitar(nodo.hijos[0])
        self._emit(f"{nombre} = {valor}")
        return ""

    # -----------------------------------------------------------------------
    # Llamada a protocolo
    # -----------------------------------------------------------------------

    def _visitar_llamada_protocolo(self, nodo: Nodo) -> str:
        nombre    = nodo.contenido
        args      = nodo.hijos[0]
        arg_strs  = [self._visitar(a) for a in args.hijos]
        return f"{nombre}({', '.join(arg_strs)})"

    # -----------------------------------------------------------------------
    # Llamada a mecanismo
    # -----------------------------------------------------------------------

    def _visitar_llamada_mecanismo(self, nodo: Nodo) -> str:
        mecanismo = nodo.contenido
        receptor  = self._visitar(nodo.hijos[0])
        args      = nodo.hijos[1]
        arg_strs  = [self._visitar(a) for a in args.hijos]

        todos = [receptor] + arg_strs
        return f"_{mecanismo}({', '.join(todos)})"

    # -----------------------------------------------------------------------
    # Expresiones
    # -----------------------------------------------------------------------

    def _visitar_binaria(self, nodo: Nodo) -> str:
        op  = self._OP_PY.get(nodo.contenido, nodo.contenido)
        izq = self._visitar(nodo.hijos[0])
        der = self._visitar(nodo.hijos[1])
        return f"({izq} {op} {der})"

    def _visitar_unaria(self, nodo: Nodo) -> str:
        operando = self._visitar(nodo.hijos[0])
        return f"(-{operando})"

    # -----------------------------------------------------------------------
    # Literales
    # -----------------------------------------------------------------------

    def _visitar_identificador(self, nodo: Nodo) -> str:
        return nodo.contenido

    def _visitar_numero(self, nodo: Nodo) -> str:
        return nodo.contenido

    def _visitar_booleano(self, nodo: Nodo) -> str:
        return "True" if nodo.contenido == "V" else "False"

    def _visitar_cadena_adn(self, nodo: Nodo) -> str:
        return f'"{nodo.contenido}"'

    def _visitar_cadena_arn(self, nodo: Nodo) -> str:
        return f'"{nodo.contenido}"'

    def _visitar_cadena_proteina(self, nodo: Nodo) -> str:
        return f'"{nodo.contenido}"'
