"""
parser.py - Analizador Sintáctico de descenso recursivo (LL(1)) para GenLen.

Gramática LL(1) en EBNF
═══════════════════════
programa         ::= "lab" IDENTIFICADOR BLOQUE_ABRE cuerpo BLOQUE_CIERRA EOF

cuerpo           ::= { instruccion }

instruccion      ::= declaracion
                   | protocolo_def
                   | instruccion_expr

declaracion      ::= "muestra" IDENTIFICADOR ":" tipo [ "=" expresion ] ";"

protocolo_def    ::= "protocolo" IDENTIFICADOR "(" [ lista_params ] ")"
                     BLOQUE_ABRE cuerpo BLOQUE_CIERRA

lista_params     ::= param { "," param }
param            ::= IDENTIFICADOR ":" tipo

instruccion_expr ::= IDENTIFICADOR instruccion_cola ";"
instruccion_cola ::= "=" expresion
                   | "(" [ lista_args ] ")" { "->" MECANISMO "(" [ lista_args ] ")" }
                   | "->" MECANISMO "(" [ lista_args ] ")" { "->" MECANISMO "(" [ lista_args ] ")" }

expresion        ::= expr_o
expr_o           ::= expr_y   { "o" expr_y   }
expr_y           ::= expr_comp { "y" expr_comp }
expr_comp        ::= expr_suma [ op_comp expr_suma ]
op_comp          ::= "==" | "!=" | "<" | "<=" | ">" | ">="
expr_suma        ::= expr_mult { ( "+" | "-" ) expr_mult }
expr_mult        ::= expr_unaria { ( "*" | "/" | "%" ) expr_unaria }
expr_unaria      ::= "-" expr_unaria | expr_postfija
expr_postfija    ::= expr_primaria { "->" MECANISMO "(" [ lista_args ] ")" }
expr_primaria    ::= NUMERO
                   | BOOLEANO
                   | "(" expresion ")"
                   | tipo cadena_genetica
                   | cadena_genetica
                   | IDENTIFICADOR [ "(" [ lista_args ] ")" ]

lista_args       ::= expresion { "," expresion }
tipo             ::= TIPO
cadena_genetica  ::= CADENA_ADN | CADENA_ARN | CADENA_PROTEINA

Propiedades LL(1)
─────────────────
- Sin ambigüedad: cada producción tiene su propio token de previsión.
- Sin recursividad izquierda: las producciones iterativas usan { ... }.
- Factorización izquierda aplicada a instruccion_cola y expr_postfija.
- Conjuntos FIRST disjuntos:
    instruccion  → "muestra" | "protocolo" | IDENTIFICADOR
    instruccion_cola → "=" | "(" | "->"
    expr_primaria → NUMERO | BOOLEANO | "(" | TIPO | CADENA_* | IDENTIFICADOR

Manejo de errores
─────────────────
- Errores sintácticos se acumulan en Parser.errores.
- Modo pánico: al detectar un error se saltan tokens hasta ';',
  BLOQUE_CIERRA o EOF para continuar el análisis.

Optimizaciones básicas (constant folding)
──────────────────────────────────────────
- La función doblar_constantes(nodo) evalúa en tiempo de compilación
  operaciones aritméticas entre literales numéricos.
  Ejemplo: 3 * 4  →  NUMERO[12]

GenLen - Lenguaje Genético
Curso: Compiladores e Intérpretes
"""

from __future__ import annotations
from typing import Optional

from .token import Token, TipoToken
from .nodo  import Nodo, TipoNodo


# ---------------------------------------------------------------------------
# Señal interna para el modo pánico
# ---------------------------------------------------------------------------

class _PanicMode(Exception):
    """Señal interna que activa el modo pánico en el parser."""
    def __init__(self, token: Token) -> None:
        self.token = token


# ---------------------------------------------------------------------------
# Excepción pública de error sintáctico
# ---------------------------------------------------------------------------

