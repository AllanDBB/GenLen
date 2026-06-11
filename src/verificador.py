"""
verificador.py - Verificador semántico (checker) para GenLen.

Recorre el AST en estrategia Descendente (Top-Down) usando el patrón Visitante.
Realiza:
  - Verificación de identificadores (variables/protocolos declarados antes de uso)
  - Inferencia de tipos para expresiones y mecanismos
  - Decorado del AST: tipo_dato y referencia a definición en cada nodo
  - Impresión parcial de la tabla de símbolos cada vez que cambia

GenLen - Lenguaje Genético
Curso: Compiladores e Intérpretes
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .nodo import Nodo, TipoNodo


# ---------------------------------------------------------------------------
# Entrada de la tabla de símbolos
# ---------------------------------------------------------------------------

@dataclass
class EntradaSimbolo:
    nombre: str
    tipo: str        # 'adn' | 'arn' | 'prot' | 'num' | 'bool' | 'protocolo'
    nodo_def: Nodo
    nivel: int       # profundidad del alcance donde se definió


# ---------------------------------------------------------------------------
# Tabla de símbolos con alcances anidados
# ---------------------------------------------------------------------------

class TablaSimbolo:
    """Tabla de símbolos con pila de alcances."""

    def __init__(self) -> None:
        self._alcances: list[dict[str, EntradaSimbolo]] = [{}]

    @property
    def nivel(self) -> int:
        return len(self._alcances) - 1

    def entrar_alcance(self) -> None:
        self._alcances.append({})

    def salir_alcance(self) -> None:
        if len(self._alcances) > 1:
            self._alcances.pop()

    def definir(self, nombre: str, tipo: str, nodo_def: Nodo) -> None:
        self._alcances[-1][nombre] = EntradaSimbolo(nombre, tipo, nodo_def, self.nivel)

    def buscar(self, nombre: str) -> Optional[EntradaSimbolo]:
        for alcance in reversed(self._alcances):
            if nombre in alcance:
                return alcance[nombre]
        return None

    def esta_en_alcance_actual(self, nombre: str) -> bool:
        return nombre in self._alcances[-1]

    def imprimir(self) -> str:
        """Retorna la tabla formateada como texto."""
        col_nom  = 18
        col_tipo =  9
        col_niv  =  5
        col_pos  = 10

        def _fila(izq, med, der):
            return (
                izq + "─" * (col_nom + 2)
                + med + "─" * (col_tipo + 2)
                + med + "─" * (col_niv + 2)
                + med + "─" * (col_pos + 2) + der
            )

        sep_top = _fila("┌", "┬", "┐")
        sep_mid = _fila("├", "┼", "┤")
        sep_bot = _fila("└", "┴", "┘")

        titulo_ancho = col_nom + col_tipo + col_niv + col_pos + 9
        lineas = [
            "┌" + "─" * titulo_ancho + "┐",
            "│ {:^{}} │".format("TABLA DE SÍMBOLOS", titulo_ancho - 2),
            sep_top,
            "│ {:<{}} │ {:<{}} │ {:^{}} │ {:>{}} │".format(
                "Nombre", col_nom,
                "Tipo",   col_tipo,
                "Nivel",  col_niv,
                "Línea",  col_pos,
            ),
            sep_mid,
        ]

        hay_entradas = False
        for alcance in self._alcances:
            for nombre, ent in alcance.items():
                hay_entradas = True
                pos = f"{ent.nodo_def.linea}:{ent.nodo_def.columna}"
                lineas.append(
                    "│ {:<{}} │ {:<{}} │ {:^{}} │ {:>{}} │".format(
                        nombre[:col_nom], col_nom,
                        ent.tipo[:col_tipo], col_tipo,
                        ent.nivel, col_niv,
                        pos[:col_pos], col_pos,
                    )
                )

        if not hay_entradas:
            lineas.append(
                "│ {:^{}} │".format("(vacía)", titulo_ancho - 2)
            )

        lineas.append(sep_bot)
        return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Verificador semántico — patrón Visitante, estrategia Top-Down
# ---------------------------------------------------------------------------

class Verificador:
    """
    Verificador semántico para GenLen.

    Uso:
        ver = Verificador()
        ver.verificar(ast)
        # ver.errores  — lista de mensajes de error semántico
    """

    # Tipos de entrada/salida para mecanismos.
    # None significa "el mismo tipo que el receptor".
    _MECANISMO: dict[str, tuple[Optional[str], Optional[str]]] = {
        "transcribir": ("adn",  "arn"),
        "traducir":    ("arn",  "prot"),
        "mutar":       (None,   None),   # mismo tipo
        "cas9":        ("adn",  "adn"),
        "alinear":     (None,   None),   # mismo tipo
        "modelar":     ("prot", "prot"),
        "docking":     ("prot", "prot"),
        "mostrar":     (None,   None),   # mismo tipo, imprime
    }

    def __init__(self) -> None:
        self.tabla   = TablaSimbolo()
        self.errores: list[str] = []

    # -----------------------------------------------------------------------
    # Interfaz pública
    # -----------------------------------------------------------------------

    def verificar(self, ast: Nodo) -> None:
        print("\n" + "─" * 60)
        print("  Iniciando verificación semántica")
        print("─" * 60)
        self._visitar(ast)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _error(self, msg: str, linea: int, columna: int) -> None:
        texto = f"[Error semántico] Línea {linea}, col {columna}: {msg}"
        self.errores.append(texto)

    def _mostrar_tabla(self, etiqueta: str = "") -> None:
        if etiqueta:
            print(f"\n  [{etiqueta}]")
        print(self.tabla.imprimir())

    def _visitar(self, nodo: Nodo) -> Optional[str]:
        """Despacha al visitante correspondiente según el tipo del nodo."""
        nombre_metodo = "_visitar_" + nodo.tipo.value.lower()
        metodo = getattr(self, nombre_metodo, self._visitar_generico)
        tipo = metodo(nodo)
        if tipo is not None:
            nodo.tipo_dato = tipo
        return tipo

    def _visitar_generico(self, nodo: Nodo) -> None:
        for hijo in nodo.hijos:
            self._visitar(hijo)

    # -----------------------------------------------------------------------
    # Estructura del programa
    # -----------------------------------------------------------------------

    def _visitar_programa(self, nodo: Nodo) -> None:
        self._mostrar_tabla("Alcance global (inicio)")
        for hijo in nodo.hijos:
            self._visitar(hijo)

    def _visitar_cuerpo(self, nodo: Nodo) -> None:
        for hijo in nodo.hijos:
            self._visitar(hijo)

    # -----------------------------------------------------------------------
    # Declaración
    # -----------------------------------------------------------------------

    def _visitar_declaracion(self, nodo: Nodo) -> None:
        nombre = nodo.contenido
        tipo   = nodo.hijos[0].contenido   # nodo TIPO

        if self.tabla.esta_en_alcance_actual(nombre):
            self._error(
                f"Variable '{nombre}' ya declarada en este alcance",
                nodo.linea, nodo.columna,
            )
        else:
            self.tabla.definir(nombre, tipo, nodo)
            nodo.tipo_dato = tipo
            self._mostrar_tabla(f"+ '{nombre}' : {tipo}")

        # Inicialización opcional
        if len(nodo.hijos) > 1:
            expr_tipo = self._visitar(nodo.hijos[1])
            if expr_tipo and expr_tipo != tipo:
                self._error(
                    f"Asignación incompatible: '{nombre}' es '{tipo}' "
                    f"pero la expresión es '{expr_tipo}'",
                    nodo.linea, nodo.columna,
                )

    # -----------------------------------------------------------------------
    # Protocolo
    # -----------------------------------------------------------------------

    def _visitar_protocolo(self, nodo: Nodo) -> None:
        nombre = nodo.contenido

        if self.tabla.esta_en_alcance_actual(nombre):
            self._error(
                f"Protocolo '{nombre}' ya declarado en este alcance",
                nodo.linea, nodo.columna,
            )
        else:
            self.tabla.definir(nombre, "protocolo", nodo)
            self._mostrar_tabla(f"+ protocolo '{nombre}'")

        # Nuevo alcance para el cuerpo del protocolo
        self.tabla.entrar_alcance()

        lista_params = nodo.hijos[0]   # LISTA_PARAMS
        for param in lista_params.hijos:
            pnom  = param.contenido
            ptipo = param.hijos[0].contenido
            self.tabla.definir(pnom, ptipo, param)
            param.tipo_dato = ptipo

        if lista_params.hijos:
            self._mostrar_tabla(f"Parámetros de '{nombre}'")

        self._visitar(nodo.hijos[1])   # CUERPO

        self.tabla.salir_alcance()
        self._mostrar_tabla(f"Salida de alcance '{nombre}'")

    # -----------------------------------------------------------------------
    # Asignación
    # -----------------------------------------------------------------------

    def _visitar_asignacion(self, nodo: Nodo) -> None:
        nombre  = nodo.contenido
        entrada = self.tabla.buscar(nombre)

        if entrada is None:
            self._error(
                f"Variable '{nombre}' no declarada",
                nodo.linea, nodo.columna,
            )
        else:
            nodo.definicion = entrada.nodo_def
            nodo.tipo_dato  = entrada.tipo

        expr_tipo = self._visitar(nodo.hijos[0])

        if entrada and expr_tipo and expr_tipo != entrada.tipo:
            self._error(
                f"Tipo incompatible: '{nombre}' es '{entrada.tipo}' "
                f"pero se asigna '{expr_tipo}'",
                nodo.linea, nodo.columna,
            )

    # -----------------------------------------------------------------------
    # Llamada a protocolo
    # -----------------------------------------------------------------------

    def _visitar_llamada_protocolo(self, nodo: Nodo) -> Optional[str]:
        nombre  = nodo.contenido
        entrada = self.tabla.buscar(nombre)

        if entrada is None:
            self._error(
                f"Protocolo '{nombre}' no declarado",
                nodo.linea, nodo.columna,
            )
        elif entrada.tipo != "protocolo":
            self._error(
                f"'{nombre}' no es un protocolo (es '{entrada.tipo}')",
                nodo.linea, nodo.columna,
            )
        else:
            nodo.definicion = entrada.nodo_def

        for hijo in nodo.hijos:
            self._visitar(hijo)

        return None   # los protocolos son void

    # -----------------------------------------------------------------------
    # Llamada a mecanismo
    # -----------------------------------------------------------------------

    def _visitar_llamada_mecanismo(self, nodo: Nodo) -> Optional[str]:
        mecanismo    = nodo.contenido
        receptor_tipo = self._visitar(nodo.hijos[0])

        arg_tipos: list[Optional[str]] = []
        if len(nodo.hijos) > 1:
            for arg in nodo.hijos[1].hijos:
                arg_tipos.append(self._visitar(arg))

        resultado = self._inferir_mecanismo(
            mecanismo, receptor_tipo, arg_tipos, nodo
        )
        nodo.tipo_dato = resultado
        return resultado

    def _inferir_mecanismo(
        self,
        mec: str,
        rec: Optional[str],
        args: list[Optional[str]],
        nodo: Nodo,
    ) -> Optional[str]:
        if mec not in self._MECANISMO:
            self._error(
                f"Mecanismo '{mec}' desconocido",
                nodo.linea, nodo.columna,
            )
            return None

        tipo_esperado_rec, tipo_resultado = self._MECANISMO[mec]

        if tipo_esperado_rec is not None and rec and rec != tipo_esperado_rec:
            self._error(
                f"'{mec}()' requiere receptor '{tipo_esperado_rec}', "
                f"se recibió '{rec}'",
                nodo.linea, nodo.columna,
            )

        # Verificaciones adicionales por mecanismo
        if mec == "cas9" and args and args[0] and args[0] not in ("adn", "arn"):
            self._error(
                f"cas9() requiere argumento 'adn' o 'arn', "
                f"se recibió '{args[0]}'",
                nodo.linea, nodo.columna,
            )

        if mec == "docking" and args and args[0] and args[0] != "prot":
            self._error(
                f"docking() requiere argumento 'prot', "
                f"se recibió '{args[0]}'",
                nodo.linea, nodo.columna,
            )

        if mec == "alinear" and rec and args and args[0] and rec != args[0]:
            self._error(
                f"alinear() requiere que receptor y argumento sean del mismo tipo "
                f"('{rec}' vs '{args[0]}')",
                nodo.linea, nodo.columna,
            )

        # Si tipo_resultado es None, el resultado es el mismo tipo que el receptor
        return tipo_resultado if tipo_resultado is not None else rec

    # -----------------------------------------------------------------------
    # Expresiones binaria / unaria
    # -----------------------------------------------------------------------

    _OPS_ARIT  = frozenset({"+", "-", "*", "/", "%"})
    _OPS_COMP  = frozenset({"==", "!=", "<", "<=", ">", ">="})
    _OPS_LOGICOS = frozenset({"y", "o"})

    def _visitar_binaria(self, nodo: Nodo) -> Optional[str]:
        op        = nodo.contenido
        tipo_izq  = self._visitar(nodo.hijos[0])
        tipo_der  = self._visitar(nodo.hijos[1])

        if op in self._OPS_ARIT:
            for lado, t in (("izquierdo", tipo_izq), ("derecho", tipo_der)):
                if t and t != "num":
                    self._error(
                        f"Operador '{op}': operando {lado} debe ser 'num', "
                        f"se recibió '{t}'",
                        nodo.linea, nodo.columna,
                    )
            return "num"

        if op in self._OPS_COMP:
            if tipo_izq and tipo_der and tipo_izq != tipo_der:
                self._error(
                    f"Operador '{op}': operandos de tipos distintos "
                    f"('{tipo_izq}' y '{tipo_der}')",
                    nodo.linea, nodo.columna,
                )
            return "bool"

        if op in self._OPS_LOGICOS:
            for lado, t in (("izquierdo", tipo_izq), ("derecho", tipo_der)):
                if t and t != "bool":
                    self._error(
                        f"Operador '{op}': operando {lado} debe ser 'bool', "
                        f"se recibió '{t}'",
                        nodo.linea, nodo.columna,
                    )
            return "bool"

        return None

    def _visitar_unaria(self, nodo: Nodo) -> Optional[str]:
        tipo_op = self._visitar(nodo.hijos[0])
        if tipo_op and tipo_op != "num":
            self._error(
                f"Operador unario '-' requiere 'num', se recibió '{tipo_op}'",
                nodo.linea, nodo.columna,
            )
        return "num"

    # -----------------------------------------------------------------------
    # Listas
    # -----------------------------------------------------------------------

    def _visitar_lista_args(self, nodo: Nodo) -> None:
        for hijo in nodo.hijos:
            self._visitar(hijo)

    def _visitar_lista_params(self, nodo: Nodo) -> None:
        for hijo in nodo.hijos:
            self._visitar(hijo)

    # -----------------------------------------------------------------------
    # Literales y primarios
    # -----------------------------------------------------------------------

    def _visitar_identificador(self, nodo: Nodo) -> Optional[str]:
        entrada = self.tabla.buscar(nodo.contenido)
        if entrada is None:
            self._error(
                f"Identificador '{nodo.contenido}' no declarado",
                nodo.linea, nodo.columna,
            )
            return None
        nodo.definicion = entrada.nodo_def
        return entrada.tipo

    def _visitar_numero(self, nodo: Nodo) -> str:
        return "num"

    def _visitar_booleano(self, nodo: Nodo) -> str:
        return "bool"

    def _visitar_cadena_adn(self, nodo: Nodo) -> str:
        return "adn"

    def _visitar_cadena_arn(self, nodo: Nodo) -> str:
        return "arn"

    def _visitar_cadena_proteina(self, nodo: Nodo) -> str:
        return "prot"

    def _visitar_tipo(self, nodo: Nodo) -> str:
        return nodo.contenido

    def _visitar_param(self, nodo: Nodo) -> Optional[str]:
        return nodo.hijos[0].contenido if nodo.hijos else None
