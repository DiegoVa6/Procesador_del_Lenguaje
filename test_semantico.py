"""
test.py — Batería de pruebas semánticas para el compilador Lava (P3)
Ejecuta los ficheros .lava de la carpeta inputs/ y comprueba los
archivos de salida generados (.symbols, .records, .functions, .quartets).

Uso:  python test.py
      python test.py -v        (verbose: muestra todos los checks)
"""

import os
import sys
import subprocess
import pathlib

INPUTS_DIR  = pathlib.Path(__file__).parent / "test_semantico"
MAIN_PY     = pathlib.Path(__file__).parent / "main.py"
VERBOSE     = "-v" in sys.argv

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
results = []


def run_lava(lava_path):
    proc = subprocess.run(
        [sys.executable, str(MAIN_PY), str(lava_path)],
        capture_output=True, text=True
    )
    return proc.returncode, proc.stdout + proc.stderr


def read_output(lava_path, ext):
    out = lava_path.with_suffix(ext)
    if not out.exists():
        return None
    return [l.rstrip() for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]


def cleanup(lava_path):
    for ext in (".symbols", ".records", ".functions", ".quartets", ".token"):
        f = lava_path.with_suffix(ext)
        if f.exists():
            f.unlink()


class TestCase:
    def __init__(self, name, lava_path):
        self.name      = name
        self.lava_path = lava_path
        self.checks    = []
        self.ok        = True
        self.msgs      = []

    def run(self):
        cleanup(self.lava_path)
        rc, output = run_lava(self.lava_path)
        self._rc     = rc
        self._output = output
        self._sym    = read_output(self.lava_path, ".symbols")
        self._rec    = read_output(self.lava_path, ".records")
        self._fn     = read_output(self.lava_path, ".functions")
        self._qrt    = read_output(self.lava_path, ".quartets")
        for fn in self.checks:
            fn()
        results.append((self.ok, self.name, self.msgs))
        label = f"{PASS if self.ok else FAIL} {self.name}"
        print(label)
        for m in self.msgs:
            print(f"     {m}")

    def expect_no_errors(self):
        def check():
            if self._rc != 0 or "ERROR" in self._output:
                self.ok = False
                self.msgs.append(f"  Errores inesperados:\n    {self._output.strip()[:300]}")
        self.checks.append(check)
        return self

    def expect_errors(self, *substrings):
        def check():
            if self._rc == 0 and "ERROR" not in self._output:
                self.ok = False
                self.msgs.append("  Se esperaban errores pero el análisis fue exitoso")
                return
            for s in substrings:
                if s not in self._output:
                    self.ok = False
                    self.msgs.append(f"  Error esperado no encontrado: '{s}'")
        self.checks.append(check)
        return self

    def symbols_contains(self, *lines):
        def check():
            if self._sym is None:
                self.ok = False; self.msgs.append("  .symbols no generado"); return
            for line in lines:
                if line not in self._sym:
                    self.ok = False
                    self.msgs.append(f"  .symbols falta '{line}'  actual:{self._sym}")
        self.checks.append(check)
        return self

    def symbols_exact(self, *lines):
        def check():
            if self._sym is None:
                self.ok = False; self.msgs.append("  .symbols no generado"); return
            exp, act = set(lines), set(self._sym)
            for l in exp - act: self.ok = False; self.msgs.append(f"  .symbols falta '{l}'")
            for l in act - exp: self.ok = False; self.msgs.append(f"  .symbols extra '{l}'")
        self.checks.append(check)
        return self

    def symbols_no_values(self, *var_names):
        def check():
            if self._sym is None:
                self.ok = False; self.msgs.append("  .symbols no generado"); return
            for vname in var_names:
                matching = [l for l in self._sym if l.startswith(f"{vname}:")]
                if not matching:
                    self.ok = False; self.msgs.append(f"  .symbols falta '{vname}'"); continue
                for l in matching:
                    if "," in l:
                        self.ok = False
                        self.msgs.append(f"  .symbols '{l}' tiene valor, esperaba solo tipo")
        self.checks.append(check)
        return self

    def symbols_not_contains(self, *var_names):
        def check():
            if self._sym is None: return
            for vname in var_names:
                if any(l.startswith(f"{vname}:") for l in self._sym):
                    self.ok = False
                    self.msgs.append(f"  .symbols '{vname}' no debería aparecer (local)")
        self.checks.append(check)
        return self

    def records_exact(self, *lines):
        def check():
            actual = self._rec or []
            exp, act = set(lines), set(actual)
            for l in exp - act: self.ok = False; self.msgs.append(f"  .records falta '{l}'")
            for l in act - exp: self.ok = False; self.msgs.append(f"  .records extra '{l}'")
        self.checks.append(check)
        return self

    def records_contains(self, *lines):
        def check():
            actual = self._rec or []
            for line in lines:
                if line not in actual:
                    self.ok = False; self.msgs.append(f"  .records falta '{line}'")
        self.checks.append(check)
        return self

    def functions_exact(self, *lines):
        def check():
            actual = self._fn or []
            exp, act = set(lines), set(actual)
            for l in exp - act: self.ok = False; self.msgs.append(f"  .functions falta '{l}'")
            for l in act - exp: self.ok = False; self.msgs.append(f"  .functions extra '{l}'")
        self.checks.append(check)
        return self

    def functions_contains(self, *lines):
        def check():
            actual = self._fn or []
            for line in lines:
                if line not in actual:
                    self.ok = False; self.msgs.append(f"  .functions falta '{line}'")
        self.checks.append(check)
        return self

    def quartets_contain(self, *quartets):
        def check():
            if self._qrt is None:
                self.ok = False; self.msgs.append("  .quartets no generado"); return
            idx = 0
            for q in quartets:
                found = False
                while idx < len(self._qrt):
                    if self._qrt[idx] == q:
                        found = True; idx += 1; break
                    idx += 1
                if not found:
                    self.ok = False
                    self.msgs.append(f"  .quartets '{q}' no encontrado (o fuera de orden)")
        self.checks.append(check)
        return self

    def quartets_not_contain(self, *quartets):
        def check():
            if self._qrt is None: return
            for q in quartets:
                if q in self._qrt:
                    self.ok = False; self.msgs.append(f"  .quartets '{q}' no debería aparecer")
        self.checks.append(check)
        return self

    def no_output_files(self):
        def check():
            for ext in (".symbols", ".records", ".functions", ".quartets"):
                f = self.lava_path.with_suffix(ext)
                if f.exists():
                    self.ok = False; self.msgs.append(f"  Se generó {f.name} pese a errores")
        self.checks.append(check)
        return self


