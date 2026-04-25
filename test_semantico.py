"""
test_semantico.py — Batería de pruebas semánticas para el compilador Lava (P3)

Ejecuta los ficheros .lava de la carpeta test_semantico/ y comprueba los
archivos de salida generados por main.py:
    - .symbols
    - .records
    - .functions

Uso:
    python test_semantico.py
    python test_semantico.py -v
"""

import sys
import subprocess
import pathlib

INPUTS_DIR = pathlib.Path(__file__).parent / "test_semantico"
MAIN_PY = pathlib.Path(__file__).parent / "main.py"
VERBOSE = "-v" in sys.argv

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
results = []


def run_lava(lava_path: pathlib.Path):
    proc = subprocess.run(
        [sys.executable, str(MAIN_PY), str(lava_path)],
        capture_output=True,
        text=True
    )
    return proc.returncode, proc.stdout + proc.stderr


def read_output(lava_path: pathlib.Path, ext: str):
    out = lava_path.with_suffix(ext)
    if not out.exists():
        return None
    return [line.rstrip() for line in out.read_text(encoding="utf-8").splitlines() if line.strip()]


def cleanup(lava_path: pathlib.Path):
    for ext in (".symbols", ".records", ".functions", ".token"):
        f = lava_path.with_suffix(ext)
        if f.exists():
            f.unlink()


class TestCase:
    def __init__(self, name: str, lava_path: pathlib.Path):
        self.name = name
        self.lava_path = lava_path
        self.checks = []
        self.ok = True
        self.msgs = []

    def run(self):
        cleanup(self.lava_path)
        rc, output = run_lava(self.lava_path)

        self._rc = rc
        self._output = output
        self._sym = read_output(self.lava_path, ".symbols")
        self._rec = read_output(self.lava_path, ".records")
        self._fn = read_output(self.lava_path, ".functions")

        for fn in self.checks:
            fn()

        results.append((self.ok, self.name, self.msgs))
        print(f"{PASS if self.ok else FAIL} {self.name}")

        if VERBOSE or not self.ok:
            for m in self.msgs:
                print(f"     {m}")

    def expect_no_errors(self):
        def check():
            if self._rc != 0 or "ERROR" in self._output:
                self.ok = False
                snippet = self._output.strip()[:400]
                self.msgs.append(f"Errores inesperados:\n{snippet}")
        self.checks.append(check)
        return self

    def expect_errors(self, *substrings):
        def check():
            if self._rc == 0 and "ERROR" not in self._output:
                self.ok = False
                self.msgs.append("Se esperaban errores pero el análisis fue exitoso")
                return

            for s in substrings:
                if s not in self._output:
                    self.ok = False
                    self.msgs.append(f"Error esperado no encontrado: '{s}'")
        self.checks.append(check)
        return self

    def symbols_contains(self, *lines):
        def check():
            if self._sym is None:
                self.ok = False
                self.msgs.append(".symbols no generado")
                return

            for line in lines:
                if line not in self._sym:
                    self.ok = False
                    self.msgs.append(f".symbols falta '{line}' | actual={self._sym}")
        self.checks.append(check)
        return self

    def symbols_exact(self, *lines):
        def check():
            if self._sym is None:
                self.ok = False
                self.msgs.append(".symbols no generado")
                return

            exp, act = set(lines), set(self._sym)
            for l in exp - act:
                self.ok = False
                self.msgs.append(f".symbols falta '{l}'")
            for l in act - exp:
                self.ok = False
                self.msgs.append(f".symbols extra '{l}'")
        self.checks.append(check)
        return self

    def symbols_no_values(self, *var_names):
        def check():
            if self._sym is None:
                self.ok = False
                self.msgs.append(".symbols no generado")
                return

            for vname in var_names:
                matching = [l for l in self._sym if l.startswith(f"{vname}:")]
                if not matching:
                    self.ok = False
                    self.msgs.append(f".symbols falta '{vname}'")
                    continue

                for l in matching:
                    if "," in l:
                        self.ok = False
                        self.msgs.append(f".symbols '{l}' tiene valor, esperaba solo tipo")
        self.checks.append(check)
        return self

    def symbols_not_contains(self, *var_names):
        def check():
            if self._sym is None:
                return

            for vname in var_names:
                if any(l.startswith(f"{vname}:") for l in self._sym):
                    self.ok = False
                    self.msgs.append(f".symbols '{vname}' no debería aparecer (local)")
        self.checks.append(check)
        return self

    def records_exact(self, *lines):
        def check():
            actual = self._rec or []
            exp, act = set(lines), set(actual)

            for l in exp - act:
                self.ok = False
                self.msgs.append(f".records falta '{l}'")
            for l in act - exp:
                self.ok = False
                self.msgs.append(f".records extra '{l}'")
        self.checks.append(check)
        return self

    def records_contains(self, *lines):
        def check():
            actual = self._rec or []
            for line in lines:
                if line not in actual:
                    self.ok = False
                    self.msgs.append(f".records falta '{line}'")
        self.checks.append(check)
        return self

    def functions_exact(self, *lines):
        def check():
            actual = self._fn or []
            exp, act = set(lines), set(actual)

            for l in exp - act:
                self.ok = False
                self.msgs.append(f".functions falta '{l}'")
            for l in act - exp:
                self.ok = False
                self.msgs.append(f".functions extra '{l}'")
        self.checks.append(check)
        return self

    def functions_contains(self, *lines):
        def check():
            actual = self._fn or []
            for line in lines:
                if line not in actual:
                    self.ok = False
                    self.msgs.append(f".functions falta '{line}'")
        self.checks.append(check)
        return self

    def no_output_files(self):
        def check():
            for ext in (".symbols", ".records", ".functions"):
                f = self.lava_path.with_suffix(ext)
                if f.exists():
                    self.ok = False
                    self.msgs.append(f"Se generó {f.name} pese a errores")
        self.checks.append(check)
        return self


