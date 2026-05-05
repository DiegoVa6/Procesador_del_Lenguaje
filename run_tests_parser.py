"""
run_tests.py — Batería de tests para el parser de Lava (P2)
Uso: python run_tests.py
Coloca este archivo en la misma carpeta que main.py y parser.py.
"""

import subprocess
import sys
import os
import tempfile

GREEN = "\033[92m"
RED   = "\033[91m"
GRAY  = "\033[90m"
CYAN  = "\033[96m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
RESET = "\033[0m"

# ═══════════════════════════════════════════════════════════════════════════
# CASOS VÁLIDOS — el parser debe aceptarlos (exit code 0, sin [ERROR])
# ═══════════════════════════════════════════════════════════════════════════
VALID = [

    # ── Casos límite de estructura ────────────────────────────────────────
    ("fichero vacío",
     ""),

    ("solo saltos de línea",
     "\n\n\n"),

    ("solo un semicolon",
     ";"),

    ("múltiples semicolons seguidos",
     ";; ; ;;;"),

    ("semicolons entre sentencias",
     "int a = 1;;\nint b = 2;;;"),

    # ── Tipos básicos: declaración sin asignación ─────────────────────────
    ("declaración int sin asignación",
     "int a;"),

    ("declaración float sin asignación",
     "float b;"),

    ("declaración char sin asignación",
     "char c;"),

    ("declaración boolean sin asignación",
     "boolean d;"),

    # ── Tipos básicos: declaración con asignación ─────────────────────────
    ("int decimal",
     "int a = 495;"),

    ("int binario",
     "int a = 0b111101111;"),

    ("int octal",
     "int a = 0757;"),

    ("int hexadecimal",
     "int a = 0x1EF;"),

    ("int cero",
     "int a = 0;"),

    ("float punto decimal",
     "float f = 100.001;"),

    ("float notación científica positiva",
     "float f = 9.87e-2;"),

    ("float notación científica entera",
     "float f = 5e5;"),

    ("char letra",
     "char c = 'a';"),

    ("char símbolo",
     "char c = ';';"),

    ("boolean true",
     "boolean b = true;"),

    ("boolean false",
     "boolean b = false;"),

    # ── Multi-declaración (solo sin asignación) ───────────────────────────
    ("multi-declaración 2 variables",
     "int a, b;"),

    ("multi-declaración 3 variables",
     "int a, b, c;"),

    ("multi-declaración y asignación posterior separadas",
     "int a, b;\na = 10;\nb = a * a - a;"),

    # ── Asignaciones ─────────────────────────────────────────────────────
    ("asignación simple",
     "int a;\na = 5;"),

    ("asignación con expresión compleja",
     "int a;\na = 10 + 5 * 2 - 3;"),

    # ── Operaciones aritméticas ───────────────────────────────────────────
    ("suma",
     "int a = 10 + 5;"),

    ("resta",
     "int a = 10 - 5;"),

    ("multiplicación",
     "int a = 10 * 5;"),

    ("división",
     "float a = 10.0 / 3.0;"),

    ("unario negativo",
     "float f = -3.14;"),

    ("unario positivo",
     "float f = +1.0;"),

    ("expresión compleja con precedencia",
     "int x = 10 + 5 * 2 - 3 / 1;"),

    ("paréntesis cambian precedencia",
     "int x = (2 + 3) * 4;"),

    ("doble unario",
     "int x = --5;"),

    # ── Operaciones booleanas ─────────────────────────────────────────────
    ("and",
     "boolean b = true && false;"),

    ("or",
     "boolean b = true || false;"),

    ("not",
     "boolean b = !true;"),

    ("not encadenado",
     "boolean b = !!true;"),

    ("expresión booleana mixta",
     "boolean b = true && false || !true;"),

    # ── Operaciones comparativas ──────────────────────────────────────────
    ("igual",
     "boolean b = 5 == 5;"),

    ("mayor que",
     "boolean b = 10 > 5;"),

    ("mayor o igual",
     "boolean b = 10 >= 10;"),

    ("menor que",
     "boolean b = 3 < 4;"),

    ("menor o igual",
     "boolean b = 3 <= 4;"),

    ("comparativa con float",
     "boolean b = 10.3 > 200e-1;"),

    # ── Expresión compleja del enunciado ──────────────────────────────────
    ("expresión del if del enunciado",
     "boolean b1 = true;\nboolean b2 = false;\nfloat f2 = 3.0;\nint i1 = 1;\n"
     "boolean r = f2 == 3 || b1 && b2 || 10 - 4 * i1 >= 0xFF - 1e-1;"),

    # ── Expresión como sentencia standalone ───────────────────────────────
    ("expresión standalone aritmética",
     "int a = 1;\nint b = 2;\na + b;"),

    ("expresión standalone booleana",
     "boolean b = true;\n!b;"),

    # ── Records ───────────────────────────────────────────────────────────
    ("record simple",
     "record Point(int x, int y);"),

    ("record con tipos básicos mixtos",
     "record Circle(float cx, float cy, float radius, char color);"),

    ("record con tipo record como campo",
     "record Point(int x, int y);\nrecord Line(Point a, Point b);"),

    ("instanciación de record",
     "record Point(int x, int y);\nPoint p = new Point(1, 2);"),

    ("acceso a campo de record",
     "record Point(int x, int y);\nPoint p = new Point(1, 2);\nint v = p.x;"),

    ("acceso a campo anidado",
     "record V(float x, float y);\nrecord P(V pos, float mass);\n"
     "P p = new P(new V(1.0, 2.0), 5.0);\nfloat vx = p.pos.x;"),

    ("record como campo de otro record (enunciado)",
     "record Vector(float x, float y);\n"
     "record Planet(Vector position, Vector velocity, float mass, boolean active);\n"
     "Planet earth = new Planet(new Vector(0, 0), new Vector(1, 2), 5, true);"),

    ("asignación a campo de record",
     "record Point(int x, int y);\nPoint p = new Point(0, 0);\np.x = 10;"),

    ("asignación a campo anidado",
     "record V(float x);\nrecord P(V pos);\n"
     "P p = new P(new V(0.0));\np.pos.x = 1.5;"),

    ("instanciación anidada compleja (enunciado)",
     "record Location(char city, char country);\n"
     "record Price(float euro, float dollar, float yen);\n"
     "record House(Location location, Price price);\n"
     "House myHouse = new House(\n"
     "  new Location('M', 'E'),\n"
     "  new Price(100e100, 108e100, 16397e100));"),

    # ── Control de flujo: if ──────────────────────────────────────────────
    ("if simple",
     "int a = 1;\nif (a > 0) {\n  a = 0;\n}"),

    ("if-else",
     "int a = 1;\nif (a > 0) {\n  a = 0;\n} else {\n  a = 1;\n}"),

    ("if con condición compleja",
     "float f2 = 3.0;\nboolean b1 = true;\nboolean b2 = false;\nint i1 = 1;\n"
     "if (f2 == 3 || b1 && b2 || 10 - 4 * i1 >= 0xFF - 1e-1) {\n"
     "  f2 = f2 - 3;\n} else {\n  f2 = 10 - f2 * f2;\n}"),

    ("if anidado",
     "int a = 1;\nif (a > 0) {\n  if (a > 1) {\n    a = 2;\n  }\n}"),

    ("if con bloque vacío",
     "int a = 1;\nif (a > 0) {\n}"),

    ("if-else con bloque vacío",
     "int a = 1;\nif (a > 0) {\n} else {\n}"),

    # ── Control de flujo: while ───────────────────────────────────────────
    ("while simple",
     "int i = 0;\nwhile (i < 10) {\n  i = i + 1;\n}"),

    ("while con break",
     "int i = 0;\nwhile (i < 10) {\n  if (i == 5) {\n    break;\n  }\n  i = i + 1;\n}"),

    ("while con cuerpo vacío",
     "int i = 0;\nwhile (i < 10) {\n}"),

    ("while del enunciado",
     "int step = 0;\nwhile (step < 3) {\n  step = step + 1;\n}"),

    # ── Control de flujo: do-while ────────────────────────────────────────
    ("do-while simple",
     "int v = 0;\ndo {\n  v = v + 1;\n} while (v < 5);"),

    ("do-while del enunciado",
     "int i = 0;\nint v = 0;\n"
     "do {\n"
     "  if (v >= 10) {\n    break;\n  }\n"
     "  v = (v + 1) * 2;\n"
     "  i = i + 1;\n"
     "  print(v);\n"
     "} while (i < 4);"),

    ("do-while con semicolon después",
     "int v = 0;\ndo {\n  v = v + 1;\n} while (v < 5);"),

    # ── Funciones ─────────────────────────────────────────────────────────
    ("función void sin parámetros",
     "void saluda() {\n  print('H');\n}"),

    ("función con retorno int",
     "int doble(int x) {\n  return x * 2;\n}"),

    ("función con retorno float",
     "float avg(float a, float b) {\n  float s = a + b;\n  return s / 2;\n}"),

    ("función con múltiples parámetros",
     "int suma(int a, int b, int c) {\n  return a + b + c;\n}"),

    ("función void con parámetros",
     "void move(int x, int y) {\n  print(x);\n  print(y);\n}"),

    ("función con tipo record como parámetro",
     "record Point(int x, int y);\nint getX(Point p) {\n  return p.x;\n}"),

    ("función con tipo record como retorno",
     "record Point(int x, int y);\n"
     "Point make(int x, int y) {\n  return new Point(x, y);\n}"),

    ("llamada a función como expresión",
     "int doble(int x) {\n  return x * 2;\n}\nint r = doble(5);"),

    ("llamada a función sin argumentos",
     "int getValor() {\n  return 42;\n}\nint r = getValor();"),

    ("llamada a función como sentencia standalone",
     "void f() {\n  print('X');\n}\nf();"),

    ("función del enunciado: energy",
     "record Vector(float x, float y);\n"
     "record Planet(Vector position, Vector velocity, float mass, boolean active);\n"
     "float energy(Planet p) {\n"
     "  float squareSpeed = p.velocity.x * p.velocity.x + p.velocity.y * p.velocity.y;\n"
     "  return 0.5 * p.mass * squareSpeed;\n"
     "}"),

    ("función que devuelve new",
     "record Point(int x, int y);\n"
     "record Line(Point a, Point b);\n"
     "Line lineFromCoords(int x1, int y1, int x2, int y2) {\n"
     "  return new Line(new Point(x1, y1), new Point(x2, y2));\n"
     "}"),

    # ── Sobrecarga de funciones ───────────────────────────────────────────
    ("sobrecarga de funciones",
     "int f(int x) {\n  return x;\n}\n"
     "float f(float x) {\n  return x;\n}"),

    # ── print ─────────────────────────────────────────────────────────────
    ("print char",
     "print('Y');"),

    ("print variable",
     "int v = 42;\nprint(v);"),

    ("print expresión",
     "print(1 + 2);"),

    ("print expresión booleana",
     "print(3 > 2);"),

    # ── Comentarios ───────────────────────────────────────────────────────
    ("comentario de línea",
     "// esto es un comentario\nint a = 1;"),

    ("comentario de bloque",
     "/* bloque\nmultilinea */\nint a = 1;"),

    ("comentario entre tokens",
     "int /* comentario */ a = 1;"),

    # ── Programa completo del enunciado ───────────────────────────────────
    ("programa completo del enunciado",
     """record Vector(float x, float y);
record Planet(Vector position, Vector velocity, float mass, boolean active);

void move(Planet p) {
  p.position.x = p.position.x + p.velocity.x;
  p.position.y = p.position.y + p.velocity.y;
}

float energy(Planet p) {
  float squareSpeed = p.velocity.x * p.velocity.x + p.velocity.y * p.velocity.y;
  return 0.5 * p.mass * squareSpeed;
}

Planet earth = new Planet(new Vector(0, 0), new Vector(1, 2), 5, true);

int step = 0;
while (step < 3) {
  if (!earth.active) {
    move(earth);
  }
  step = step + 1;
}

if (energy(earth) > 10.0) {
  print('Y');
} else {
  print('N');
}
"""),

    ("función sin ';' y ';' suelto después (son dos items separados)",
     "int f() {\n  return 1;\n}\n;"),

]

