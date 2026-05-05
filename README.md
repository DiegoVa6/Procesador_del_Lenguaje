# Procesador del Lenguaje Lava

Implementación de un analizador para **Lava**, un pequeño lenguaje imperativo y fuertemente tipado definido para la asignatura de Procesadores del Lenguaje.

El proyecto incluye las tres fases principales de la práctica:

- Analizador léxico con `ply.lex`.
- Analizador sintáctico con `ply.yacc`.
- Análisis semántico con comprobación de tipos, registros, funciones y generación de tablas de salida.

## Lenguaje Lava

Lava soporta:

- Tipos básicos: `int`, `float`, `char` y `boolean`.
- Literales enteros en decimal, binario, octal y hexadecimal.
- Literales reales con punto decimal o notación científica.
- Comentarios de línea (`//`) y multilínea (`/* ... */`).
- Operadores aritméticos, booleanos y comparativos.
- Declaración, instanciación y acceso a campos de `record`.
- Estructuras de control `if`, `else`, `while`, `do while` y `break`.
- Declaración e invocación de funciones, incluyendo sobrecarga.
- Sentencia de salida `print`.

Ejemplo:

```lava
record Vector(float x, float y);
record Planet(Vector position, Vector velocity, float mass, boolean active);

void move(Planet p) {
    p.position.x = p.position.x + p.velocity.x;
    p.position.y = p.position.y + p.velocity.y;
}

Planet earth = new Planet(new Vector(0, 0), new Vector(1, 2), 5, true);

int step = 0;
while (step < 3) {
    if (earth.active) {
        move(earth);
    }
    step = step + 1;
}
```

## Requisitos

- Python 3
- PLY

Instalación de dependencias:

```bash
python3 -m pip install -r requirements.txt
```

## Uso

Para ejecutar el análisis léxico, sintáctico y semántico sobre un fichero `.lava`:

```bash
python3 main.py fichero.lava
```

Si el programa es correcto, no se muestra salida por consola y se generan ficheros auxiliares junto al fichero de entrada.

Para ejecutar solo el analizador léxico y generar el fichero de tokens:

```bash
python3 main.py --token fichero.lava
```

## Ficheros Generados

Según el modo de ejecución y el contenido del programa, se pueden generar:

- `.token`: secuencia de tokens reconocidos por el lexer.
- `.symbols`: tabla de símbolos con variables declaradas.
- `.records`: tabla de registros definidos.
- `.functions`: tabla de funciones declaradas.

Los ficheros semánticos se generan con el mismo nombre base que el fichero `.lava` analizado.

## Tests

El repositorio incluye pruebas para las diferentes fases del procesador.

Tests del parser:

```bash
python3 run_parser_tests.py
```

Tests extendidos del parser:

```bash
python3 run_parser_extended_tests.py
```

Tests semánticos:

```bash
python3 test_semantico.py
```

Tests semánticos con salida detallada:

```bash
python3 test_semantico.py -v
```

Tests del lexer:

```bash
python3 tests_lexer/run_tests.py
```

## Estructura del Proyecto

```text
.
├── lexer.py                 # Analizador léxico
├── parser.py                # Analizador sintáctico y semántico
├── main.py                  # Punto de entrada
├── run_parser_tests.py      # Batería de tests del parser
├── run_parser_extended_tests.py # Tests adicionales del parser
├── test_semantico.py        # Batería de tests semánticos
├── tests_lexer/             # Casos de prueba del lexer
├── tests_parser/            # Casos válidos e inválidos del parser
└── test_semantico/          # Programas Lava para pruebas semánticas
```

## Notas

Este proyecto está orientado al análisis de programas Lava, no a su ejecución completa. La salida principal del analizador semántico son las tablas auxiliares generadas a partir del programa de entrada.