class ErrorSintactico(Exception):
    """Error sintáctico con información de posición."""

    def __init__(self, mensaje: str, linea: int, columna: int) -> None:
        self.mensaje = mensaje
        self.linea   = linea
        self.columna = columna
        super().__init__(
            f"[Error sintáctico] Línea {linea}, columna {columna}: {mensaje}"
        )


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Analizador:
    """
    Analizador Sintáctico de descenso recursivo LL(1) para GenLen.

    Consume la lista de tokens producida por el Explorador y construye
    el Árbol de Sintaxis Abstracta (AST).

    Uso:
        analizador = Analizador(tokens)
        ast        = analizador.analizar()
        # analizador.errores contiene los mensajes de error sintáctico
    """

    def __init__(self, tokens: list[Token]) -> None:
        """
        Inicializa el analizador con la lista de tokens.

        Parámetros:
            tokens : list[Token] - lista producida por Explorador.escanear()
        """
        self._tokens: list[Token] = tokens
        self._pos: int            = 0
        self.errores: list[str]   = []

    # ===================================================================
    # Helpers de navegación
    # ===================================================================

    def _actual(self) -> Token:
        """Retorna el token en la posición actual sin consumirlo."""
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        # Garantía: siempre hay un EOF al final
        return self._tokens[-1]

    def _avanzar(self) -> Token:
        """Consume y retorna el token actual."""
        tok = self._actual()
        if self._pos < len(self._tokens) - 1:
            self._pos += 1
        return tok

    def _es(self, tipo: TipoToken, lexema: Optional[str] = None) -> bool:
        """
        Comprueba si el token actual coincide con el tipo (y opcionalmente
        el lexema) indicados, sin consumirlo.
        """
        tok = self._actual()
        if tok.tipo != tipo:
            return False
        return lexema is None or tok.lexema == lexema

    def _verificar(self, tipo: TipoToken, lexema: Optional[str] = None) -> Token:
        """
        Verifica que el token actual sea del tipo (y opcionalmente lexema)
        esperado.  Si coincide, lo consume y lo retorna.
        Si no coincide, registra un error sintáctico y activa el modo pánico.
        """
        tok = self._actual()
        if tok.tipo == tipo and (lexema is None or tok.lexema == lexema):
            return self._avanzar()

        if lexema is not None:
            esperado = f'"{lexema}"'
        else:
            esperado = tipo.value

        self._registrar_error(
            f"Se esperaba {esperado}, se encontró '{tok.lexema}'",
            tok.linea,
            tok.columna,
        )
        raise _PanicMode(tok)

    # ===================================================================
    # Manejo de errores
    # ===================================================================

    def _registrar_error(self, mensaje: str, linea: int, columna: int) -> None:
        """Formatea y almacena un mensaje de error sintáctico."""
        texto = f"[Error sintáctico] Línea {linea}, columna {columna}: {mensaje}"
        self.errores.append(texto)

    def _recuperar(self) -> None:
        """
        Modo pánico: avanza hasta encontrar un token de sincronización
        (';', BLOQUE_CIERRA o EOF) para reanudar el análisis.

        Si encuentra ';' lo consume para posicionarse al inicio de la
        siguiente instrucción.
        """
        while not self._es(TipoToken.EOF) and not self._es(TipoToken.BLOQUE_CIERRA):
            if self._es(TipoToken.PUNTUACION, ";"):
                self._avanzar()   # consume el ';'
                return
            self._avanzar()

    # ===================================================================
    # Punto de entrada público
    # ===================================================================

    def analizar(self) -> Nodo:
        """
        Analiza el flujo completo de tokens y retorna el nodo raíz (PROGRAMA).

        Si hay errores, quedan en self.errores y el AST puede ser parcial.
        """
        try:
            ast = self._analizar_programa()
        except _PanicMode:
            # Error irrecuperable a nivel de programa (falta bloque-abre o bloque-cierra raiz).
            # Devolver un PROGRAMA vacío para que la ejecución no aborte.
            tok = self._actual()
            ast = Nodo(TipoNodo.PROGRAMA, "", tok.linea, tok.columna)
            ast.agregar_hijo(Nodo(TipoNodo.CUERPO, "", tok.linea, tok.columna))
        return ast

    # ===================================================================
    # Reglas gramaticales
    # ===================================================================

    # -------------------------------------------------------------------
    # programa ::= "lab" IDENTIFICADOR BLOQUE_ABRE cuerpo BLOQUE_CIERRA EOF
    # -------------------------------------------------------------------

    def _analizar_programa(self) -> Nodo:
        """
        programa ::= "lab" IDENTIFICADOR BLOQUE_ABRE cuerpo BLOQUE_CIERRA EOF
        """
        tok_lab = self._verificar(TipoToken.PALABRA_CLAVE, "lab")
        tok_nom = self._verificar(TipoToken.IDENTIFICADOR)
        self._verificar(TipoToken.BLOQUE_ABRE)

        nodo = Nodo(TipoNodo.PROGRAMA, tok_nom.lexema, tok_lab.linea, tok_lab.columna)
        nodo.agregar_hijo(self._analizar_cuerpo())

        self._verificar(TipoToken.BLOQUE_CIERRA)
        self._verificar(TipoToken.EOF)
        return nodo

    # -------------------------------------------------------------------
    # cuerpo ::= { instruccion }
    # -------------------------------------------------------------------

    def _analizar_cuerpo(self) -> Nodo:
        """
        cuerpo ::= { instruccion }

        Se producen nodos para todas las instrucciones válidas dentro del
        bloque abre/cierra.  Los errores se recuperan en modo panico.
        """
        tok = self._actual()
        cuerpo = Nodo(TipoNodo.CUERPO, "", tok.linea, tok.columna)

        while not self._es(TipoToken.BLOQUE_CIERRA) and not self._es(TipoToken.EOF):
            try:
                instr = self._analizar_instruccion()
                if instr is not None:
                    cuerpo.agregar_hijo(instr)
            except _PanicMode:
                self._recuperar()

        return cuerpo

    # -------------------------------------------------------------------
    # instruccion ::= declaracion | protocolo_def | instruccion_expr
    # -------------------------------------------------------------------

    def _analizar_instruccion(self) -> Optional[Nodo]:
        """
        instruccion ::= declaracion
                      | protocolo_def
                      | instruccion_expr

        Dispatching por el token de previsión:
          "muestra"   → declaracion
          "protocolo" → protocolo_def
          IDENTIFICADOR → instruccion_expr
          ERROR         → se omite y se avanza
        """
        # Saltar tokens de error léxico (ya reportados por el Explorador)
        while self._es(TipoToken.ERROR):
            self._avanzar()

        if self._es(TipoToken.BLOQUE_CIERRA) or self._es(TipoToken.EOF):
            return None

        tok = self._actual()

        if self._es(TipoToken.PALABRA_CLAVE, "muestra"):
            return self._analizar_declaracion()

        if self._es(TipoToken.PALABRA_CLAVE, "protocolo"):
            return self._analizar_protocolo()

        if self._es(TipoToken.IDENTIFICADOR):
            return self._analizar_instruccion_expr()

        # Token inesperado
        self._registrar_error(
            f"Se esperaba una instrucción (muestra, protocolo o identificador), "
            f"se encontró '{tok.lexema}'",
            tok.linea,
            tok.columna,
        )
        raise _PanicMode(tok)

    # -------------------------------------------------------------------
    # declaracion ::= "muestra" IDENTIFICADOR ":" tipo [ "=" expresion ] ";"
    # -------------------------------------------------------------------

    def _analizar_declaracion(self) -> Nodo:
        """
        declaracion ::= "muestra" IDENTIFICADOR ":" tipo [ "=" expresion ] ";"

        Ejemplos:
            muestra gen1 : adn = adn 'ATGCT';
            muestra arn1 : arn;
        """
        tok_muestra = self._verificar(TipoToken.PALABRA_CLAVE, "muestra")
        tok_nom     = self._verificar(TipoToken.IDENTIFICADOR)
        self._verificar(TipoToken.PUNTUACION, ":")
        tipo_nodo   = self._analizar_tipo()

        nodo = Nodo(TipoNodo.DECLARACION, tok_nom.lexema, tok_muestra.linea, tok_muestra.columna)
        nodo.agregar_hijo(tipo_nodo)

        if self._es(TipoToken.OPERADOR, "="):
            self._avanzar()    # consume "="
            nodo.agregar_hijo(self._analizar_expresion())

        self._verificar(TipoToken.PUNTUACION, ";")
        return nodo

    # -------------------------------------------------------------------
    # protocolo_def ::= "protocolo" IDENTIFICADOR "(" [lista_params] ")"
    #                   BLOQUE_ABRE cuerpo BLOQUE_CIERRA
    # -------------------------------------------------------------------

    def _analizar_protocolo(self) -> Nodo:
        """
        protocolo_def ::= "protocolo" IDENTIFICADOR "(" [ lista_params ] ")"
                          BLOQUE_ABRE cuerpo BLOQUE_CIERRA

        Ejemplo:
            protocolo editarYTraducir(g: adn, corte: adn) /[bloque] ... [/bloque]
        """
        tok_prot = self._verificar(TipoToken.PALABRA_CLAVE, "protocolo")
        tok_nom  = self._verificar(TipoToken.IDENTIFICADOR)
        self._verificar(TipoToken.PUNTUACION, "(")

        nodo = Nodo(TipoNodo.PROTOCOLO, tok_nom.lexema, tok_prot.linea, tok_prot.columna)

        # Parámetros formales (opcionales)
        if not self._es(TipoToken.PUNTUACION, ")"):
            nodo.agregar_hijo(self._analizar_lista_params())
        else:
            # Nodo vacío de parámetros para uniformidad
            tok = self._actual()
            nodo.agregar_hijo(Nodo(TipoNodo.LISTA_PARAMS, "", tok.linea, tok.columna))

        self._verificar(TipoToken.PUNTUACION, ")")
        self._verificar(TipoToken.BLOQUE_ABRE)
        nodo.agregar_hijo(self._analizar_cuerpo())
        self._verificar(TipoToken.BLOQUE_CIERRA)
        return nodo

    # -------------------------------------------------------------------
    # lista_params ::= param { "," param }
    # -------------------------------------------------------------------

    def _analizar_lista_params(self) -> Nodo:
        """lista_params ::= param { "," param }"""
        tok = self._actual()
        lista = Nodo(TipoNodo.LISTA_PARAMS, "", tok.linea, tok.columna)
        lista.agregar_hijo(self._analizar_param())
        while self._es(TipoToken.PUNTUACION, ","):
            self._avanzar()    # consume ","
            lista.agregar_hijo(self._analizar_param())
        return lista

    # -------------------------------------------------------------------
    # param ::= IDENTIFICADOR ":" tipo
    # -------------------------------------------------------------------

    def _analizar_param(self) -> Nodo:
        """param ::= IDENTIFICADOR ":" tipo"""
        tok_nom = self._verificar(TipoToken.IDENTIFICADOR)
        self._verificar(TipoToken.PUNTUACION, ":")
        tipo_nodo = self._analizar_tipo()
        nodo = Nodo(TipoNodo.PARAM, tok_nom.lexema, tok_nom.linea, tok_nom.columna)
        nodo.agregar_hijo(tipo_nodo)
        return nodo

    # -------------------------------------------------------------------
    # instruccion_expr ::= IDENTIFICADOR instruccion_cola ";"
    #
    # instruccion_cola ::= "=" expresion
    #                    | "(" [lista_args] ")" { "->" MECANISMO "(" [lista_args] ")" }
    #                    | "->" MECANISMO "(" [lista_args] ")" { "->" ... }
    # -------------------------------------------------------------------

    def _analizar_instruccion_expr(self) -> Nodo:
        """
        instruccion_expr ::= IDENTIFICADOR instruccion_cola ";"

        Tres formas según el token siguiente al identificador:
          "="  → asignación
          "("  → llamada a protocolo de usuario (standalone)
          "->" → cadena de mecanismos standalone
        """
        tok_id = self._verificar(TipoToken.IDENTIFICADOR)

        # --- Asignación ---
        if self._es(TipoToken.OPERADOR, "="):
            self._avanzar()    # consume "="
            expr = self._analizar_expresion()
            self._verificar(TipoToken.PUNTUACION, ";")
            nodo = Nodo(TipoNodo.ASIGNACION, tok_id.lexema, tok_id.linea, tok_id.columna)
            nodo.agregar_hijo(expr)
            return nodo

        # --- Llamada a protocolo de usuario como instrucción standalone ---
        if self._es(TipoToken.PUNTUACION, "("):
            self._avanzar()    # consume "("
            args = self._analizar_lista_args_o_vacio(tok_id)
            self._verificar(TipoToken.PUNTUACION, ")")
            llamada: Nodo = Nodo(
                TipoNodo.LLAMADA_PROTOCOLO,
                tok_id.lexema,
                tok_id.linea,
                tok_id.columna,
            )
            llamada.agregar_hijo(args)
            # Cadena opcional de mecanismos sobre el resultado
            llamada = self._analizar_cadena_mecanismos(llamada)
            self._verificar(TipoToken.PUNTUACION, ";")
            return llamada

        # --- Cadena de mecanismos standalone ---
        if self._es(TipoToken.OPERADOR, "->"):
            receptor: Nodo = Nodo(
                TipoNodo.IDENTIFICADOR,
                tok_id.lexema,
                tok_id.linea,
                tok_id.columna,
            )
            nodo = self._analizar_cadena_mecanismos(receptor)
            self._verificar(TipoToken.PUNTUACION, ";")
            return nodo

        # Token inesperado después del identificador
        tok = self._actual()
        self._registrar_error(
            f"Se esperaba '=', '(' o '->' después de '{tok_id.lexema}', "
            f"se encontró '{tok.lexema}'",
            tok.linea,
            tok.columna,
        )
        raise _PanicMode(tok)

    def _analizar_cadena_mecanismos(self, receptor: Nodo) -> Nodo:
        """
        Auxiliar: consume una o más cadenas  ->MECANISMO(args)  y construye
        los nodos LLAMADA_MECANISMO anidados de forma iterativa
        (izquierda a derecha).
        """
        nodo = receptor
        while self._es(TipoToken.OPERADOR, "->"):
            self._avanzar()    # consume "->"
            tok_mec = self._verificar(TipoToken.MECANISMO)
            self._verificar(TipoToken.PUNTUACION, "(")
            args = self._analizar_lista_args_o_vacio(tok_mec)
            self._verificar(TipoToken.PUNTUACION, ")")
            llamada = Nodo(
                TipoNodo.LLAMADA_MECANISMO,
                tok_mec.lexema,
                tok_mec.linea,
                tok_mec.columna,
            )
            llamada.agregar_hijo(nodo)    # receptor
            llamada.agregar_hijo(args)    # argumentos
            nodo = llamada
        return nodo

    def _analizar_lista_args_o_vacio(self, tok_ref: Token) -> Nodo:
        """
        Retorna un nodo LISTA_ARGS.  Si no hay argumentos, retorna uno vacío.
        """
        if self._es(TipoToken.PUNTUACION, ")"):
            return Nodo(TipoNodo.LISTA_ARGS, "", tok_ref.linea, tok_ref.columna)
        return self._analizar_lista_args()

    # ===================================================================
    # Expresiones (precedencia ascendente)
    # ===================================================================

    # -------------------------------------------------------------------
    # expresion ::= expr_o
    # -------------------------------------------------------------------

    def _analizar_expresion(self) -> Nodo:
        """expresion ::= expr_o"""
        return self._analizar_expr_o()

    # -------------------------------------------------------------------
    # expr_o ::= expr_y { "o" expr_y }
    # -------------------------------------------------------------------

    def _analizar_expr_o(self) -> Nodo:
        """expr_o ::= expr_y { "o" expr_y }"""
        izq = self._analizar_expr_y()
        while self._es(TipoToken.PALABRA_CLAVE, "o"):
            op  = self._avanzar()
            der = self._analizar_expr_y()
            nodo = Nodo(TipoNodo.BINARIA, "o", op.linea, op.columna)
            nodo.agregar_hijo(izq)
            nodo.agregar_hijo(der)
            izq = nodo
        return izq

    # -------------------------------------------------------------------
    # expr_y ::= expr_comp { "y" expr_comp }
    # -------------------------------------------------------------------

    def _analizar_expr_y(self) -> Nodo:
        """expr_y ::= expr_comp { "y" expr_comp }"""
        izq = self._analizar_expr_comp()
        while self._es(TipoToken.PALABRA_CLAVE, "y"):
            op  = self._avanzar()
            der = self._analizar_expr_comp()
            nodo = Nodo(TipoNodo.BINARIA, "y", op.linea, op.columna)
            nodo.agregar_hijo(izq)
            nodo.agregar_hijo(der)
            izq = nodo
        return izq

    # -------------------------------------------------------------------
    # expr_comp ::= expr_suma [ op_comp expr_suma ]
    # op_comp   ::= "==" | "!=" | "<" | "<=" | ">" | ">="
    # -------------------------------------------------------------------

    _OP_COMP = frozenset({"==", "!=", "<", "<=", ">", ">="})

    def _analizar_expr_comp(self) -> Nodo:
        """expr_comp ::= expr_suma [ op_comp expr_suma ]"""
        izq = self._analizar_expr_suma()
        if self._es(TipoToken.OPERADOR) and self._actual().lexema in self._OP_COMP:
            op  = self._avanzar()
            der = self._analizar_expr_suma()
            nodo = Nodo(TipoNodo.BINARIA, op.lexema, op.linea, op.columna)
            nodo.agregar_hijo(izq)
            nodo.agregar_hijo(der)
            return nodo
        return izq

    # -------------------------------------------------------------------
    # expr_suma ::= expr_mult { ( "+" | "-" ) expr_mult }
    # -------------------------------------------------------------------

    def _analizar_expr_suma(self) -> Nodo:
        """expr_suma ::= expr_mult { ( "+" | "-" ) expr_mult }"""
        izq = self._analizar_expr_mult()
        while self._es(TipoToken.OPERADOR) and self._actual().lexema in ("+", "-"):
            op  = self._avanzar()
            der = self._analizar_expr_mult()
            nodo = Nodo(TipoNodo.BINARIA, op.lexema, op.linea, op.columna)
            nodo.agregar_hijo(izq)
            nodo.agregar_hijo(der)
            izq = nodo
        return izq

    # -------------------------------------------------------------------
    # expr_mult ::= expr_unaria { ( "*" | "/" | "%" ) expr_unaria }
    # -------------------------------------------------------------------

    def _analizar_expr_mult(self) -> Nodo:
        """expr_mult ::= expr_unaria { ( "*" | "/" | "%" ) expr_unaria }"""
        izq = self._analizar_expr_unaria()
        while self._es(TipoToken.OPERADOR) and self._actual().lexema in ("*", "/", "%"):
            op  = self._avanzar()
            der = self._analizar_expr_unaria()
            nodo = Nodo(TipoNodo.BINARIA, op.lexema, op.linea, op.columna)
            nodo.agregar_hijo(izq)
            nodo.agregar_hijo(der)
            izq = nodo
        return izq

    # -------------------------------------------------------------------
    # expr_unaria ::= "-" expr_unaria | expr_postfija
    # -------------------------------------------------------------------

    def _analizar_expr_unaria(self) -> Nodo:
        """expr_unaria ::= "-" expr_unaria | expr_postfija"""
        if self._es(TipoToken.OPERADOR, "-"):
            op  = self._avanzar()
            operando = self._analizar_expr_unaria()
            nodo = Nodo(TipoNodo.UNARIA, "-", op.linea, op.columna)
            nodo.agregar_hijo(operando)
            return nodo
        return self._analizar_expr_postfija()

    # -------------------------------------------------------------------
    # expr_postfija ::= expr_primaria { "->" MECANISMO "(" [lista_args] ")" }
    # -------------------------------------------------------------------

    def _analizar_expr_postfija(self) -> Nodo:
        """
        expr_postfija ::= expr_primaria { "->" MECANISMO "(" [lista_args] ")" }

        Construye nodos LLAMADA_MECANISMO anidados (izquierda a derecha)
        para encadenamientos como:
            gen->transcribir()->traducir()
        """
        nodo = self._analizar_expr_primaria()
        return self._analizar_cadena_mecanismos(nodo)

    # -------------------------------------------------------------------
    # expr_primaria
    # -------------------------------------------------------------------

    def _analizar_expr_primaria(self) -> Nodo:
        """
        expr_primaria ::= NUMERO
                        | BOOLEANO
                        | "(" expresion ")"
                        | tipo cadena_genetica        (adn|arn|prot + literal)
                        | cadena_genetica              (literal sin prefijo)
                        | IDENTIFICADOR [ "(" [lista_args] ")" ]
        """
        tok = self._actual()

        # Número literal
        if tok.tipo == TipoToken.NUMERO:
            self._avanzar()
            return Nodo(TipoNodo.NUMERO, tok.lexema, tok.linea, tok.columna)

        # Booleano literal
        if tok.tipo == TipoToken.BOOLEANO:
            self._avanzar()
            return Nodo(TipoNodo.BOOLEANO, tok.lexema, tok.linea, tok.columna)

        # Expresión entre paréntesis
        if tok.tipo == TipoToken.PUNTUACION and tok.lexema == "(":
            self._avanzar()    # consume "("
            nodo = self._analizar_expresion()
            self._verificar(TipoToken.PUNTUACION, ")")
            return nodo

        # Literal genético con prefijo de tipo: adn 'ATGC', arn 'AUCG', prot 'MKL'
        if tok.tipo == TipoToken.TIPO and tok.lexema in ("adn", "arn", "prot"):
            self._avanzar()    # consume el tipo (no se incluye en el AST)
            return self._analizar_cadena_genetica()

        # Literal genético inferido (sin prefijo)
        if tok.tipo in (TipoToken.CADENA_ADN, TipoToken.CADENA_ARN, TipoToken.CADENA_PROTEINA):
            return self._analizar_cadena_genetica()

        # Identificador (variable o llamada a protocolo de usuario)
        if tok.tipo == TipoToken.IDENTIFICADOR:
            self._avanzar()
            if self._es(TipoToken.PUNTUACION, "("):
                # Llamada a protocolo de usuario como expresión
                self._avanzar()    # consume "("
                args = self._analizar_lista_args_o_vacio(tok)
                self._verificar(TipoToken.PUNTUACION, ")")
                nodo = Nodo(
                    TipoNodo.LLAMADA_PROTOCOLO,
                    tok.lexema,
                    tok.linea,
                    tok.columna,
                )
                nodo.agregar_hijo(args)
                return nodo
            return Nodo(TipoNodo.IDENTIFICADOR, tok.lexema, tok.linea, tok.columna)

        # Token inesperado
        self._registrar_error(
            f"Se esperaba una expresión, se encontró '{tok.lexema}'",
            tok.linea,
            tok.columna,
        )
        raise _PanicMode(tok)

    # -------------------------------------------------------------------
    # lista_args ::= expresion { "," expresion }
    # -------------------------------------------------------------------

    def _analizar_lista_args(self) -> Nodo:
        """lista_args ::= expresion { "," expresion }"""
        tok = self._actual()
        lista = Nodo(TipoNodo.LISTA_ARGS, "", tok.linea, tok.columna)
        lista.agregar_hijo(self._analizar_expresion())
        while self._es(TipoToken.PUNTUACION, ","):
            self._avanzar()    # consume ","
            lista.agregar_hijo(self._analizar_expresion())
        return lista

    # -------------------------------------------------------------------
    # tipo ::= TIPO
    # -------------------------------------------------------------------

    def _analizar_tipo(self) -> Nodo:
        """tipo ::= TIPO  (lexema: adn | arn | prot | num | bool)"""
        tok = self._verificar(TipoToken.TIPO)
        return Nodo(TipoNodo.TIPO, tok.lexema, tok.linea, tok.columna)

    # -------------------------------------------------------------------
    # cadena_genetica ::= CADENA_ADN | CADENA_ARN | CADENA_PROTEINA
    # -------------------------------------------------------------------

    def _analizar_cadena_genetica(self) -> Nodo:
        """cadena_genetica ::= CADENA_ADN | CADENA_ARN | CADENA_PROTEINA"""
        tok = self._actual()
        if tok.tipo == TipoToken.CADENA_ADN:
            self._avanzar()
            return Nodo(TipoNodo.CADENA_ADN, tok.lexema, tok.linea, tok.columna)
        if tok.tipo == TipoToken.CADENA_ARN:
            self._avanzar()
            return Nodo(TipoNodo.CADENA_ARN, tok.lexema, tok.linea, tok.columna)
        if tok.tipo == TipoToken.CADENA_PROTEINA:
            self._avanzar()
            return Nodo(TipoNodo.CADENA_PROTEINA, tok.lexema, tok.linea, tok.columna)

        self._registrar_error(
            f"Se esperaba una cadena genética (ADN, ARN o proteína), "
            f"se encontró '{tok.lexema}'",
            tok.linea,
            tok.columna,
        )
        raise _PanicMode(tok)