def T(name, filename):
    return TestCase(name, INPUTS_DIR / filename)


# ══════════════════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════════════════

print("\n── Input 01: Símbolos Básicos ────────────────────────────────────")
T("01-A Valores int/float/char/boolean en .symbols","input_01_simbolos_basicos.lava").expect_no_errors().symbols_contains("a:int,99","b:float,24.9","c:char,K","flag:boolean,false").run()
T("01-B Valores calculados (sin control flow)","input_01_simbolos_basicos.lava").expect_no_errors().symbols_contains("suma:int,8","prod:int,28","div:float,2.5").run()
T("01-C Widening int→float y char→float","input_01_simbolos_basicos.lava").expect_no_errors().symbols_contains("wf1:float,7.0","wf2:float,65.0").run()
T("01-D Multideclaración — ambas variables con valor","input_01_simbolos_basicos.lava").expect_no_errors().symbols_contains("x:int,10","y:int,90").run()
T("01-E .records y .functions vacíos","input_01_simbolos_basicos.lava").expect_no_errors().records_exact().functions_exact().run()
T("01-F Cuartetos declaraciones con valor","input_01_simbolos_basicos.lava").expect_no_errors().quartets_contain("ASSIGN,28,_,a","ASSIGN,24.9,_,b","ASSIGN,\'K\',_,c","ASSIGN,true,_,flag").run()
T("01-G Cuarteto operación aritmética (suma=3+5)","input_01_simbolos_basicos.lava").expect_no_errors().quartets_contain("ADD,3,5,@T1","ASSIGN,@T1,_,suma").run()
T("01-H Cuarteto widening int→float","input_01_simbolos_basicos.lava").expect_no_errors().quartets_contain("INT_TO_FLOAT,7,_,@T4","ASSIGN,@T4,_,wf1").run()
T("01-I Cuarteto widening char→float","input_01_simbolos_basicos.lava").expect_no_errors().quartets_contain("CHAR_TO_INT,\'A\',_,@T5","INT_TO_FLOAT,@T5,_,@T6","ASSIGN,@T6,_,wf2").run()

