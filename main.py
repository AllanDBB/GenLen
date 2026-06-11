"""
main.py - Punto de entrada del compilador GenLen.

Flujo completo:  Escaneo  →  Análisis Sint.  →  AST  →  Verificación  →  Generación

Uso:
    python main.py <archivo.gl>                       # escaneo + análisis + AST
    python main.py --solo-lexico <archivo.gl>          # solo escaneo
    python main.py --fold <archivo.gl>                 # AST con constant folding
    python main.py --verificar <archivo.gl>            # análisis + checker + AST decorado
    python main.py --generar <archivo.gl>              # pipeline completo → <nombre>.py
    python main.py --generar <archivo.gl> -o <out.py>  # con nombre de salida explícito

Ejemplos:
    python main.py ejemplos/ejemplo1.gl
    python main.py --verificar ejemplos/ejemplo12.gl
    python main.py --generar ejemplos/carrera_caracoles.gl

GenLen - Lenguaje Genético
Curso: Compiladores e Intérpretes
"""

import sys
import os

from src.explorador  import Explorador
from src.token       import TipoToken
from src.analizador  import Analizador, doblar_constantes
from src.verificador import Verificador
from src.generador   import Generador


def mostrar_banner() -> None:
    banner = r"""
                            _.-;;-._
                    '-..-'|   ||   |
                    '-..-'|_.-;;-._|
                    '-..-'|   ||   |
                    '-..-'|_.-''-._|

         Scanner + Parser (LL1) + Checker + Generador  —  GenLen
                Compiladores e Interpretes - TEC
    """
    print(banner)
    print()


# ---------------------------------------------------------------------------
# Sección: escaneo
# ---------------------------------------------------------------------------

def _mostrar_tokens(tokens, ruta: str) -> None:
    print(f"Analizando: {ruta}\n")
    print("┌" + "─" * 78 + "┐")
    print("│ {:^76} │".format("TOKENS"))
    print("├" + "─" * 78 + "┤")
    for tok in tokens:
        if tok.tipo == TipoToken.EOF:
            continue
        print(f"│ {str(tok):<76} │")
    print("└" + "─" * 78 + "┘")


def _escanear_y_parsear(ruta: str):
    """
    Retorna (ast, analizador) o termina el proceso si hay errores léxicos.
    """
    if not os.path.isfile(ruta):
        print(f"Error: el archivo '{ruta}' no existe.", file=sys.stderr)
        sys.exit(1)

    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()

    explorador = Explorador(fuente)
    tokens     = explorador.escanear()

    _mostrar_tokens(tokens, ruta)

    if explorador.errores:
        print(f"\n{len(explorador.errores)} error(es) léxico(s):\n")
        for err in explorador.errores:
            print(f"   {err}")
        print("\nNo se puede continuar con el análisis sintáctico.")
        sys.exit(1)

    print(f"\nEscaneo completado sin errores ({len(tokens) - 1} tokens)\n")

    analizador = Analizador(tokens)
    try:
        ast = analizador.analizar()
    except Exception as exc:
        print(f"[Error interno del analizador] {exc}", file=sys.stderr)
        sys.exit(2)

    return ast, analizador


# ---------------------------------------------------------------------------
# Modos de ejecución
# ---------------------------------------------------------------------------

def modo_solo_lexico(ruta: str) -> int:
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
    """Escaneo + parseo + AST (+ constant folding opcional)."""
    ast, analizador = _escanear_y_parsear(ruta)

    if con_folding:
        ast      = doblar_constantes(ast)
        etiqueta = "AST (con constant folding)"
    else:
        etiqueta = "AST"

    print("┌" + "─" * 78 + "┐")
    print("│ {:^76} │".format(etiqueta))
    print("└" + "─" * 78 + "┘")
    print(ast.imprimir())

    if analizador.errores:
        print(f"\n{len(analizador.errores)} error(es) sintáctico(s):\n")
        for err in analizador.errores:
            print(f"   {err}")
        return 2

    print("\nAnálisis completado sin errores.")
    return 0