# ═══════════════════════════════════════════════════════════════════════════
# CASOS INVÁLIDOS — el parser debe rechazarlos (exit code != 0, con [ERROR])
# ═══════════════════════════════════════════════════════════════════════════
INVALID = [

    # ── Errores de declaración ────────────────────────────────────────────
    ("multi-declaración con asignación",
     "float d, e = 0xFF;"),

    ("multi-declaración parcial con asignación",
     "int a, b = 5;"),

    ("declaración sin tipo",
     "a = 5;"),   # sin declarar 'a' primero... pero espera,
    # esto SÍ es válido sintácticamente (lvalue ASSIGN expr).
    # Lo quitamos de INVALID y lo ponemos como válido.

    # ── Errores de asignación ─────────────────────────────────────────────
    ("asignación en medio de expresión",
     "int a = 4;\nint b = 2;\na + 4 * b = 3;"),

    # ── Errores de punto y coma ───────────────────────────────────────────
    ("falta de semicolon entre declaraciones",
     "int a = 5\nint b = 3;"),

    ("falta de semicolon al final",
     "int a = 5"),

    # ── Errores de expresión ──────────────────────────────────────────────
    ("operador sin operando derecho",
     "int a = 5 +;"),

    ("operador sin operando izquierdo (no unario)",
     "int a = * 5;"),

    ("asignación sin expresión",
     "int a =;"),

    ("paréntesis sin cerrar",
     "int a = (5 + 3;"),

    ("paréntesis de más al cerrar",
     "int a = (5 + 3));"),

    # ── Errores en control de flujo ───────────────────────────────────────
    ("if sin paréntesis de condición",
     "int a = 1;\nif a > 0 {\n  a = 0;\n}"),

    ("if sin llaves (Lava requiere llaves)",
     "int a = 1;\nif (a > 0)\n  a = 0;"),

    # ── Errores semánticos ────────────────────────────────────────────────
    ("tipo de registro no definido",
     "MiTipo a = new MiTipo(1, 2);"),

    ("return en función void",
     "void f() {\n  return 1;\n}"),

    ("función sin return",
     "int f() {\n}"),

    ("break fuera de bucle",
     "break;"),

    ("if sin condición",
     "if () {\n  int a = 1;\n}"),

    # ── Errores en funciones ──────────────────────────────────────────────
    ("función sin llaves",
     "int f(int x)\n  return x;"),

    ("función sin nombre",
     "int (int x) {\n  return x;\n}"),

    # ── Errores en records ────────────────────────────────────────────────
    ("new sin tipo",
     "int a = new (1, 2);"),

    ("record sin paréntesis",
     "record Point int x, int y;"),

    # ── Errores de tokens inesperados ─────────────────────────────────────
    ("token inesperado al inicio",
     "= 5;"),

    ("llaves sueltas",
     "{ int a = 1; }"),

    ("dos operadores seguidos",
     "int a = 5 + * 3;"),

]

