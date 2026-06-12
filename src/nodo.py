"""
nodo.py - Definición del Árbol de Sintaxis Abstracta (AST) para GenLen.

Cada nodo del AST contiene:
  - tipo     : TipoNodo  - categoria semantica del nodo
  - contenido: str       - valor textual (lexema, operador, nombre, etc.)
  - hijos    : list[Nodo]- sub-nodos directos
  - linea    : int       - linea en la fuente (para mensajes de error)
  - columna  : int       - columna en la fuente (para mensajes de error)

Los simbolos irrelevantes (parentesis, llaves, punto y coma, etc.) NO se
incluyen en el AST; solamente la estructura semantica queda representada.

GenLen - Lenguaje Genetico
Curso: Compiladores e Interpretes
"""

from __future__ import annotations
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Tipos de nodos
# ---------------------------------------------------------------------------

class TipoNodo(Enum):
    """
    Categorías semánticas de los nodos del AST de GenLen.

    Estructura del programa
    ───────────────────────
    PROGRAMA          lab <nombre> [/] cuerpo [/]
    CUERPO            secuencia de instrucciones dentro del bloque
    PROTOCOLO         definición de protocolo (función)
    LISTA_PARAMS      lista formal de parámetros
    PARAM             un parámetro: nombre : tipo

    Instrucciones
    ─────────────
    DECLARACION       muestra <nombre> : <tipo> [= <expr>] ;
    ASIGNACION        <nombre> = <expr> ;
    LLAMADA_MECANISMO <receptor>-><mecanismo>(<args>)  (encadenado o simple)
    LLAMADA_PROTOCOLO <nombre>(<args>)  como expresión o instrucción standalone

    Expresiones
    ───────────
    BINARIA           operación binaria: izquierda op derecha
    UNARIA            operación unaria: op operando
    LISTA_ARGS        lista de argumentos en una llamada

    Literales / Primarios
    ──────────────────────
    IDENTIFICADOR     nombre de variable / protocolo
    NUMERO            literal numérico
    BOOLEANO          literal booleano V / F
    CADENA_ADN        secuencia de nucleótidos ADN
    CADENA_ARN        secuencia de nucleótidos ARN
    CADENA_PROTEINA   secuencia de aminoácidos
    TIPO              nombre de tipo (adn, arn, prot, num, bool)
    """

    # Estructura del programa
    PROGRAMA          = "PROGRAMA"
    CUERPO            = "CUERPO"
    PROTOCOLO         = "PROTOCOLO"
    LISTA_PARAMS      = "LISTA_PARAMS"
    PARAM             = "PARAM"

    # Instrucciones
    DECLARACION       = "DECLARACION"
    ASIGNACION        = "ASIGNACION"
    LLAMADA_MECANISMO = "LLAMADA_MECANISMO"
    LLAMADA_PROTOCOLO = "LLAMADA_PROTOCOLO"

    # Expresiones
    BINARIA           = "BINARIA"
    UNARIA            = "UNARIA"
    LISTA_ARGS        = "LISTA_ARGS"

    # Literales / primarios
    IDENTIFICADOR     = "IDENTIFICADOR"
    NUMERO            = "NUMERO"
    BOOLEANO          = "BOOLEANO"
    CADENA_ADN        = "CADENA_ADN"
    CADENA_ARN        = "CADENA_ARN"
    CADENA_PROTEINA   = "CADENA_PROTEINA"
    TIPO              = "TIPO"


# ---------------------------------------------------------------------------
# Clase Nodo
# ---------------------------------------------------------------------------

class Nodo:
    """
    Nodo del Árbol de Sintaxis Abstracta (AST) de GenLen.

    Atributos:
        tipo      : TipoNodo   - categoría semántica
        contenido : str        - valor textual asociado al nodo
        hijos     : list[Nodo] - sub-nodos
        linea     : int        - línea en la fuente (base 1)
        columna   : int        - columna en la fuente (base 1)
    """

    def __init__(
        self,
        tipo: TipoNodo,
        contenido: str = "",
        linea: int = 0,
        columna: int = 0,
    ) -> None:
        self.tipo: TipoNodo   = tipo
        self.contenido: str   = contenido
        self.hijos: list[Nodo] = []
        self.linea: int       = linea
        self.columna: int     = columna
        # Campos de decorado (rellenados por el Verificador)
        self.tipo_dato: Optional[str]  = None
        self.definicion: Optional[Nodo] = None

    # ------------------------------------------------------------------
    # Mutación
    # ------------------------------------------------------------------

    def agregar_hijo(self, hijo: Nodo) -> None:
        """Agrega un sub-nodo al final de la lista de hijos."""
        self.hijos.append(hijo)

    # ------------------------------------------------------------------
    # Representación
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        if self.contenido:
            return f"Nodo({self.tipo.value}, '{self.contenido}')"
        return f"Nodo({self.tipo.value})"

    def imprimir(self, nivel: int = 0, decorado: bool = False) -> str:
        """
        Retorna una representación textual con sangría del árbol.

        Con decorado=True muestra también el tipo inferido y la referencia
        a la definición de cada nodo (formato <tipo_dato, def@L:C>).
        """
        def _info(nodo: Nodo) -> str:
            texto = nodo.tipo.value
            if nodo.contenido:
                texto += f"  [{nodo.contenido}]"

            if decorado:
                partes = []
                if nodo.tipo_dato:
                    partes.append(f"tipo:{nodo.tipo_dato}")
                if nodo.definicion is not None:
                    partes.append(
                        f"def@{nodo.definicion.linea}:{nodo.definicion.columna}"
                    )
                if partes:
                    texto += f"  <{', '.join(partes)}>"
            return texto

        def _imprimir(
            nodo: Nodo,
            prefijo: str,
            es_ultimo: bool,
            raiz: bool,
        ) -> list[str]:
            if raiz:
                lineas = [_info(nodo)]
                prefijo_hijos = ""
            else:
                rama = "└── " if es_ultimo else "├── "
                lineas = [prefijo + rama + _info(nodo)]
                prefijo_hijos = prefijo + ("    " if es_ultimo else "│   ")

            for i, hijo in enumerate(nodo.hijos):
                lineas.extend(
                    _imprimir(
                        hijo,
                        prefijo_hijos,
                        i == len(nodo.hijos) - 1,
                        False,
                    )
                )
            return lineas

        return "\n".join(_imprimir(self, "  " * nivel, True, nivel == 0))
