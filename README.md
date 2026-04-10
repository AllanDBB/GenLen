# GenLen — Lenguaje Genético

GenLen es un lenguaje de propósito específico para bioinformática que permite trabajar con secuencias de ADN, ARN y proteínas como ciudadanos de primera clase del lenguaje.

---

## Estructura del repositorio

```
GenLen/
├── docs/
│   ├── grammatica.pdf        # Especificación de la gramática EBNF del lenguaje
│   └── apuntes_compi.pdf     # Apuntes del curso de Compiladores e Intérpretes
│
├── src/
│   ├── __init__.py
│   ├── token.py              # Clase Token y enumeración TipoToken
│   └── explorador.py         # Explorador léxico (Scanner)
│
├── tests/
│   ├── __init__.py
│   └── test_explorador.py       # Pruebas unitarias del explorador
│
├── ejemplos/
│   ├── ejemplo1.gl           # Declarar y transcribir una secuencia ADN
│   ├── ejemplo2.gl           # Protocolo con edición CRISPR y traducción
│   ├── ejemplo3.gl           # Operadores, booleanos y llamadas encadenadas
│   └── errores.gl            # Archivo con errores léxicos intencionales
│
├── main.py                   # Punto de entrada principal
└── README.md
```

---

## Uso

```bash
python main.py ejemplos/ejemplo1.gl
```

El explorador imprime cada token en el formato:

```
<"TIPO", "lexema", "linea: N, columna: M">
```

### Ejemplo de salida

```
<"PALABRA_CLAVE", "lab", "linea: 1, columna: 1">
<"IDENTIFICADOR", "Ejemplo1", "linea: 1, columna: 5">
<"BLOQUE_ABRE", "/\", "linea: 2, columna: 1">
...
```

---

## Pruebas

```bash
python -m pytest tests/ -v
# o con unittest directamente:
python -m unittest tests/test_explorador.py -v
```

---

## Tokens del lenguaje

| Tipo             | Ejemplos                                       |
|------------------|------------------------------------------------|
| `PALABRA_CLAVE`  | `lab`, `muestra`, `protocolo`, `y`, `o`        |
| `TIPO`           | `adn`, `arn`, `prot`, `num`, `bool`            |
| `MECANISMO`      | `transcribir`, `traducir`, `mutar`, `cas9`, …  |
| `BOOLEANO`       | `V`, `F`                                       |
| `IDENTIFICADOR`  | `gen1`, `secuencia`, `_aux`                    |
| `NUMERO`         | `42`, `3.14`                                   |
| `CADENA_ADN`     | `'ATGCGT'` (solo A/G/C/T)                      |
| `CADENA_ARN`     | `'AUGCAU'` (solo A/U/C/G)                      |
| `CADENA_PROTEINA`| `'MCHHHHH'` (aminoácidos estándar)             |
| `OPERADOR`       | `->`, `=`, `==`, `!=`, `<`, `<=`, `+`, …       |
| `BLOQUE_ABRE`    | `/\`                                           |
| `BLOQUE_CIERRA`  | `\/`                                           |
| `PUNTUACION`     | `(`, `)`, `:`, `;`, `,`                        |

