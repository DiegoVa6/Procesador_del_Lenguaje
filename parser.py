import ply.yacc as yacc
from lexer import Lexer


class Parser:
    def __init__(self):
        self.lexer = Lexer()
        self.has_errors = False
        # write_tables=False  → no genera parser.out ni parser.tab.py en disco
        # errorlog=NullLogger → suprime cualquier warning de PLY en consola
        self.parser = yacc.yacc(
            module=self,
            write_tables=False,
            debug=False,
            errorlog=yacc.NullLogger(),
        )

    tokens = Lexer.tokens
    start = 'program'

    # De menor a mayor precedencia
    precedence = (
        ('nonassoc', 'IFX'),
        ('nonassoc', 'ELSE'),
        ('left', 'OR'),
        ('left', 'AND'),
        ('nonassoc', 'EQ', 'GT', 'GE', 'LT', 'LE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('right', 'NOT'),
        ('right', 'UMINUS', 'UPLUS'),
    )

    # =========================
    # Programa
    # =========================

    def p_program(self, p):
        'program : top_list_opt'
        p[0] = ('program', p[1] if p[1] is not None else [])

    def p_top_list_opt(self, p):
        '''top_list_opt : top_list
                        | empty'''
        p[0] = p[1]

    def p_top_list_single(self, p):
        'top_list : top_item'
        p[0] = [p[1]]

    def p_top_list_rec(self, p):
        'top_list : top_list top_item'
        p[0] = p[1] + [p[2]]

    def p_top_item(self, p):
        '''top_item : SEMICOLON
                    | simple_statement SEMICOLON
                    | compound_statement
                    | function_decl
                    | record_decl SEMICOLON'''
        if len(p) == 2:
            if p.slice[1].type == 'SEMICOLON':
                p[0] = ('empty_stmt',)
            else:
                p[0] = p[1]
        else:
            p[0] = p[1]

    # =========================
    # Bloques
    # =========================

    def p_block(self, p):
        'block : LBRACE block_items_opt RBRACE'
        p[0] = ('block', p[2] if p[2] is not None else [])

    def p_block_items_opt(self, p):
        '''block_items_opt : block_items
                           | empty'''
        p[0] = p[1]

    def p_block_items_single(self, p):
        'block_items : block_item'
        p[0] = [p[1]]

    def p_block_items_rec(self, p):
        'block_items : block_items block_item'
        p[0] = p[1] + [p[2]]

    def p_block_item(self, p):
        '''block_item : SEMICOLON
                      | simple_statement SEMICOLON
                      | compound_statement'''
        if len(p) == 2:
            if p.slice[1].type == 'SEMICOLON':
                p[0] = ('empty_stmt',)
            else:
                p[0] = p[1]
        else:
            p[0] = p[1]

    # =========================
    # Sentencias
    # =========================

    def p_simple_statement(self, p):
        '''simple_statement : declaration
                            | assignment
                            | print_stmt
                            | break_stmt
                            | return_stmt
                            | expression'''
        p[0] = p[1]

    def p_compound_statement(self, p):
        '''compound_statement : if_stmt
                              | while_stmt
                              | do_while_stmt'''
        p[0] = p[1]

    # =========================
    # Declaraciones y asignaciones
    # =========================

    def p_declaration(self, p):
        'declaration : type_spec ID decl_tail'
        # decl_tail puede ser:
        # None                        -> declaración simple
        # ('init', expr)              -> declaración con inicialización
        # ('multi', [id2, id3, ...])  -> multideclaración
        tail = p[3]

        if tail is None:
            p[0] = ('decl', p[1], [p[2]])
        elif tail[0] == 'init':
            p[0] = ('decl_init', p[1], p[2], tail[1])
        else:
            p[0] = ('decl', p[1], [p[2]] + tail[1])

    def p_decl_tail(self, p):
        '''decl_tail : empty
                     | ASSIGN expression
                     | COMMA id_list_tail'''
        if len(p) == 2:
            p[0] = None
        elif p.slice[1].type == 'ASSIGN':
            p[0] = ('init', p[2])
        else:
            p[0] = ('multi', p[2])

    def p_id_list_tail_single(self, p):
        'id_list_tail : ID'
        p[0] = [p[1]]

    def p_id_list_tail_rec(self, p):
        'id_list_tail : ID COMMA id_list_tail'
        p[0] = [p[1]] + p[3]

    def p_assignment(self, p):
        'assignment : lvalue ASSIGN expression'
        p[0] = ('assign', p[1], p[3])

    def p_lvalue_id(self, p):
        'lvalue : ID'
        p[0] = ('var', p[1])

    def p_lvalue_field(self, p):
        'lvalue : lvalue DOT ID'
        p[0] = ('field_access', p[1], p[3])

    # =========================
    # Print / break / return
    # =========================

    def p_print_stmt(self, p):
        'print_stmt : PRINT LPAREN expression RPAREN'
        p[0] = ('print', p[3])

    def p_break_stmt(self, p):
        'break_stmt : BREAK'
        p[0] = ('break',)

    def p_return_stmt_expr(self, p):
    # return con valor — usado en funciones con tipo de retorno concreto
        'return_stmt : RETURN expression'
        p[0] = ('return', p[2])

def p_return_stmt_void(self, p):
    # return vacío — solo válido en funciones void (se comprobará en P3)
    'return_stmt : RETURN'
    p[0] = ('return', None)

    # =========================
    # Control de flujo
    # =========================

    def p_if_stmt(self, p):
        '''if_stmt : IF LPAREN expression RPAREN block %prec IFX
                   | IF LPAREN expression RPAREN block ELSE block'''
        if len(p) == 6:
            p[0] = ('if', p[3], p[5], None)
        else:
            p[0] = ('if', p[3], p[5], p[7])

    def p_while_stmt(self, p):
        'while_stmt : WHILE LPAREN expression RPAREN block'
        p[0] = ('while', p[3], p[5])

    def p_do_while_stmt(self, p):
        'do_while_stmt : DO block WHILE LPAREN expression RPAREN'
        p[0] = ('do_while', p[2], p[5])

    # =========================
    # Funciones y records
    # =========================

    def p_function_decl_typed(self, p):
    # Función con tipo de retorno concreto (int, float, char, boolean, o registro)
    # Se separa de void para eliminar el conflicto reduce/reduce:
    # con return_type unificado, el parser no podía distinguir entre
    # "int f(...)" (función) y "int a" (declaración de variable) con un
    # solo token de lookahead.
        'function_decl : type_spec ID LPAREN param_list_opt RPAREN block'
        p[0] = ('func_decl', p[1], p[2], p[4], p[6])

    def p_function_decl_void(self, p):
    # Función void: VOID no pertenece a type_spec, por lo que no hay
    # ambigüedad y puede seguir siendo una regla independiente.
        'function_decl : VOID ID LPAREN param_list_opt RPAREN block'
        p[0] = ('func_decl', 'void', p[2], p[4], p[6])


    def p_param_list_opt(self, p):
        '''param_list_opt : param_list
                          | empty'''
        p[0] = p[1] if p[1] is not None else []

    def p_param_list_single(self, p):
        'param_list : param'
        p[0] = [p[1]]

    def p_param_list_rec(self, p):
        'param_list : param_list COMMA param'
        p[0] = p[1] + [p[3]]

    def p_param(self, p):
        'param : type_spec ID'
        p[0] = (p[1], p[2])

    def p_record_decl(self, p):
        'record_decl : RECORD ID LPAREN field_list_opt RPAREN'
        p[0] = ('record_decl', p[2], p[4])

    def p_field_list_opt(self, p):
        '''field_list_opt : field_list
                          | empty'''
        p[0] = p[1] if p[1] is not None else []

    def p_field_list_single(self, p):
        'field_list : field'
        p[0] = [p[1]]

    def p_field_list_rec(self, p):
        'field_list : field_list COMMA field'
        p[0] = p[1] + [p[3]]

    def p_field(self, p):
        'field : type_spec ID'
        p[0] = (p[1], p[2])

    # =========================
    # Tipos
    # =========================

    def p_type_spec_basic(self, p):
        '''type_spec : INT
                     | FLOAT
                     | CHAR
                     | BOOLEAN'''
        p[0] = p[1]

    def p_type_spec_record(self, p):
        'type_spec : ID'
        # Los tipos de registro definidos por el usuario salen del lexer como ID
        p[0] = ('type_id', p[1])

    # =========================
    # Expresiones
    # =========================

    def p_expression_binary(self, p):
        '''expression : expression PLUS expression
                      | expression MINUS expression
                      | expression TIMES expression
                      | expression DIVIDE expression
                      | expression AND expression
                      | expression OR expression
                      | expression GT expression
                      | expression GE expression
                      | expression LT expression
                      | expression LE expression
                      | expression EQ expression'''
        p[0] = ('binop', p[2], p[1], p[3])

    def p_expression_unary(self, p):
        '''expression : MINUS expression %prec UMINUS
                      | PLUS expression %prec UPLUS
                      | NOT expression'''
        p[0] = ('unop', p[1], p[2])

    def p_expression_postfix(self, p):
        'expression : postfix_expression'
        p[0] = p[1]

    def p_postfix_expression_primary(self, p):
        'postfix_expression : primary_expression'
        p[0] = p[1]

    def p_postfix_expression_field(self, p):
        'postfix_expression : postfix_expression DOT ID'
        p[0] = ('field_access', p[1], p[3])

    def p_postfix_expression_call(self, p):
        'postfix_expression : postfix_expression LPAREN argument_list_opt RPAREN'
        p[0] = ('call', p[1], p[3])

    def p_primary_literal(self, p):
        'primary_expression : literal'
        p[0] = p[1]

    def p_primary_id(self, p):
        'primary_expression : ID'
        p[0] = ('var', p[1])

    def p_primary_new(self, p):
        'primary_expression : NEW ID LPAREN argument_list_opt RPAREN'
        p[0] = ('new', p[2], p[4])

    def p_primary_group(self, p):
        'primary_expression : LPAREN expression RPAREN'
        p[0] = p[2]

    def p_argument_list_opt(self, p):
        '''argument_list_opt : argument_list
                             | empty'''
        p[0] = p[1] if p[1] is not None else []

    def p_argument_list_single(self, p):
        'argument_list : expression'
        p[0] = [p[1]]

    def p_argument_list_rec(self, p):
        'argument_list : argument_list COMMA expression'
        p[0] = p[1] + [p[3]]

    def p_literal(self, p):
        '''literal : INT_VALUE
                   | FLOAT_VALUE
                   | CHAR_VALUE
                   | TRUE
                   | FALSE'''
        p[0] = ('const', p[1])

    # =========================
    # Vacío
    # =========================

    def p_empty(self, p):
        'empty :'
        p[0] = None

    # =========================
    # Errores
    # =========================

    def p_error(self, p):
        self.has_errors = True

        if p is None:
            print("[ERROR] Fin de fichero inesperado")
            return

        col = getattr(p, 'col_start', '?')
        print(f"[ERROR] Token '{p.type}' inesperado en la línea {p.lineno}, columna {col}")

    # =========================
    # API pública
    # =========================

    def parse(self, input_text):
        self.has_errors = False
        self.lexer.input(input_text)

        return self.parser.parse(
            input=input_text,
            lexer=self.lexer.lexer,      # lexer interno de PLY, sí tiene lineno
            tokenfunc=self.lexer.token,  # seguimos usando tu token() para columnas
            tracking=True
        )