print("\n── Input 02: Registros ──────────────────────────────────────────")
T("02-A Records en .records","input_02_registros.lava").expect_no_errors().records_exact("Vector:[x:float,y:float]","Planet:[position:Vector,velocity:Vector,mass:float,active:boolean]").run()
T("02-B Instanciación + asignación a propiedad en .symbols","input_02_registros.lava").expect_no_errors().symbols_contains("v1:Vector,{x:9.0,y:4.0}").run()
T("02-C Record anidado con campo modificado","input_02_registros.lava").expect_no_errors().symbols_contains("earth:Planet,{position:{x:100.0,y:0.0},velocity:{x:1.0,y:2.0},mass:5.0,active:false}").run()
T("02-D Acceso a propiedad simple → valor en symbols","input_02_registros.lava").expect_no_errors().symbols_contains("vx:float,3.0","vy:float,4.0","em:float,5.0").run()
T("02-E Acceso a propiedad anidada","input_02_registros.lava").expect_no_errors().symbols_contains("evy:float,2.0").run()
T("02-F Record sin inicializar → valores por defecto","input_02_registros.lava").expect_no_errors().symbols_contains("vdefault:Vector,{x:0.0,y:0.0}").run()
T("02-G Cuarteto acceso a propiedad (lvalue read)","input_02_registros.lava").expect_no_errors().quartets_contain("ASSIGN,v1.x,_,vx","ASSIGN,v1.y,_,vy").run()

print("\n── Input 03: Funciones ──────────────────────────────────────────")
T("03-A Funciones en .functions","input_03_funciones.lava").expect_no_errors().functions_contains("square:[f:float],float","squareInt:[i:int],int","debugVal:[v:int],void","makeSegment:[x1:int,y1:int,x2:int,y2:int],Line").run()
T("03-B Records de parámetros/retorno en .records","input_03_funciones.lava").expect_no_errors().records_contains("Point:[x:int,y:int]","Line:[a:Point,b:Point]").run()
T("03-C Variables globales en .symbols","input_03_funciones.lava").expect_no_errors().symbols_contains("d:float","n:int","r:int","rc:float").run()
T("03-D Variables locales NO en .symbols global","input_03_funciones.lava").expect_no_errors().symbols_not_contains("f","x1","y1","x2","y2").run()
T("03-E Con funciones → symbols sin valor","input_03_funciones.lava").expect_no_errors().symbols_no_values("d","n","r","rc").run()

