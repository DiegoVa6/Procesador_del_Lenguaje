import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent


def run(file: Path):
    print(f"==> {file}")
    r = subprocess.run(
        [sys.executable, "main.py", "--token", str(file)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.stdout.strip():
        print(r.stdout)
    if r.stderr.strip():
        print("STDERR:", r.stderr)
    out = file.with_suffix(".token")
    ok = r.returncode == 0 and out.exists()
    print("token file:", "OK" if out.exists() else "MISSING")
    print("result:", "OK" if ok else "FAIL")
    print()
    return ok


def main():
    failed = 0
    for f in sorted(TESTS_DIR.glob("*.lava")):
        if not run(f):
            failed += 1

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
