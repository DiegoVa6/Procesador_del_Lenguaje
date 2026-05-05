import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lexer import Lexer

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tests_lexer/main_lexer.py <file.lava>")
        sys.exit(1)

    in_path = sys.argv[1]
    with open(in_path, 'r', encoding='utf-8') as f:
        data = f.read()

    lavalexer = Lexer()
    lavalexer.input(data)

    out_path = in_path.rsplit('.', 1)[0] + '.token'

    with open(out_path, 'w', encoding='utf-8') as out:
        while True:
            tok = lavalexer.token()
            if not tok:
                break
            
            # usar columnas que ya vienen calculadas en el token
            out.write(f"{tok.type}, {tok.value}, {tok.lineno}, {tok.col_start}, {tok.col_end}\n")


if __name__ == "__main__":
    main()
