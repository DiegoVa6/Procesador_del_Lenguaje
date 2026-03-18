import glob
import subprocess
import sys
from pathlib import Path

def run(file):
    print(f"==> {file}")
    r = subprocess.run([sys.executable, "main.py", file], capture_output=True, text=True)
    if r.stdout.strip():
        print(r.stdout)
    if r.stderr.strip():
        print("STDERR:", r.stderr)
    out = Path(file).with_suffix(".token")
    print("token file:", "OK" if out.exists() else "MISSING")
    print()

def main():
    for f in glob.glob("*.lava"):
        run(f)

if __name__ == "__main__":
    main()
