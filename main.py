import os
import sys

from lexer import Lexer
from parser import Parser


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def remove_semantic_outputs(input_path: str):
    base_path = os.path.splitext(input_path)[0]

    for ext in (".symbols", ".records", ".functions"):
        output_path = base_path + ext
        if os.path.exists(output_path):
            os.remove(output_path)


def token_value_to_text(tok):
    # Prioridad al lexema original si el lexer lo guardó
    if hasattr(tok, "raw"):
        return tok.raw

    # Para TRUE/FALSE, en tu lexer value es bool
    if tok.type == "TRUE":
        return "true"
    if tok.type == "FALSE":
        return "false"

    return str(tok.value)


def export_tokens(input_path: str):
    data = read_file(input_path)
    lexer = Lexer()
    lexer.input(data)

    output_path = os.path.splitext(input_path)[0] + ".token"

    with open(output_path, "w", encoding="utf-8") as out:
        while True:
            tok = lexer.token()
            if not tok:
                break

            value_text = token_value_to_text(tok)
            col_start = getattr(tok, "col_start", 0)
            col_end = getattr(tok, "col_end", col_start)

            out.write(
                f"{tok.type}, {value_text}, {tok.lineno}, {col_start}, {col_end}\n"
            )


def run_parser(input_path: str) -> int:
    remove_semantic_outputs(input_path)

    data = read_file(input_path)
    parser = Parser()
    parser.parse(data)

    if not parser.has_errors:
        parser.write_symbols_file(input_path)
        parser.write_records_file(input_path)
        parser.write_functions_file(input_path)

    return 1 if parser.has_errors else 0


def usage():
    print("Uso:")
    print("  python main.py fichero.lava")
    print("  python main.py --token fichero.lava")


def main():
    if len(sys.argv) == 2:
        input_path = sys.argv[1]
        sys.exit(run_parser(input_path))

    elif len(sys.argv) == 3 and sys.argv[1] == "--token":
        input_path = sys.argv[2]
        export_tokens(input_path)
        sys.exit(0)

    else:
        usage()
        sys.exit(1)


if __name__ == "__main__":
    main()