# Limpiamos el caso que pusimos por error — "declaración sin tipo" es válido
INVALID = [case for case in INVALID if case[0] != "declaración sin tipo"]


def run_test(name: str, code: str, expect_valid: bool):
    with tempfile.NamedTemporaryFile(
        suffix=".lava", mode="w", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "main.py", path],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout + result.stderr
        is_valid = (result.returncode == 0) and ("[ERROR]" not in output)
        passed = (is_valid == expect_valid)
        return passed, output.strip()
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    finally:
        os.unlink(path)


def print_section(title: str):
    print(f"\n{BOLD}{CYAN}{'─' * 62}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 62}{RESET}")


def main():
    passed_total = 0
    failed_total = 0
    failures = []

    print_section("Tests VÁLIDOS  (el parser debe aceptarlos)")

    for name, code in VALID:
        ok, output = run_test(name, code, expect_valid=True)
        if ok:
            print(f"  {GREEN}✓{RESET}  {name}")
            passed_total += 1
        else:
            print(f"  {RED}✗{RESET}  {name}")
            if output:
                for line in output.splitlines():
                    print(f"      {GRAY}{line}{RESET}")
            failed_total += 1
            failures.append(("VÁLIDO", name, output))

    print_section("Tests INVÁLIDOS  (el parser debe rechazarlos)")

    for name, code in INVALID:
        ok, output = run_test(name, code, expect_valid=False)
        if ok:
            print(f"  {GREEN}✓{RESET}  {name}")
            passed_total += 1
        else:
            print(f"  {RED}✗{RESET}  {name}")
            if output:
                for line in output.splitlines():
                    print(f"      {GRAY}{line}{RESET}")
            failed_total += 1
            failures.append(("INVÁLIDO", name, output))

    total = passed_total + failed_total
    print(f"\n{'─' * 62}")
    pct = int(passed_total / total * 100) if total else 0
    color = GREEN if failed_total == 0 else RED
    print(f"  {BOLD}Resultado: {color}{passed_total}/{total}{RESET}"
          f"  ({pct}%)", end="")
    if failed_total == 0:
        print(f"  {GREEN}— ¡Sin errores!{RESET}")
    else:
        print(f"  |  {RED}{failed_total} fallidos{RESET}")

    if failures:
        print(f"\n{BOLD}Resumen de fallos:{RESET}")
        for kind, name, output in failures:
            print(f"  {RED}[{kind}]{RESET} {name}")
            if output:
                first_line = output.splitlines()[0]
                print(f"    {DIM}{first_line}{RESET}")

    print(f"{'─' * 62}\n")
    sys.exit(0 if failed_total == 0 else 1)


if __name__ == "__main__":
    main()