print("\n── Input 04: Tipos y Widening ───────────────────────────────────")
T("04-A char+char→char","input_04_tipos_y_widening.lava").expect_no_errors().symbols_contains("cc:char,ab").run()
T("04-B int+int→int","input_04_tipos_y_widening.lava").expect_no_errors().symbols_contains("ii:int,21").run()
T("04-C float+float→float","input_04_tipos_y_widening.lava").expect_no_errors().symbols_contains("ff:float,4.0").run()
T("04-D char+int→int (widening)","input_04_tipos_y_widening.lava").expect_no_errors().symbols_contains("ci:int,98").run()
T("04-E int+float→float (widening)","input_04_tipos_y_widening.lava").expect_no_errors().symbols_contains("if1:float,3.5").run()
T("04-F char+float→float (widening doble)","input_04_tipos_y_widening.lava").expect_no_errors().symbols_contains("cf:float,66.5").run()
T("04-G Comparativas → boolean con valor correcto","input_04_tipos_y_widening.lava").expect_no_errors().symbols_contains("gt:boolean,true","gte:boolean,true","lt:boolean,true","lte:boolean,true","eq:boolean,true","beq:boolean,false").run()
T("04-H Lógicas booleanas","input_04_tipos_y_widening.lava").expect_no_errors().symbols_contains("band:boolean,false","bor:boolean,true","bnot:boolean,false").run()
T("04-I Unarios","input_04_tipos_y_widening.lava").expect_no_errors().symbols_contains("uminus:int,-5","uplus:float,3.14").run()
T("04-J Cuarteto CHAR_TO_INT en char+int","input_04_tipos_y_widening.lava").expect_no_errors().quartets_contain("CHAR_TO_INT,\'a\',_,@T4","ADD,@T4,1,@T5","ASSIGN,@T5,_,ci").run()
T("04-K Cuarteto INT_TO_FLOAT en int+float","input_04_tipos_y_widening.lava").expect_no_errors().quartets_contain("INT_TO_FLOAT,2,_,@T6","ADD,@T6,1.5,@T7","ASSIGN,@T7,_,if1").run()
T("04-L Cuarteto NOT booleano","input_04_tipos_y_widening.lava").expect_no_errors().quartets_contain("NOT,true,_,@T18","ASSIGN,@T18,_,bnot").run()
T("04-M Cuarteto UMINUS","input_04_tipos_y_widening.lava").expect_no_errors().quartets_contain("UMINUS,5,_,@T19","ASSIGN,@T19,_,uminus").run()

print("\n── Input 05: Control de Flujo ───────────────────────────────────")
T("05-A Con control flow → .symbols sin valores","input_05_control_flujo.lava").expect_no_errors().symbols_no_values("num","isPositive","counter","result","i","v","steps").run()
T("05-B Cuartetos if-else (spec ejemplo 2)","input_05_control_flujo.lava").expect_no_errors().quartets_contain("GTE,num,0,@T1","JUMPF,@T1,@L1,_","ASSIGN,true,_,isPositive","JUMP,@L2,_,_","LABEL,@L1,_,_","ASSIGN,false,_,isPositive","LABEL,@L2,_,_").run()
T("05-C Cuartetos while (spec ejemplo 3)","input_05_control_flujo.lava").expect_no_errors().quartets_contain("LABEL,@L3,_,_","LT,counter,5,@T2","JUMPF,@T2,@L4,_","ADD,counter,1,@T3","ASSIGN,@T3,_,counter","JUMP,@L3,_,_","LABEL,@L4,_,_").run()
T("05-D Cuartetos do-while (LABEL+JUMPT)","input_05_control_flujo.lava").expect_no_errors().quartets_contain("LABEL,@L5,_,_","ADD,i,1,@T6","ASSIGN,@T6,_,i","PRINT,i,_,_","LT,i,3,@T7","JUMPT,@T7,@L5,_").run()
T("05-E Cuarteto INT_TO_FLOAT en result=counter","input_05_control_flujo.lava").expect_no_errors().quartets_contain("INT_TO_FLOAT,counter,_,@T4","ASSIGN,@T4,_,result","UMINUS,result,_,@T5","ASSIGN,@T5,_,result").run()

