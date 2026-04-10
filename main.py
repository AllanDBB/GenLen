"""
main.py - Punto de entrada del explorador léxico de GenLen.

Uso:
    python main.py <archivo.gl>

Ejemplo:
    python main.py ejemplos/ejemplo1.gl

GenLen - Lenguaje Genético
Curso: Compiladores e Intérpretes
"""

import sys
import os

from src.explorador import Explorador
from src.token import TipoToken


def mostrar_banner() -> None:
    """
    Muestra un banner ASCII art al iniciar el programa.
    """
    banner = r"""
                                _.-;;-._
                        '-..-'|   ||   |
                        '-..-'|_.-;;-._|
                        '-..-'|   ||   |
                        '-..-'|_.-''-._|

                    Explorador Lexico de GenLen
                   Compiladores e Interpretes - TEC
    """
    print(banner)
    print()


def escanear_archivo(ruta: str) -> int:
    """
    Lee un archivo GenLen, lo escanea y muestra los tokens en pantalla.

    Retorna el codigo de salida: 0 si no hay errores, 1 si hay errores lexicos.
    """
    if not os.path.isfile(ruta):
        print(f"Error: el archivo '{ruta}' no existe.", file=sys.stderr)
        return 1

    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()

    explorador = Explorador(fuente)
    tokens = explorador.escanear()

    # Imprimir los tokens en el formato de la especificacion
    print(f"Analizando: {ruta}\n")
    print("┌" + "─" * 78 + "┐")
    print("│ {:^76} │".format("TOKENS"))
    print("├" + "─" * 78 + "┤")
    
    for tok in tokens:
        if tok.tipo == TipoToken.EOF:
            continue
        print(f"│ {str(tok):<76} │")
    
    print("└" + "─" * 78 + "┘")

    # Mostrar resumen de errores lexicos
    if explorador.errores:
        print(f"\n{len(explorador.errores)} error(es) lexico(s) encontrados:\n")
        for err in explorador.errores:
            print(f"   {err}")
        return 1

    print(f"\nEscaneo completado sin errores ({len(tokens) - 1} tokens)")
    return 0


def main() -> None:
    """Punto de entrada principal."""
    mostrar_banner()
    
    if len(sys.argv) < 2:
        print("Uso: python main.py <archivo.gl>")
        print("Ejemplo: python main.py ejemplos/ejemplo1.gl")
        sys.exit(1)

    ruta = sys.argv[1]
    codigo = escanear_archivo(ruta)
    sys.exit(codigo)


if __name__ == "__main__":
    main()