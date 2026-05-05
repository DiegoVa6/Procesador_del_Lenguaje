import ply.lex as lex

#REGEXP para hacer pruebas
class Lexer:
    def __init__(self) -> None:
        self.lexer = lex.lex(module=self)
        self.line_start = 0
        self.has_errors = False
    
    def input(self, data):
        self.has_errors = False
        self.line_start = 0
        self.lexer.lineno = 1
        self.lexer.input(data)

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
    ) # Está correcto

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

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'

    t_AND = r'&&'
    t_OR = r'\|\|'
    t_NOT = r'!'

    t_GE = r'>='
    t_GT = r'>'
    t_LE = r'<='
    t_LT = r'<'
    t_EQ = r'=='
    t_ASSIGN = r'='

    t_DOT = r'\.'

    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_COMMA = r','
    t_SEMICOLON = r';'

    t_ignore = ' \t\r'

    # Sobrescribo el método token para calcular columnas
    def token(self):
        tok = self.lexer.token()
        
        if tok:
            raw_lexeme = getattr(tok, 'raw', str(tok.value))
            tok.col_start = tok.lexpos - self.line_start
            tok.col_end = tok.col_start + len(raw_lexeme)
        
        return tok


    def t_COMMENT(self, t):
        r'/\*[\s\S]*?\*/|//[^\n]*'
        n = t.value.count('\n')
        if n:
            t.lexer.lineno += n
            last_nl = t.value.rfind('\n')
            self.line_start = t.lexpos + last_nl + 1
        return None

    def t_FLOAT_VALUE(self, t):
        r'(([1-9][0-9]*|0)(\.[0-9]+)?e[+-]?[0-9]+)|((0|[1-9][0-9]*)\.[0-9]+)'
        t.raw = t.value # guarda lexema original antes de convertirlo a float
        t.value = float(t.value)
        return t

    def t_INT_VALUE(self, t):
        r'0b[01]+|0x[0-9A-F]+|0[0-7]+|0|[1-9][0-9]*'
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
    
    def t_CHAR_VALUE(self, t):
        r"'[\s\S]'"
        t.raw = t.value
        ch = t.value[1]
        if ord(ch) > 255:
            self.has_errors = True
            print(f"[ERROR LÉXICO] char fuera de ASCII-extendido en línea {t.lineno}")
            return None
        t.value = ch
        return t

    def t_ID(self, t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        t.type = self.reserved_map.get(t.value, 'ID') #detecta palabras reservadas
        if t.type == 'TRUE':
            t.value = True
        elif t.type == 'FALSE':
            t.value = False
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count('\n')
        self.line_start = t.lexpos + len(t.value)

    def t_error(self, t):
        self.has_errors = True
        col = t.lexpos - self.line_start
        print(f"[ERROR LÉXICO] Caracter ilegal '{t.value[0]}' en linea {t.lineno}, columna {col}")
        t.lexer.skip(1)
