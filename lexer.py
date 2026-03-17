import ply.lex as lex

# Variable global para rastrear la columna total
total_columns = 0

class Lexer:
    def __init__(self) -> None:
        self.lexer = lex.lex(module=self)

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
        return self.build_column_info(t)

    def t_LE(self, t):
        r'<='
        return self.build_column_info(t)

    def t_EQ(self, t):
        r'=='
        return self.build_column_info(t)

    def t_AND(self, t):
        r'&&'
        return self.build_column_info(t)

    def t_OR(self, t):
        r'\|\|'
        return self.build_column_info(t)

    # Operadores de un carácter
    def t_PLUS(self, t):
        r'\+'
        return self.build_column_info(t)

    def t_MINUS(self, t):
        r'-'
        return self.build_column_info(t)

    def t_TIMES(self, t):
        r'\*'
        return self.build_column_info(t)

    def t_DIVIDE(self, t):
        r'/'
        return self.build_column_info(t)

    def t_GT(self, t):
        r'>'
        return self.build_column_info(t)

    def t_LT(self, t):
        r'<'
        return self.build_column_info(t)

    def t_ASSIGN(self, t):
        r'='
        return self.build_column_info(t)

    def t_NOT(self, t):
        r'!'
        return self.build_column_info(t)

    def t_DOT(self, t):
        r'\.'
        return self.build_column_info(t)

    def t_LPAREN(self, t):
        r'\('
        return self.build_column_info(t)

    def t_RPAREN(self, t):
        r'\)'
        return self.build_column_info(t)

    def t_LBRACE(self, t):
        r'\{'
        return self.build_column_info(t)

    def t_RBRACE(self, t):
        r'\}'
        return self.build_column_info(t)

    def t_COMMA(self, t):
        r','
        return self.build_column_info(t)

    def t_SEMICOLON(self, t):
        r';'
        return self.build_column_info(t)

    def build_column_info(self, t) -> None:
        """Calcula la posición de columna relativa a la línea actual"""
        global total_columns
        t.column_start = t.lexpos - total_columns + 1
        t.column_end = t.column_start + len(t.value)
        total_columns += len(t.value)
        return t

    def t_COMMENT(self, t):
        r'/\*[\s\S]*?\*/|//[^\n]*'
        n = t.value.count('\n')
        if n:
            global total_columns
            t.lexer.lineno += n
            total_columns = 0
        return None

    def t_FLOAT_VALUE(self, t):
        r'((0|[1-9]\d*)(\.\d+)?[eE][+-]?\d+)|((0|[1-9]\d*)\.\d+)'
        self.build_column_info(t)
        t.raw = t.value
        t.value = float(t.value)
        return t

    def t_INT_VALUE(self, t):
        r'0b[01]+|0x[0-9A-F]+|0[0-7]+|0|[1-9][0-9]*'
        self.build_column_info(t)
        t.raw = t.value
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

    def t_CHAR_VALUE(self, t):
        r"'(\\.|[^\n\\'])'"
        self.build_column_info(t)
        t.raw = t.value
        ch_str = t.value[1:-1]
        
        # Procesar secuencias de escape
        escape_map = {
            'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', "'": "'"
        }
        if ch_str.startswith('\\') and len(ch_str) == 2:
            ch = escape_map.get(ch_str[1], ch_str[1])
        else:
            ch = ch_str
        
        if ord(ch) > 255:
            print(f"ERROR: char fuera de ASCII-extendido en línea {t.lineno}")
            return None
        t.value = ch
        return t

    def t_ID(self, t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        self.build_column_info(t)
        t.type = self.reserved_map.get(t.value, 'ID')
        # Convertir TRUE y FALSE a booleanos
        if t.type == 'TRUE':
            t.value = True
        elif t.type == 'FALSE':
            t.value = False
        return t

    def t_newline(self, t):
        r'\n+'
        global total_columns
        t.lexer.lineno += t.value.count('\n')
        total_columns = 0

    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
        t.lexer.skip(1)
