"""
explorador.py - Implementación del explorador léxico (Scanner) para GenLen.

El explorador recibe el texto fuente y produce una lista de tokens
según la gramática EBNF definida en la especificación de GenLen.

Reglas de la gramática relevantes para el scanner (sección 3.11 y 3.12):
  IDENTIFICADOR  ::= [a-zA-Z_][a-zA-Z0-9_]*
  NUMERO         ::= [0-9]+(\\.[0-9]+)?
  CADENA_ADN     ::= "'" [AGCT]+ "'"
  CADENA_ARN     ::= "'" [AUCG]+ "'"
  CADENA_PROTEINA::= "'" [ACDEFGHIKLMNPQRSTVWY]+ "'"
  COMENTARIO     ::= "//" [^\\n]*

GenLen - Lenguaje Genético
Curso: Compiladores e Intérpretes
"""

from .token import Token, TipoToken


# ---------------------------------------------------------------------------
# Conjuntos de palabras reservadas
# ---------------------------------------------------------------------------

# Palabras clave estructurales del lenguaje
PALABRAS_CLAVE: set[str] = {"lab", "muestra", "protocolo"}

# Operadores lógicos escritos como palabras
OP_LOGICOS: set[str] = {"y", "o"}

# Tipos de datos primitivos del lenguaje
TIPOS: set[str] = {"adn", "arn", "prot", "num", "bool"}

# Mecanismos biológicos (métodos intrínsecos de los tipos genéticos)
MECANISMOS: set[str] = {
    "transcribir", "traducir", "mutar",
    "cas9", "alinear", "modelar", "docking",
}

# Literales booleanos
BOOLEANOS: set[str] = {"V", "F"}

# ---------------------------------------------------------------------------
# Conjuntos de caracteres válidos para cada tipo de cadena genética
# ---------------------------------------------------------------------------

ADN_CHARS  = frozenset("AGCT")
ARN_CHARS  = frozenset("AUCG")
PROT_CHARS = frozenset("ACDEFGHIKLMNPQRSTVWY")


# ---------------------------------------------------------------------------
# Explorador
# ---------------------------------------------------------------------------