def T(name: str, filename: str):
    return TestCase(name, INPUTS_DIR / filename)


# ════════════════════════════════════════════════════════════════════════
# TESTS
# ════════════════════════════════════════════════════════════════════════

print("\n── Input 01: Símbolos Básicos ────────────────────────────────────")
T("01-A Valores básicos en .symbols", "input_01_simbolos_basicos.lava")\
    .expect_no_errors()\
    .symbols_contains("a:int,99", "b:float,24.9", "c:char,K", "flag:boolean,false")\
    .run()

T("01-B Valores calculados", "input_01_simbolos_basicos.lava")\
    .expect_no_errors()\
    .symbols_contains("suma:int,8", "prod:int,28", "div:float,2.5")\
    .run()

T("01-C Widening int→float y char→float", "input_01_simbolos_basicos.lava")\
    .expect_no_errors()\
    .symbols_contains("wf1:float,7.0", "wf2:float,65.0")\
    .run()

T("01-D Multideclaración", "input_01_simbolos_basicos.lava")\
    .expect_no_errors()\
    .symbols_contains("x:int,10", "y:int,90")\
    .run()

T("01-E .records y .functions vacíos", "input_01_simbolos_basicos.lava")\
    .expect_no_errors()\
    .records_exact()\
    .functions_exact()\
    .run()

print("\n── Input 02: Registros ──────────────────────────────────────────")
T("02-A Records en .records", "input_02_registros.lava")\
    .expect_no_errors()\
    .records_exact(
        "Vector:[x:float,y:float]",
        "Planet:[position:Vector,velocity:Vector,mass:float,active:boolean]"
    )\
    .run()

T("02-B Instanciación + asignación a propiedad", "input_02_registros.lava")\
    .expect_no_errors()\
    .symbols_contains("v1:Vector,{x:9.0,y:4.0}")\
    .run()

T("02-C Record anidado modificado", "input_02_registros.lava")\
    .expect_no_errors()\
    .symbols_contains("earth:Planet,{position:{x:100.0,y:0.0},velocity:{x:1.0,y:2.0},mass:5.0,active:false}")\
    .run()

T("02-D Acceso a propiedad simple", "input_02_registros.lava")\
    .expect_no_errors()\
    .symbols_contains("vx:float,3.0", "vy:float,4.0", "em:float,5.0")\
    .run()

T("02-E Acceso a propiedad anidada", "input_02_registros.lava")\
    .expect_no_errors()\
    .symbols_contains("evy:float,2.0")\
    .run()

T("02-F Record sin inicializar", "input_02_registros.lava")\
    .expect_no_errors()\
    .symbols_contains("vdefault:Vector,{x:0.0,y:0.0}")\
    .run()

print("\n── Input 03: Funciones ──────────────────────────────────────────")
T("03-A Funciones en .functions", "input_03_funciones.lava")\
    .expect_no_errors()\
    .functions_contains(
        "square:[f:float],float",
        "squareInt:[i:int],int",
        "debugVal:[v:int],void",
        "makeSegment:[x1:int,y1:int,x2:int,y2:int],Line"
    )\
    .run()

T("03-B Records usados por funciones", "input_03_funciones.lava")\
    .expect_no_errors()\
    .records_contains("Point:[x:int,y:int]", "Line:[a:Point,b:Point]")\
    .run()

T("03-C Variables globales en .symbols", "input_03_funciones.lava")\
    .expect_no_errors()\
    .symbols_contains("d:float", "n:int", "r:int", "rc:float")\
    .run()

T("03-D Variables locales no aparecen en .symbols", "input_03_funciones.lava")\
    .expect_no_errors()\
    .symbols_not_contains("f", "x1", "y1", "x2", "y2")\
    .run()

T("03-E Con funciones, .symbols sin valores", "input_03_funciones.lava")\
    .expect_no_errors()\
    .symbols_no_values("d", "n", "r", "rc")\
    .run()

print("\n── Input 04: Tipos y Widening ───────────────────────────────────")
T("04-A char+char→char", "input_04_tipos_y_widening.lava")\
    .expect_no_errors()\
    .symbols_contains("cc:char,ab")\
    .run()

