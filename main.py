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
            tok = lavalexer.token()
            if not tok:
                break
            
            # usar columana que ya vienen calculadas en el token
            out.write(f"{tok.type}, {tok.value}, {tok.lineno}, {tok.col_start}, {tok.col_end}\n")

    print(f"Analisis completo.Tokens generated and saved to {out_path}")

if __name__ == "__main__":
    main()