print("\n── Input 06: Errores Semánticos ─────────────────────────────────")
T("06-A Fichero con errores → no genera archivos","input_06_errores_semanticos.lava").expect_errors().no_output_files().run()
T("06-B Error variable no declarada","input_06_errores_semanticos.lava").expect_errors("ERROR","\'z\'").run()
T("06-C Error redeclaración","input_06_errores_semanticos.lava").expect_errors("\'dup\'").run()
T("06-D Error reasignación tipo incorrecto","input_06_errores_semanticos.lava").expect_errors("boolean").run()
T("06-E Error break fuera de bucle","input_06_errores_semanticos.lava").expect_errors("break").run()
T("06-F Error record tipo inexistente","input_06_errores_semanticos.lava").expect_errors("Inexistente").run()
T("06-G Error campo repetido en record","input_06_errores_semanticos.lava").expect_errors("repetido").run()
T("06-H Error constructor args incorrecto","input_06_errores_semanticos.lava").expect_errors("2 argumento").run()
T("06-I Error función no declarada","input_06_errores_semanticos.lava").expect_errors("noExiste").run()
T("06-J Error char*char no permitido","input_06_errores_semanticos.lava").expect_errors("\'*\'").run()
T("06-K Error ! sobre int","input_06_errores_semanticos.lava").expect_errors("\'!\'").run()

print("\n── Input 07: Cuartetos del Enunciado ────────────────────────────")
T("07-A Spec ej.1 — expresiones aritméticas","input_07_cuartetos.lava").expect_no_errors().quartets_contain("MUL,5,4,@T1","DIV,80,10,@T2","SUB,@T1,@T2,@T3","ASSIGN,@T3,_,f1","LT,5,3,@T7","ASSIGN,@T7,_,b1").run()
T("07-B Spec ej.2 — if-else exacto","input_07_cuartetos.lava").expect_no_errors().quartets_contain("GTE,num,0,@T8","JUMPF,@T8,@L1,_","ASSIGN,true,_,isPositive","JUMP,@L2,_,_","LABEL,@L1,_,_","ASSIGN,false,_,isPositive","LABEL,@L2,_,_").run()
T("07-C Spec ej.3 — while con casts","input_07_cuartetos.lava").expect_no_errors().quartets_contain("LABEL,@L3,_,_","LT,counter,5,@T9","JUMPF,@T9,@L4,_","ADD,counter,1,@T10","ASSIGN,@T10,_,counter","INT_TO_FLOAT,counter,_,@T11","ASSIGN,@T11,_,result","UMINUS,result,_,@T12","ASSIGN,@T12,_,result","JUMP,@L3,_,_","LABEL,@L4,_,_").run()
T("07-D Defaults de declaración al inicio","input_07_cuartetos.lava").expect_no_errors().quartets_contain("ASSIGN,0.0,_,f1","ASSIGN,0.0,_,f2","ASSIGN,false,_,b1","ASSIGN,0,_,num","ASSIGN,false,_,isPositive","ASSIGN,0,_,counter","ASSIGN,0.0,_,result").run()

print("\n── Input 08: Programa Completo ──────────────────────────────────")
T("08-A Records del enunciado en .records","input_08_programa_completo.lava").expect_no_errors().records_exact("Vector:[x:float,y:float]","Planet:[position:Vector,velocity:Vector,mass:float,active:boolean]").run()
T("08-B Funciones del enunciado en .functions","input_08_programa_completo.lava").expect_no_errors().functions_exact("move:[p:Planet],void","energy:[p:Planet],float").run()
T("08-C Variables globales sin valores","input_08_programa_completo.lava").expect_no_errors().symbols_no_values("earth","step").run()
T("08-D Variables locales NO en .symbols","input_08_programa_completo.lava").expect_no_errors().symbols_not_contains("squareSpeed","p").run()
T("08-E Cuartetos operaciones dentro de funciones","input_08_programa_completo.lava").expect_no_errors().quartets_contain("MUL,p.velocity.x,p.velocity.x,@T3","MUL,p.velocity.y,p.velocity.y,@T4","ADD,@T3,@T4,@T5","ASSIGN,@T5,_,squareSpeed").run()
T("08-F Cuartetos del while principal","input_08_programa_completo.lava").expect_no_errors().quartets_contain("LABEL,@L1,_,_","LT,step,3,@T8","JUMPF,@T8,@L2,_","JUMP,@L1,_,_","LABEL,@L2,_,_").run()

# ══════════════════════════════════════════════════════════════════════════
total  = len(results)
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
            for m in msgs: print(f"     {m}")
else:
    print("  — ¡Todo correcto!")
