import ply.yacc as yacc
from lexer import Lexer


class Parser:
    tokens = Lexer.tokens

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

    start = 'program'

    def __init__(self):
        self.lexer = Lexer()
        self.has_errors = False
        self.parser = yacc.yacc(module=self, start=self.start)

    def parse(self, data: str):
        self.has_errors = False
        self.lexer.input(data)
        return self.parser.parse(input=data, lexer=self.lexer, tracking=True)

    # -------------------------
    # Programa
    # -------------------------

    def p_program(self, p):
        'program : top_items_opt'
        p[0] = None

    def p_top_items_opt(self, p):
        '''top_items_opt : top_items
                         | empty'''
        p[0] = None

    def p_top_items(self, p):
        '''top_items : top_items top_item
                     | top_item'''
        p[0] = None

    def p_top_item(self, p):
        '''top_item : SEMICOLON
                    | simple_statement SEMICOLON
                    | compound_statement
                    | function_decl
                    | record_decl SEMICOLON'''
        p[0] = None

    # -------------------------
    # Bloques
    # -------------------------

    def p_block(self, p):
        'block : LBRACE block_items_opt RBRACE'
        p[0] = None

    def p_block_items_opt(self, p):
        '''block_items_opt : block_items
                           | empty'''
        p[0] = None

    def p_block_items(self, p):
        '''block_items : block_items block_item
                       | block_item'''
        p[0] = None

    def p_block_item(self, p):
        '''block_item : SEMICOLON
                      | simple_statement SEMICOLON
                      | compound_statement'''
        p[0] = None

    # -------------------------
    # Sentencias
    # -------------------------

    def p_simple_statement(self, p):
        '''simple_statement : declaration
                            | assignment
                            | print_stmt
                            | break_stmt
                            | return_stmt
                            | expression'''
        p[0] = None

    def p_compound_statement(self, p):
        '''compound_statement : if_stmt
                              | while_stmt
                              | do_while_stmt'''
        p[0] = None

    # -------------------------
    # Declaraciones
    # -------------------------

    def p_declaration(self, p):
        'declaration : type_spec ID decl_rest'
        p[0] = None

    def p_decl_rest(self, p):
        '''decl_rest : empty
                     | ASSIGN expression
                     | COMMA id_list_tail'''
        p[0] = None

    def p_id_list_tail(self, p):
        '''id_list_tail : ID
                        | ID COMMA id_list_tail'''
        p[0] = None

    def p_assignment(self, p):
        'assignment : lvalue ASSIGN expression'
        p[0] = None

    def p_lvalue(self, p):
        '''lvalue : ID
                  | lvalue DOT ID'''
        p[0] = None

    # -------------------------
    # Print / break / return
    # -------------------------

    def p_print_stmt(self, p):
        'print_stmt : PRINT LPAREN expression RPAREN'
        p[0] = None

    def p_break_stmt(self, p):
        'break_stmt : BREAK'
        p[0] = None

    def p_return_stmt(self, p):
        'return_stmt : RETURN expression'
        p[0] = None

    # -------------------------
    # Control de flujo
    # -------------------------

    def p_if_stmt(self, p):
        '''if_stmt : IF LPAREN expression RPAREN block %prec IFX
                   | IF LPAREN expression RPAREN block ELSE block'''
        p[0] = None

    def p_while_stmt(self, p):
        'while_stmt : WHILE LPAREN expression RPAREN block'
        p[0] = None

    def p_do_while_stmt(self, p):
        'do_while_stmt : DO block WHILE LPAREN expression RPAREN'
        p[0] = None

    # -------------------------
    # Funciones y records
    # -------------------------

    def p_function_decl(self, p):
        'function_decl : return_type ID LPAREN param_list_opt RPAREN block'
        p[0] = None

    def p_return_type(self, p):
        '''return_type : type_spec
                       | VOID'''
        p[0] = None

    def p_param_list_opt(self, p):
        '''param_list_opt : param_list
                          | empty'''
        p[0] = None

    def p_param_list(self, p):
        '''param_list : param
                      | param COMMA param_list'''
        p[0] = None

    def p_param(self, p):
        'param : type_spec ID'
        p[0] = None

    def p_record_decl(self, p):
        'record_decl : RECORD ID LPAREN field_list_opt RPAREN'
        p[0] = None

    def p_field_list_opt(self, p):
        '''field_list_opt : field_list
                          | empty'''
        p[0] = None

    def p_field_list(self, p):
        '''field_list : field_decl
                      | field_decl COMMA field_list'''
        p[0] = None

    def p_field_decl(self, p):
        'field_decl : type_spec ID'
        p[0] = None

    # -------------------------
    # Tipos
    # -------------------------

    def p_type_spec(self, p):
        '''type_spec : INT
                     | FLOAT
                     | CHAR
                     | BOOLEAN
                     | ID'''
        p[0] = None

    # -------------------------
    # Expresiones
    # -------------------------

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
        p[0] = None

    def p_expression_unary(self, p):
        '''expression : MINUS expression %prec UMINUS
                      | PLUS expression %prec UPLUS
                      | NOT expression'''
        p[0] = None

    def p_expression_postfix(self, p):
        'expression : postfix_expression'
        p[0] = None

    def p_postfix_expression(self, p):
        '''postfix_expression : atom
                              | postfix_expression DOT ID
                              | postfix_expression LPAREN argument_list_opt RPAREN'''
        p[0] = None

    def p_atom(self, p):
        '''atom : literal
                | ID
                | NEW ID LPAREN argument_list_opt RPAREN
                | LPAREN expression RPAREN'''
        p[0] = None

    def p_argument_list_opt(self, p):
        '''argument_list_opt : argument_list
                             | empty'''
        p[0] = None

    def p_argument_list(self, p):
        '''argument_list : expression
                         | expression COMMA argument_list'''
        p[0] = None

    def p_literal(self, p):
        '''literal : INT_VALUE
                   | FLOAT_VALUE
                   | CHAR_VALUE
                   | TRUE
                   | FALSE'''
        p[0] = None

    # -------------------------
    # Vacío
    # -------------------------

    def p_empty(self, p):
        'empty :'
        pass

    # -------------------------
    # Errores
    # -------------------------

    def p_error(self, p):
        self.has_errors = True

        if p is None:
            print("[ERROR] Fin de fichero inesperado")
            return

        col = getattr(p, 'col_start', '?')
        print(f"[ERROR] Token '{p.type}' inesperado en la línea {p.lineno}, columna {col}")