class Explorador:
    """
    Explorador léxico (Scanner) para GenLen.

    Transforma el texto fuente en una lista de tokens.
    Todos los errores léxicos se acumulan en `self.errores`
    y simultáneamente se emite un token de tipo ERROR para
    mantener la lista completa con su posición.

    Uso:
        explorer = Explorador(codigo_fuente)
        tokens   = explorer.escanear()
        # explorer.errores contiene los mensajes de error (si los hay)
    """

    def __init__(self, fuente: str):
        """
        Inicializa el explorador con el texto fuente.

        Parámetros:
            fuente : str - contenido completo del archivo a analizar
        """
        self.fuente: str        = fuente
        self.pos: int           = 0       # posición actual en la cadena
        self.linea: int         = 1       # línea actual (base 1)
        self.columna: int       = 1       # columna actual (base 1)
        self.tokens: list[Token] = []
        self.errores: list[str]  = []

    # ------------------------------------------------------------------
    # Helpers de lectura
    # ------------------------------------------------------------------

    def _actual(self) -> str:
        """Retorna el carácter en la posición actual sin consumirlo."""
        if self.pos < len(self.fuente):
            return self.fuente[self.pos]
        return ""

    def _siguiente(self) -> str:
        """Retorna el carácter inmediatamente siguiente sin consumirlo."""
        if self.pos + 1 < len(self.fuente):
            return self.fuente[self.pos + 1]
        return ""

    def _avanzar(self) -> str:
        """
        Consume el carácter actual, actualiza línea/columna y lo retorna.
        Actualiza la línea cuando encuentra un salto de línea.
        """
        c = self.fuente[self.pos]
        self.pos += 1
        if c == "\n":
            self.linea  += 1
            self.columna = 1
        else:
            self.columna += 1
        return c

    # ------------------------------------------------------------------
    # Helpers de emisión
    # ------------------------------------------------------------------

    def _emitir(self, tipo: TipoToken, lexema: str, linea: int, columna: int) -> None:
        """Crea un token y lo agrega a la lista de tokens."""
        self.tokens.append(Token(tipo, lexema, linea, columna))

    def _error(self, mensaje: str, linea: int, columna: int) -> None:
        """
        Registra un error léxico y emite un token ERROR para que el
        parser pueda continuar.  El formato del mensaje incluye posición.
        """
        texto_error = f"[Error léxico] Línea {linea}, columna {columna}: {mensaje}"
        self.errores.append(texto_error)
        self._emitir(TipoToken.ERROR, mensaje, linea, columna)

    # ------------------------------------------------------------------
    # Consumidores especializados
    # ------------------------------------------------------------------

    def _saltar_blancos(self) -> None:
        """Consume espacios, tabulaciones y saltos de línea."""
        while self._actual() and self._actual() in " \t\r\n":
            self._avanzar()

    def _leer_comentario(self) -> None:
        """
        Consume un comentario de línea (// ...) hasta el fin de línea.
        Los comentarios se descartan; no se emite ningún token.
        """
        # Los dos // ya fueron consumidos por el llamador
        while self._actual() and self._actual() != "\n":
            self._avanzar()

    def _leer_numero(self, linea: int, col: int) -> None:
        """
        Lee un literal numérico de la forma [0-9]+([.][0-9]+)?.
        Emite un token NUMERO.
        """
        lexema = ""
        while self._actual().isdigit():
            lexema += self._avanzar()

        # Parte decimal opcional
        if self._actual() == "." and self._siguiente().isdigit():
            lexema += self._avanzar()   # consume el '.'
            while self._actual().isdigit():
                lexema += self._avanzar()

        self._emitir(TipoToken.NUMERO, lexema, linea, col)

    def _leer_identificador_o_kw(self, linea: int, col: int) -> None:
        """
        Lee una secuencia [a-zA-Z_][a-zA-Z0-9_]* y determina si es:
          - PALABRA_CLAVE  (lab, muestra, protocolo, y, o)
          - TIPO           (adn, arn, prot, num, bool)
          - MECANISMO      (transcribir, traducir, mutar, ...)
          - BOOLEANO       (V, F)
          - IDENTIFICADOR  (cualquier otro nombre)
        """
        lexema = ""
        while self._actual().isalnum() or self._actual() == "_":
            lexema += self._avanzar()

        if lexema in PALABRAS_CLAVE or lexema in OP_LOGICOS:
            self._emitir(TipoToken.PALABRA_CLAVE, lexema, linea, col)
        elif lexema in TIPOS:
            self._emitir(TipoToken.TIPO, lexema, linea, col)
        elif lexema in MECANISMOS:
            self._emitir(TipoToken.MECANISMO, lexema, linea, col)
        elif lexema in BOOLEANOS:
            self._emitir(TipoToken.BOOLEANO, lexema, linea, col)
        else:
            self._emitir(TipoToken.IDENTIFICADOR, lexema, linea, col)

    def _leer_cadena_genetica(self, linea: int, col: int) -> None:
        """
        Lee una cadena entre comillas simples ' ... ' y la clasifica como
        CADENA_ADN, CADENA_ARN o CADENA_PROTEINA.

        Estrategia de clasificación:
          1. Si el token previo es TIPO con lexema "adn"  -> valida [AGCT]+
          2. Si el token previo es TIPO con lexema "arn"  -> valida [AUCG]+
          3. Si el token previo es TIPO con lexema "prot" -> valida aminoácidos
          4. Sin contexto: infiere por los caracteres presentes.

        Errores posibles:
          - Cadena vacía
          - Cadena no cerrada (EOF o salto de línea)
          - Caracteres inválidos para el tipo inferido/declarado
        """
        self._avanzar()   # consume la comilla de apertura

        contenido = ""
        while self._actual() and self._actual() not in ("'", "\n"):
            contenido += self._avanzar()

        if not self._actual() or self._actual() == "\n":
            self._error(
                "Cadena genética no cerrada (falta comilla de cierre ')",
                linea, col
            )
            return

        self._avanzar()   # consume la comilla de cierre

        if not contenido:
            self._error("Cadena genética vacía", linea, col)
            return

        # Normalizar a mayúsculas para validación
        contenido_up = contenido.upper()
        chars = frozenset(contenido_up)

        # Determinar tipo correcto por contexto del token anterior
        prev_tipo   = self.tokens[-1].tipo   if self.tokens else None
        prev_lexema = self.tokens[-1].lexema if self.tokens else None

        if prev_tipo == TipoToken.TIPO and prev_lexema == "adn":
            invalidos = chars - ADN_CHARS
            if invalidos:
                self._error(
                    f"Cadena ADN con caracteres inválidos: "
                    f"{sorted(invalidos)} (solo se permiten A, G, C, T)",
                    linea, col
                )
            else:
                self._emitir(TipoToken.CADENA_ADN, contenido_up, linea, col)

        elif prev_tipo == TipoToken.TIPO and prev_lexema == "arn":
            invalidos = chars - ARN_CHARS
            if invalidos:
                self._error(
                    f"Cadena ARN con caracteres inválidos: "
                    f"{sorted(invalidos)} (solo se permiten A, U, C, G)",
                    linea, col
                )
            else:
                self._emitir(TipoToken.CADENA_ARN, contenido_up, linea, col)

        elif prev_tipo == TipoToken.TIPO and prev_lexema == "prot":
            invalidos = chars - PROT_CHARS
            if invalidos:
                self._error(
                    f"Cadena proteína con caracteres inválidos: "
                    f"{sorted(invalidos)} (solo se permiten aminoácidos estándar)",
                    linea, col
                )
            else:
                self._emitir(TipoToken.CADENA_PROTEINA, contenido_up, linea, col)

        else:
            # Sin contexto: inferir por contenido
            # Orden de preferencia: ADN (T exclusivo) > ARN (U exclusivo) > PROTEINA
            if chars <= ADN_CHARS:
                self._emitir(TipoToken.CADENA_ADN, contenido_up, linea, col)
            elif chars <= ARN_CHARS:
                self._emitir(TipoToken.CADENA_ARN, contenido_up, linea, col)
            elif chars <= PROT_CHARS:
                self._emitir(TipoToken.CADENA_PROTEINA, contenido_up, linea, col)
            else:
                invalidos = chars - PROT_CHARS
                self._error(
                    f"Cadena genética con caracteres inválidos: "
                    f"{sorted(invalidos)}",
                    linea, col
                )

    # ------------------------------------------------------------------
    # Ciclo principal de escaneo
    # ------------------------------------------------------------------

    def escanear(self) -> list[Token]:
        """
        Escanea el texto fuente completo y retorna la lista de tokens.

        El proceso es:
          1. Saltar espacios en blanco.
          2. Identificar el siguiente patrón por el carácter actual.
          3. Consumir los caracteres necesarios y emitir el token.
          4. Repetir hasta EOF.

        Después del escaneo, `self.errores` contiene los mensajes de
        todos los errores léxicos encontrados.
        """
        while self.pos < len(self.fuente):
            self._saltar_blancos()
            if self.pos >= len(self.fuente):
                break

            # Guardar posición de inicio del siguiente token
            linea = self.linea
            col   = self.columna
            c     = self._actual()

            # ----------------------------------------------------------
            # Comentario de línea: //
            # ----------------------------------------------------------
            if c == "/" and self._siguiente() == "/":
                self._avanzar()          # consume primer /
                self._avanzar()          # consume segundo /
                self._leer_comentario()

            # ----------------------------------------------------------
            # Bloque abre: /\
            # ----------------------------------------------------------
            elif c == "/" and self._siguiente() == "\\":
                self._avanzar()          # consume /
                self._avanzar()          # consume \
                self._emitir(TipoToken.BLOQUE_ABRE, "/\\", linea, col)

            # ----------------------------------------------------------
            # División ordinaria: /
            # ----------------------------------------------------------
            elif c == "/":
                self._avanzar()
                self._emitir(TipoToken.OPERADOR, "/", linea, col)

            # ----------------------------------------------------------
            # Bloque cierra: \/
            # ----------------------------------------------------------
            elif c == "\\" and self._siguiente() == "/":
                self._avanzar()          # consume \
                self._avanzar()          # consume /
                self._emitir(TipoToken.BLOQUE_CIERRA, "\\/", linea, col)

            # ----------------------------------------------------------
            # Barra invertida sola (inválida)
            # ----------------------------------------------------------
            elif c == "\\":
                self._avanzar()
                self._error(
                    f"Carácter '\\' inesperado. "
                    "¿Quisiste escribir el bloque cierre '\\/'?",
                    linea, col
                )

            # ----------------------------------------------------------
            # Flecha de mecanismo: ->
            # ----------------------------------------------------------
            elif c == "-" and self._siguiente() == ">":
                self._avanzar()          # consume -
                self._avanzar()          # consume >
                self._emitir(TipoToken.OPERADOR, "->", linea, col)

            # ----------------------------------------------------------
            # Operadores de dos caracteres: == != <= >=
            # ----------------------------------------------------------
            elif c == "=" and self._siguiente() == "=":
                self._avanzar(); self._avanzar()
                self._emitir(TipoToken.OPERADOR, "==", linea, col)

            elif c == "!" and self._siguiente() == "=":
                self._avanzar(); self._avanzar()
                self._emitir(TipoToken.OPERADOR, "!=", linea, col)

            elif c == "<" and self._siguiente() == "=":
                self._avanzar(); self._avanzar()
                self._emitir(TipoToken.OPERADOR, "<=", linea, col)

            elif c == ">" and self._siguiente() == "=":
                self._avanzar(); self._avanzar()
                self._emitir(TipoToken.OPERADOR, ">=", linea, col)

            # ----------------------------------------------------------
            # Operadores de un carácter: = < > + - * %
            # (el '!' solo es válido como parte de '!=')
            # ----------------------------------------------------------
            elif c in "=<>+-*%":
                self._avanzar()
                self._emitir(TipoToken.OPERADOR, c, linea, col)

            elif c == "!":
                self._avanzar()
                self._error(
                    "Carácter '!' inesperado. ¿Quisiste escribir '!='?",
                    linea, col
                )

            # ----------------------------------------------------------
            # Puntuación: ( ) : ; ,
            # ----------------------------------------------------------
            elif c in "():;,":
                self._avanzar()
                self._emitir(TipoToken.PUNTUACION, c, linea, col)

            # ----------------------------------------------------------
            # Cadenas genéticas: 'ATGCGT'
            # ----------------------------------------------------------
            elif c == "'":
                self._leer_cadena_genetica(linea, col)

            # ----------------------------------------------------------
            # Literales numéricos: 0-9
            # ----------------------------------------------------------
            elif c.isdigit():
                self._leer_numero(linea, col)

            # ----------------------------------------------------------
            # Identificadores y palabras clave: letra o _
            # ----------------------------------------------------------
            elif c.isalpha() or c == "_":
                self._leer_identificador_o_kw(linea, col)

            # ----------------------------------------------------------
            # Carácter desconocido
            # ----------------------------------------------------------
            else:
                self._avanzar()
                self._error(f"Carácter desconocido: '{c}'", linea, col)

        # Siempre agregar token de fin de archivo
        self._emitir(TipoToken.EOF, "", self.linea, self.columna)
        return self.tokens
