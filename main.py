"""
main.py - Punto de entrada del explorador léxico de GenLen.

Uso:
    python main.py <archivo.gl>

Ejemplo:
    python main.py examples/ejemplo1.gl

Salida:
    Imprime en pantalla cada token en el formato:
    <"TIPO", "lexema", "linea: N, columna: M">

    Al final imprime un resumen de errores léxicos, si los hay.

GenLen - Lenguaje Genético
Curso: Compiladores e Intérpretes
"""

import sys
import os

from src.explorador import Explorador
from src.token import TipoToken


def escanear_archivo(ruta: str) -> int:
    """
    Lee un archivo GenLen, lo escanea y muestra los tokens en pantalla.

    Retorna el código de salida: 0 si no hay errores, 1 si hay errores léxicos.
    """
    if not os.path.isfile(ruta):
        print(f"Error: el archivo '{ruta}' no existe.", file=sys.stderr)
        return 1

    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()

    explorador = Explorador(fuente)
    tokens = explorador.escanear()

    # Imprimir todos los tokens (excepto EOF) en el formato de la especificación
    print(f"=== Tokens de: {ruta} ===\n")
    for tok in tokens:
        if tok.tipo == TipoToken.EOF:
            continue
        print(tok)

    # Mostrar un resumen de errores léxicos
    if explorador.errores:
        print(f"\n=== {len(explorador.errores)} error(es) léxico(s) ===\n")
        for err in explorador.errores:
            print(err, file=sys.stderr)
        return 1

    print(f"\n=== Escaneo completado sin errores ({len(tokens) - 1} tokens) ===")
    return 0


def main() -> None:
    """Punto de entrada principal."""
    if len(sys.argv) < 2:
        print("Uso: python main.py <archivo.gl>", file=sys.stderr)
        print("Ejemplo: python main.py examples/ejemplo1.gl", file=sys.stderr)
        sys.exit(1)

    ruta = sys.argv[1]
    codigo = escanear_archivo(ruta)
    sys.exit(codigo)


if __name__ == "__main__":
    main()
