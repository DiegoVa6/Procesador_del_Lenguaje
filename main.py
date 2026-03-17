import sys
from lexer import Lexer

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <file.lava>")
        sys.exit(1)

    in_path = sys.argv[1]
    with open(in_path, 'r', encoding='utf-8') as f:
        data = f.read()

    lavalexer = Lexer()
    lavalexer.lexer.lineno = 1
    lavalexer.lexer.input(data)

    out_path = in_path.rsplit('.', 1)[0] + '.token'

    with open(out_path, 'w', encoding='utf-8') as out:
        while True:
            tok = lavalexer.lexer.token()
            if not tok:
                break
            # columna inicio = posición del token − inicio de su línea
            col_start = tok.lexpos - lavalexer.line_start
            # usa raw para longitud real
            raw = getattr(tok, "raw", None)
            lexeme_len = len(raw) if raw is not None else len(str(tok.value))
            col_end = col_start + lexeme_len
            out.write(f"{tok.type}, {tok.value}, {tok.lineno}, {col_start}, {col_end}\n")


if __name__ == "__main__":
    main()
