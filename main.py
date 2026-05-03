"""
main.py - Punto de entrada del compilador GenLen.

Flujo clásico:  Escaneo  →  Análisis Sint.  →  AST  (→  Plegado de constantes)

Uso:
    python main.py <archivo.gl>               # escaneo + análisis + AST
    python main.py --solo-lexico <archivo.gl>  # solo escaneo (modo legado)
    python main.py --fold <archivo.gl>         # escaneo + análisis + plegado

Ejemplos:
    python main.py ejemplos/ejemplo1.gl
    python main.py --fold ejemplos/ejemplo3.gl

GenLen - Lenguaje Genético
Curso: Compiladores e Intérpretes
"""

import sys
import os

from src.explorador  import Explorador
from src.token       import TipoToken
from src.analizador  import Analizador, doblar_constantes


def mostrar_banner() -> None:
    """Muestra el banner ASCII al iniciar el programa."""
    banner = r"""
                                _.-;;-._
                        '-..-'|   ||   |
                        '-..-'|_.-;;-._|
                        '-..-'|   ||   |
                        '-..-'|_.-''-._|

                 Scanner + Parser (LL1) de GenLen
                Compiladores e Interpretes - TEC
    """
    print(banner)
    print()


# ---------------------------------------------------------------------------
# Sección: escaneo
# ---------------------------------------------------------------------------

def _mostrar_tokens(tokens, ruta: str) -> None:
    """Imprime la tabla de tokens."""
    print(f"Analizando: {ruta}\n")
    print("┌" + "─" * 78 + "┐")
    print("│ {:^76} │".format("TOKENS"))
    print("├" + "─" * 78 + "┤")
    for tok in tokens:
        if tok.tipo == TipoToken.EOF:
            continue
        print(f"│ {str(tok):<76} │")
    print("└" + "─" * 78 + "┘")


# ---------------------------------------------------------------------------
# Modos de ejecución
# ---------------------------------------------------------------------------

def modo_solo_lexico(ruta: str) -> int:
    """
    Modo legado: solo escaneo.
    Retorna 0 si no hay errores léxicos, 1 si los hay.
    """
    if not os.path.isfile(ruta):
        print(f"Error: el archivo '{ruta}' no existe.", file=sys.stderr)
        return 1

    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()

    explorador = Explorador(fuente)
    tokens     = explorador.escanear()

    _mostrar_tokens(tokens, ruta)

    if explorador.errores:
        print(f"\n{len(explorador.errores)} error(es) léxico(s) encontrado(s):\n")
        for err in explorador.errores:
            print(f"   {err}")
        return 1

    print(f"\nEscaneo completado sin errores ({len(tokens) - 1} tokens)")
    return 0


def modo_completo(ruta: str, con_folding: bool = False) -> int:
    """
    Modo principal: escaneo → parseo → AST (→ constant folding opcional).

    Retorna:
        0  sin errores
        1  errores léxicos (no se continúa al parser)
        2  errores sintácticos
    """
    if not os.path.isfile(ruta):
        print(f"Error: el archivo '{ruta}' no existe.", file=sys.stderr)
        return 1

    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()

    # ── 1. Escaneo ──────────────────────────────────────────────────────
    explorador = Explorador(fuente)
    tokens     = explorador.escanear()

    _mostrar_tokens(tokens, ruta)

    hay_errores_lexicos = bool(explorador.errores)
    if hay_errores_lexicos:
        print(f"\n{len(explorador.errores)} error(es) léxico(s) encontrado(s):\n")
        for err in explorador.errores:
            print(f"   {err}")
        print("\nNo se puede continuar con el análisis sintáctico.")
        return 1

    print(f"\nEscaneo completado sin errores ({len(tokens) - 1} tokens)\n")

    # ── 2. Análisis sintáctico ───────────────────────────────────────────
    analizador = Analizador(tokens)
    try:
        ast = analizador.analizar()
    except Exception as exc:
        # Error grave no recuperado (no debería ocurrir en condiciones normales)
        print(f"[Error interno del analizador] {exc}", file=sys.stderr)
        return 2

    # ── 3. Constant Folding (opcional) ──────────────────────────────────
    if con_folding:
        ast = doblar_constantes(ast)
        etiqueta_ast = "AST (con constant folding)"
    else:
        etiqueta_ast = "AST"

    # ── 4. Mostrar AST ──────────────────────────────────────────────────
    print("┌" + "─" * 78 + "┐")
    print("│ {:^76} │".format(etiqueta_ast))
    print("└" + "─" * 78 + "┘")
    print(ast.imprimir())

    # ── 5. Errores sintácticos ──────────────────────────────────────────
    if analizador.errores:
        print(f"\n{len(analizador.errores)} error(es) sintáctico(s) encontrado(s):\n")
        for err in analizador.errores:
            print(f"   {err}")
        return 2

    print(f"\nAnálisis completado sin errores.")
    return 0


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def main() -> None:
    """Punto de entrada principal."""
    mostrar_banner()

    args = sys.argv[1:]

    if not args:
        print("Uso:")
        print("  python main.py <archivo.gl>               # escaneo + parseo + AST")
        print("  python main.py --solo-lexico <archivo.gl> # solo escaneo")
        print("  python main.py --fold <archivo.gl>        # AST con constant folding")
        sys.exit(1)

    if args[0] == "--solo-lexico":
        if len(args) < 2:
            print("Error: falta el archivo.", file=sys.stderr)
            sys.exit(1)
        sys.exit(modo_solo_lexico(args[1]))

    if args[0] == "--fold":
        if len(args) < 2:
            print("Error: falta el archivo.", file=sys.stderr)
            sys.exit(1)
        sys.exit(modo_completo(args[1], con_folding=True))

    # Por defecto: escaneo + parseo + AST
    sys.exit(modo_completo(args[0]))


if __name__ == "__main__":
    main()