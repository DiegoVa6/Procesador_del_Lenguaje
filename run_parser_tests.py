import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
TESTS_DIR = ROOT / "tests_parser"

VALID_DIR = TESTS_DIR / "valid"
INVALID_DIR = TESTS_DIR / "invalid"


def run_case(path: Path):
    proc = subprocess.run(
        [sys.executable, "main.py", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True
    )
    return proc.returncode, proc.stdout, proc.stderr


def check_dir(directory: Path, expect_ok: bool):
    passed = 0
    failed = 0

    for path in sorted(directory.glob("*.lava")):
        code, out, err = run_case(path)

        ok = (code == 0) if expect_ok else (code != 0)

        if ok:
            print(f"[OK]   {path.name}")
            passed += 1
        else:
            print(f"[FAIL] {path.name}")
            print(f"  returncode = {code}")
            if out.strip():
                print("  stdout:")
                print("  " + out.strip().replace("\n", "\n  "))
            if err.strip():
                print("  stderr:")
                print("  " + err.strip().replace("\n", "\n  "))
            failed += 1

    return passed, failed


def main():
    total_passed = 0
    total_failed = 0

    warmup = VALID_DIR / "01_empty.lava"
    if warmup.exists():
        run_case(warmup)

    print("=== VALID ===")
    p, f = check_dir(VALID_DIR, expect_ok=True)
    total_passed += p
    total_failed += f

    print("\n=== INVALID ===")
    p, f = check_dir(INVALID_DIR, expect_ok=False)
    total_passed += p
    total_failed += f

    print(f"\nResumen: {total_passed} OK, {total_failed} FAIL")
    sys.exit(1 if total_failed else 0)


if __name__ == "__main__":
    main()
