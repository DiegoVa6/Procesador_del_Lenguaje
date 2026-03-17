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
<<<<<<< HEAD
            # Usar los valores de columna calculados por el lexer
            col_start = tok.column_start
            col_end = tok.column_end
=======
            col_start = tok.lexpos - lavalexer.line_start

            raw = getattr(tok, "raw", None)
            lexeme_len = len(raw) if raw is not None else len(str(tok.value))
            col_end = col_start + lexeme_len
>>>>>>> parent of caf0ce4 (comentarios)
            out.write(f"{tok.type}, {tok.value}, {tok.lineno}, {col_start}, {col_end}\n")


if __name__ == "__main__":
    main()