# ===========================================================================
# Optimización: Constant Folding
# ===========================================================================

_OP_ARITMETICOS = frozenset({"+", "-", "*", "/", "%"})


def doblar_constantes(nodo: Nodo) -> Nodo:
    """
    Pase de optimización sobre el AST: constant folding.

    Evalúa en tiempo de compilación las operaciones aritméticas cuyos dos
    operandos sean literales numéricos.

    Ejemplos:
        BINARIA[*](NUMERO[3], NUMERO[4])   →  NUMERO[12]
        BINARIA[+](NUMERO[2], NUMERO[2.5]) →  NUMERO[4.5]

    División y módulo por cero se dejan intactos (sin plegar).

    El recorrido es post-orden: se pliegan primero los sub-árboles
    antes de intentar plegar el nodo actual.
    """
    # Post-orden: optimizar primero los hijos
    nodo.hijos = [doblar_constantes(h) for h in nodo.hijos]

    if (
        nodo.tipo == TipoNodo.BINARIA
        and nodo.contenido in _OP_ARITMETICOS
        and len(nodo.hijos) == 2
    ):
        izq, der = nodo.hijos
        if izq.tipo == TipoNodo.NUMERO and der.tipo == TipoNodo.NUMERO:
            try:
                vi = float(izq.contenido)
                vd = float(der.contenido)
                op = nodo.contenido
                resultado: Optional[float] = None

                if op == "+":
                    resultado = vi + vd
                elif op == "-":
                    resultado = vi - vd
                elif op == "*":
                    resultado = vi * vd
                elif op == "/" and vd != 0:
                    resultado = vi / vd
                elif op == "%" and vd != 0:
                    resultado = vi % vd

                if resultado is not None:
                    # Representar como entero si no hay parte decimal
                    texto = str(int(resultado)) if resultado == int(resultado) else str(resultado)
                    return Nodo(TipoNodo.NUMERO, texto, izq.linea, izq.columna)
            except (ValueError, OverflowError):
                pass    # Si falla la evaluación, se deja el nodo original

    return nodo