T("04-B int+int→int", "input_04_tipos_y_widening.lava")\
    .expect_no_errors()\
    .symbols_contains("ii:int,21")\
    .run()

T("04-C float+float→float", "input_04_tipos_y_widening.lava")\
    .expect_no_errors()\
    .symbols_contains("ff:float,4.0")\
    .run()

T("04-D char+int→int", "input_04_tipos_y_widening.lava")\
    .expect_no_errors()\
    .symbols_contains("ci:int,98")\
    .run()

T("04-E int+float→float", "input_04_tipos_y_widening.lava")\
    .expect_no_errors()\
    .symbols_contains("if1:float,3.5")\
    .run()

T("04-F char+float→float", "input_04_tipos_y_widening.lava")\
    .expect_no_errors()\
    .symbols_contains("cf:float,66.5")\
    .run()

T("04-G Comparativas", "input_04_tipos_y_widening.lava")\
    .expect_no_errors()\
    .symbols_contains(
        "gt:boolean,true",
        "gte:boolean,true",
        "lt:boolean,true",
        "lte:boolean,true",
        "eq:boolean,true",
        "beq:boolean,false"
    )\
    .run()

T("04-H Lógicas booleanas", "input_04_tipos_y_widening.lava")\
    .expect_no_errors()\
    .symbols_contains("band:boolean,false", "bor:boolean,true", "bnot:boolean,false")\
    .run()

T("04-I Unarios", "input_04_tipos_y_widening.lava")\
    .expect_no_errors()\
    .symbols_contains("uminus:int,-5", "uplus:float,3.14")\
    .run()

print("\n── Input 05: Control de Flujo ───────────────────────────────────")
T("05-A Con control flow, .symbols sin valores", "input_05_control_flujo.lava")\
    .expect_no_errors()\
    .symbols_no_values("num", "isPositive", "counter", "result", "i", "v", "steps")\
    .run()

print("\n── Input 06: Errores Semánticos ─────────────────────────────────")
T("06-A Fichero con errores no genera archivos", "input_06_errores_semanticos.lava")\
    .expect_errors()\
    .no_output_files()\
    .run()

T("06-B Variable no declarada", "input_06_errores_semanticos.lava")\
    .expect_errors("ERROR", "'z'")\
    .run()

T("06-C Redeclaración", "input_06_errores_semanticos.lava")\
    .expect_errors("'dup'")\
    .run()

T("06-D Reasignación con tipo incorrecto", "input_06_errores_semanticos.lava")\
    .expect_errors("boolean")\
    .run()

T("06-E break fuera de bucle", "input_06_errores_semanticos.lava")\
    .expect_errors("break")\
    .run()

T("06-F Record con tipo inexistente", "input_06_errores_semanticos.lava")\
    .expect_errors("Inexistente")\
    .run()

T("06-G Campo repetido en record", "input_06_errores_semanticos.lava")\
    .expect_errors("repetido")\
    .run()

T("06-H Constructor con argumentos incorrectos", "input_06_errores_semanticos.lava")\
    .expect_errors("2 argumento")\
    .run()

T("06-I Función no declarada", "input_06_errores_semanticos.lava")\
    .expect_errors("noExiste")\
    .run()

T("06-J char*char no permitido", "input_06_errores_semanticos.lava")\
    .expect_errors("*")\
    .run()

T("06-K ! sobre int", "input_06_errores_semanticos.lava")\
    .expect_errors("!")\
    .run()

print("\n── Input 08: Programa Completo ──────────────────────────────────")
T("08-A Records del enunciado en .records", "input_08_programa_completo.lava")\
    .expect_no_errors()\
    .records_exact(
        "Vector:[x:float,y:float]",
        "Planet:[position:Vector,velocity:Vector,mass:float,active:boolean]"
    )\
    .run()

T("08-B Funciones del enunciado en .functions", "input_08_programa_completo.lava")\
    .expect_no_errors()\
    .functions_exact("move:[p:Planet],void", "energy:[p:Planet],float")\
    .run()

T("08-C Variables globales sin valores", "input_08_programa_completo.lava")\
    .expect_no_errors()\
    .symbols_no_values("earth", "step")\
    .run()

T("08-D Variables locales no aparecen en .symbols", "input_08_programa_completo.lava")\
    .expect_no_errors()\
    .symbols_not_contains("squareSpeed", "p")\
    .run()


# ════════════════════════════════════════════════════════════════════════
# RESUMEN
# ════════════════════════════════════════════════════════════════════════

total = len(results)
passed = sum(1 for ok, _, _ in results if ok)
failed = total - passed

print()
print("─" * 60)
print(f"Resultado: {passed}/{total} tests pasados", end="")

if failed:
    print(f"  —  {failed} fallidos\n")
    for ok, name, msgs in results:
        if not ok:
            print(f"  {FAIL} {name}")
            for m in msgs:
                print(f"     {m}")
else:
    print("  — ¡Todo correcto!")