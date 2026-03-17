import ply.lex as lex

#REGEXP para hacer pruebas
class Lexer:
    def __init__(self) -> None:
        self.lexer = lex.lex(module=self)
        self.line_start = 0

    reserved = (
        'TRUE',
        'FALSE',
        'INT',
        'FLOAT',
        'CHAR',
        'BOOLEAN',
        'VOID',
        'RETURN',
        'IF',
        'ELSE',
        'DO',
        'WHILE',
        'PRINT',
        'NEW',
        'RECORD',
        'BREAK'
    ) # Esta correcto

    tokens = reserved + (
        # Identificadores y literales
        'ID', 'INT_VALUE', 'FLOAT_VALUE', 'CHAR_VALUE',

        # Operadores
        'PLUS','MINUS','TIMES','DIVIDE',
        'AND','OR','NOT',
        'GT','GE','LT','LE','EQ',
        'ASSIGN',
        'DOT',

        # Separadores
        'LPAREN','RPAREN','LBRACE','RBRACE',
        'COMMA','SEMICOLON',
    )

    reserved_map = {r.lower(): r for r in reserved}

    t_ignore = ' \t\r'

    # Operadores de dos caracteres (primero para evitar conflictos con de un carácter)
    def t_GE(self, t):
        r'>='
        self.build_column_info(t)
        return t

    def t_LE(self, t):
        r'<='
        self.build_column_info(t)
        return t

    def t_EQ(self, t):
        r'=='
        self.build_column_info(t)
        return t

    def t_AND(self, t):
        r'&&'
        self.build_column_info(t)
        return t

    def t_OR(self, t):
        r'\|\|'
        self.build_column_info(t)
        return t

    # Operadores de un carácter
    def t_PLUS(self, t):
        r'\+'
        self.build_column_info(t)
        return t

    def t_MINUS(self, t):
        r'-'
        self.build_column_info(t)
        return t

    def t_TIMES(self, t):
        r'\*'
        self.build_column_info(t)
        return t

    def t_DIVIDE(self, t):
        r'/'
        self.build_column_info(t)
        return t

    def t_GT(self, t):
        r'>'
        self.build_column_info(t)
        return t

    def t_LT(self, t):
        r'<'
        self.build_column_info(t)
        return t

    def t_ASSIGN(self, t):
        r'='
        self.build_column_info(t)
        return t

    def t_NOT(self, t):
        r'!'
        self.build_column_info(t)
        return t

    def t_DOT(self, t):
        r'\.'
        self.build_column_info(t)
        return t

    def t_LPAREN(self, t):
        r'\('
        self.build_column_info(t)
        return t

    def t_RPAREN(self, t):
        r'\)'
        self.build_column_info(t)
        return t

    def t_LBRACE(self, t):
        r'\{'
        self.build_column_info(t)
        return t

    def t_RBRACE(self, t):
        r'\}'
        self.build_column_info(t)
        return t

    def t_COMMA(self, t):
        r','
        self.build_column_info(t)
        return t

    def t_SEMICOLON(self, t):
        r';'
        self.build_column_info(t)
        return t

    def build_column_info(self, t) -> None:
        """Calcula la posición de columna relativa a la línea actual"""
        t.column_start = t.lexpos - self.line_start + 1
        t.column_end = t.column_start + len(t.value)

    def t_COMMENT(self, t):
        r'/\*[\s\S]*?\*/|//[^\n]*'
        n = t.value.count('\n')
        if n:
            t.lexer.lineno += n
            last_nl = t.value.rfind('\n')
            self.line_start = t.lexpos + last_nl + 1
        return None

    def t_FLOAT_VALUE(self, t):
        r'(\d+(\.\d+)?e[+-]?\d+)|(\d+\.\d+)'
        self.build_column_info(t)

        t.raw = t.value # guarda lexema original antse de convertirlo a float
        t.value = float(t.value)
        return t

    def t_INT_VALUE(self, t):
        r'0b[01]+|0x[0-9A-F]+|0[0-7]+|0|[1-9][0-9]*'
        self.build_column_info(t)

        t.raw = t.value  # lexema original
        s = t.value
        if s.startswith('0b'):
            t.value = int(s[2:], 2)
        elif s.startswith('0x'):
            t.value = int(s[2:], 16)
        elif s.startswith('0') and s != '0':
            t.value = int(s, 8)
        else:
            t.value = int(s, 10)

        return t

    def t_BAD_CHAR(self, t):
        r"'[^\n']{2,}'"
        print(f"ERROR: literal char inválido {t.value} en línea {t.lineno}")
        return None
    
    def t_CHAR_VALUE(self, t):
        r"'[^\n']'"
        self.build_column_info(t)

        t.raw = t.value
        ch = t.value[1]
        if ord(ch) > 255:
            print(f"ERROR: char fuera de ASCII-extendido en línea {t.lineno}")
            return None
        t.value = ch
        return t

    def t_ID(self, t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        self.build_column_info(t)

        t.type = self.reserved_map.get(t.value, 'ID') #detecta palabras reservadas
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count('\n')
        self.line_start = t.lexpos + len(t.value)

    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
        t.lexer.skip(1)
