"""
token.py - Definición de los tipos de tokens y la clase Token para GenLen.

GenLen - Lenguaje Genético
Curso: Compiladores e Intérpretes
"""

from enum import Enum


class TipoToken(Enum):
    """
    Tipos de componentes léxicos (tokens) del lenguaje GenLen.

    Categorías:
      - PALABRA_CLAVE    : lab, muestra, protocolo, y, o
      - TIPO             : adn, arn, prot, num, bool
      - MECANISMO        : transcribir, traducir, mutar, cas9, alinear, modelar, docking
      - BOOLEANO         : V (verdadero), F (falso)
      - IDENTIFICADOR    : nombres definidos por el usuario
      - NUMERO           : literales numéricos (enteros y decimales)
      - CADENA_ADN       : secuencia de nucleótidos ADN  'ACGT...'
      - CADENA_ARN       : secuencia de nucleótidos ARN  'AUCG...'
      - CADENA_PROTEINA  : secuencia de aminoácidos      'MCHHH...'
      - OPERADOR         : ->, =, ==, !=, <, <=, >, >=, +, -, *, /, %
      - BLOQUE_ABRE      : /\\
      - BLOQUE_CIERRA    : \\/
      - PUNTUACION       : ( ) : ; ,
      - EOF              : fin de archivo
      - ERROR            : carácter o secuencia inválida
    """

    PALABRA_CLAVE    = "PALABRA_CLAVE"
    TIPO             = "TIPO"
    MECANISMO        = "MECANISMO"
    BOOLEANO         = "BOOLEANO"
    IDENTIFICADOR    = "IDENTIFICADOR"
    NUMERO           = "NUMERO"
    CADENA_ADN       = "CADENA_ADN"
    CADENA_ARN       = "CADENA_ARN"
    CADENA_PROTEINA  = "CADENA_PROTEINA"
    OPERADOR         = "OPERADOR"
    BLOQUE_ABRE      = "BLOQUE_ABRE"
    BLOQUE_CIERRA    = "BLOQUE_CIERRA"
    PUNTUACION       = "PUNTUACION"
    EOF              = "EOF"
    ERROR            = "ERROR"


class Token:
    """
    Representa un componente léxico (token) del lenguaje GenLen.

    Atributos:
        tipo    : TipoToken  - categoría del componente léxico
        lexema  : str        - texto exacto tal como aparece en la fuente
        linea   : int        - número de línea donde inicia (base 1)
        columna : int        - número de columna donde inicia (base 1)
    """

    def __init__(self, tipo: TipoToken, lexema: str, linea: int, columna: int):
        self.tipo    = tipo
        self.lexema  = lexema
        self.linea   = linea
        self.columna = columna

    def __str__(self) -> str:
        """Formato de salida según la especificación del proyecto."""
        atributos = f"linea: {self.linea}, columna: {self.columna}"
        return f'<"{self.tipo.value}", "{self.lexema}", "{atributos}">'

    def __repr__(self) -> str:
        return self.__str__()