def modo_verificar(ruta: str) -> int:
    """
    Escaneo + parseo + verificación semántica.
    Imprime la tabla de símbolos (parcialmente durante el recorrido)
    y el AST decorado al final.
    """
    ast, analizador = _escanear_y_parsear(ruta)

    if analizador.errores:
        print(f"\n{len(analizador.errores)} error(es) sintáctico(s):\n")
        for err in analizador.errores:
            print(f"   {err}")
        print("\nNo se puede continuar con la verificación semántica.")
        return 2

    print("Análisis sintáctico completado sin errores.\n")

    # ── Verificación semántica ──────────────────────────────────────────
    verificador = Verificador()
    verificador.verificar(ast)

    # ── AST decorado ────────────────────────────────────────────────────
    print("\n" + "┌" + "─" * 78 + "┐")
    print("│ {:^76} │".format("AST DECORADO (pre-orden)"))
    print("└" + "─" * 78 + "┘")
    print(ast.imprimir(decorado=True))

    # ── Tabla de símbolos final ─────────────────────────────────────────
    print("\n" + "┌" + "─" * 78 + "┐")
    print("│ {:^76} │".format("TABLA DE SÍMBOLOS FINAL"))
    print("└" + "─" * 78 + "┘")
    print(verificador.tabla.imprimir())

    if verificador.errores:
        print(f"\n{len(verificador.errores)} error(es) semántico(s):\n")
        for err in verificador.errores:
            print(f"   {err}")
        return 3

    print("\nVerificación semántica completada sin errores.")
    return 0


def modo_generar(ruta: str, salida: str = "") -> int:
    """
    Pipeline completo: escaneo + parseo + verificación + generación de Python.
    Escribe el código Python en <salida> (por defecto <nombre_sin_ext>.py).
    """
    ast, analizador = _escanear_y_parsear(ruta)

    if analizador.errores:
        print(f"\n{len(analizador.errores)} error(es) sintáctico(s):\n")
        for err in analizador.errores:
            print(f"   {err}")
        return 2

    # Verificación semántica (los errores se reportan pero no detienen la generación)
    verificador = Verificador()
    verificador.verificar(ast)

    if verificador.errores:
        print(f"\nAdvertencia: {len(verificador.errores)} error(es) semántico(s):\n")
        for err in verificador.errores:
            print(f"   {err}")
        print()

    # Nombre del archivo de salida
    if not salida:
        base   = os.path.splitext(os.path.basename(ruta))[0]
        salida = base + ".py"

    generador = Generador()
    codigo    = generador.generar(ast)

    with open(salida, "w", encoding="utf-8") as f:
        f.write(codigo)

    print(f"\nCódigo Python generado en: {salida}")
    print(f"Ejecuta con: python {salida}")
    return 0


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def main() -> None:
    mostrar_banner()

    args = sys.argv[1:]

    if not args:
        print("Uso:")
        print("  python main.py <archivo.gl>                       # escaneo + parseo + AST")
        print("  python main.py --solo-lexico <archivo.gl>          # solo escaneo")
        print("  python main.py --fold <archivo.gl>                 # AST con constant folding")
        print("  python main.py --verificar <archivo.gl>            # checker + AST decorado")
        print("  python main.py --generar <archivo.gl>              # genera <nombre>.py")
        print("  python main.py --generar <archivo.gl> -o <out.py>  # con nombre explícito")
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

    if args[0] == "--verificar":
        if len(args) < 2:
            print("Error: falta el archivo.", file=sys.stderr)
            sys.exit(1)
        sys.exit(modo_verificar(args[1]))

    if args[0] == "--generar":
        if len(args) < 2:
            print("Error: falta el archivo.", file=sys.stderr)
            sys.exit(1)
        salida = ""
        if len(args) >= 4 and args[2] == "-o":
            salida = args[3]
        sys.exit(modo_generar(args[1], salida))

    # Por defecto: escaneo + parseo + AST
    sys.exit(modo_completo(args[0]))


if __name__ == "__main__":
    main()
