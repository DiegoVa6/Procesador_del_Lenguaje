import ply.yacc as yacc
from lexer import Lexer


class Parser:

    # ------------------------------------------------------------------
    # Atributos de clase
    # ------------------------------------------------------------------

    symbols = {}

    default_types = {
        'int':     0,
        'float':   0.0,
        'char':    '',
        'boolean': False,
    }

    widening_order = ['char', 'int', 'float']

    op_types = {
        '+':  {'int': 'int',     'float': 'float',   'char': 'char'},
        '-':  {'int': 'int',     'float': 'float',   'char': 'char'},
        '*':  {'int': 'int',     'float': 'float'},
        '/':  {'int': 'int',     'float': 'float'},
        '>':  {'int': 'boolean', 'float': 'boolean', 'char': 'boolean'},
        '>=': {'int': 'boolean', 'float': 'boolean', 'char': 'boolean'},
        '<':  {'int': 'boolean', 'float': 'boolean', 'char': 'boolean'},
        '<=': {'int': 'boolean', 'float': 'boolean', 'char': 'boolean'},
        '==': {'int': 'boolean', 'float': 'boolean', 'char': 'boolean', 'boolean': 'boolean'},
        '&&': {'boolean': 'boolean'},
        '||': {'boolean': 'boolean'},
    }

    tokens = Lexer.tokens
    start = 'program'

    precedence = (
        ('left', 'OR'),
        ('left', 'AND'),
        ('nonassoc', 'EQ', 'GT', 'GE', 'LT', 'LE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('right', 'NOT'),
        ('right', 'UMINUS', 'UPLUS'),
    )

    # ------------------------------------------------------------------
    # Constructor mínimo
    # ------------------------------------------------------------------

    def __init__(self):
        self.lexer = Lexer()
        self.parser = yacc.yacc(module=self)

    # ==================================================================
    # Programa
    # ==================================================================

    def p_program(self, p):
        'program : top_list_opt'
        p[0] = ('program', p[1] if p[1] is not None else [])

    def p_top_list_opt(self, p):
        '''top_list_opt : top_list
                        | lambda'''
        p[0] = p[1]

    def p_top_list_single(self, p):
        'top_list : top_item'
        p[0] = [p[1]]

    def p_top_list_rec(self, p):
        'top_list : top_list top_item'
        if p[2] is not None:
            p[1].append(p[2])
        p[0] = p[1]

    def p_top_item(self, p):
        '''top_item : SEMICOLON
                    | simple_statement SEMICOLON
                    | compound_statement
                    | function_decl
                    | record_decl SEMICOLON'''
        if len(p) == 2:
            p[0] = ('empty_stmt',) if p.slice[1].type == 'SEMICOLON' else p[1]
        else:
            p[0] = p[1]

    # ==================================================================
    # Bloques
    # ==================================================================

    def p_block(self, p):
        'block : LBRACE block_items_opt RBRACE'
        p[0] = ('block', p[2] if p[2] is not None else [])

    def p_block_items_opt(self, p):
        '''block_items_opt : block_items
                           | lambda'''
        p[0] = p[1]

    def p_block_items_single(self, p):
        'block_items : block_item'
        p[0] = [p[1]]

    def p_block_items_rec(self, p):
        'block_items : block_items block_item'
        if p[2] is not None:
            p[1].append(p[2])
        p[0] = p[1]

    def p_block_item(self, p):
        '''block_item : SEMICOLON
                      | simple_statement SEMICOLON
                      | compound_statement'''
        if len(p) == 2:
            p[0] = ('empty_stmt',) if p.slice[1].type == 'SEMICOLON' else p[1]
        else:
            p[0] = p[1]

    # ==================================================================
    # Sentencias
    # ==================================================================

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

    # ==================================================================
    # Declaración
    # ==================================================================

    def p_declaration(self, p):
        'declaration : type_spec ID decl_tail'
        typ  = p[1]
        name = p[2]
        tail = p[3]

        if tail is None:
            # int x;
            if name in self.symbols:
                self._semantic_error(f"La variable '{name}' ya ha sido declarada previamente")
            else:
                self.symbols[name] = (typ, self.default_types.get(typ))
            p[0] = ('decl', typ, [name])

        elif tail[0] == 'init':
            # int x = 5;
            expr     = tail[1]   # (tipo, valor)
            expr_typ = expr[0]

            if name in self.symbols:
                self._semantic_error(f"La variable '{name}' ya ha sido declarada previamente")
            elif not self._compatible(typ, expr_typ):
                self._semantic_error(
                    f"No se puede inicializar '{name}' (tipo '{typ}') "
                    f"con una expresión de tipo '{expr_typ}'"
                )
                self.symbols[name] = (typ, self.default_types.get(typ))
            else:
                self.symbols[name] = (typ, expr[1])
            p[0] = ('decl_init', typ, name, expr)

        else:
            # int a, b;
            ids = [name] + tail[1]
            for n in ids:
                if n in self.symbols:
                    self._semantic_error(f"La variable '{n}' ya ha sido declarada previamente")
                else:
                    self.symbols[n] = (typ, self.default_types.get(typ))
            p[0] = ('decl', typ, ids)

    def p_decl_tail(self, p):
        '''decl_tail : lambda
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

    # ==================================================================
    # Asignación
    # ==================================================================

    def p_assignment(self, p):
        'assignment : lvalue ASSIGN expression'
        lval     = p[1]
        expr     = p[3]   # (tipo, valor)
        lval_typ = self._lvalue_type(lval)
        expr_typ = expr[0]

        if lval_typ is not None and expr_typ is not None:
            if not self._compatible(lval_typ, expr_typ):
                self._semantic_error(
                    f"No se puede asignar '{expr_typ}' a variable de tipo '{lval_typ}'"
                )
            else:
                if lval[0] == 'var' and lval[1] in self.symbols:
                    self.symbols[lval[1]] = (lval_typ, expr[1])

        p[0] = ('assign', lval, expr)

    def p_lvalue_id(self, p):
        'lvalue : ID'
        p[0] = ('var', p[1])

    def p_lvalue_field(self, p):
        'lvalue : lvalue DOT ID'
        p[0] = ('field_access', p[1], p[3])

    # ==================================================================
    # Print / break / return
    # ==================================================================

    def p_print_stmt(self, p):
        'print_stmt : PRINT LPAREN expression RPAREN'
        p[0] = ('print', p[3])

    def p_break_stmt(self, p):
        'break_stmt : BREAK'
        if self.loop_depth == 0:
            self._semantic_error(
                f"'break' solo puede usarse dentro de un bucle (línea {p.lineno(1)})"
            )
        p[0] = ('break',)

    def p_return_stmt_expr(self, p):
        'return_stmt : RETURN expression'
        p[0] = ('return', p[2])

    def p_return_stmt_void(self, p):
        'return_stmt : RETURN'
        p[0] = ('return', None)

    # ==================================================================
    # Control de flujo
    # ==================================================================

    def p_if_stmt(self, p):
        '''if_stmt : IF LPAREN expression RPAREN block
                   | IF LPAREN expression RPAREN block ELSE block'''
        cond = p[3]   # (tipo, valor)

        if cond[0] != 'boolean':
            self._semantic_error(
                f"La condición del 'if' debe ser 'boolean', "
                f"se encontró '{cond[0]}' (línea {p.lineno(1)})"
            )

        if len(p) == 6:
            p[0] = ('if', cond, p[5], None)
        else:
            p[0] = ('if', cond, p[5], p[7])

    def p_enter_loop(self, p):
        'enter_loop :'
        self.loop_depth += 1

    def p_exit_loop(self, p):
        'exit_loop :'
        self.loop_depth -= 1

    def p_while_stmt(self, p):
        'while_stmt : WHILE LPAREN expression RPAREN enter_loop block exit_loop'
        cond = p[3]   # (tipo, valor)

        if cond[0] != 'boolean':
            self._semantic_error(
                f"La condición del 'while' debe ser 'boolean', "
                f"se encontró '{cond[0]}' (línea {p.lineno(1)})"
            )

        p[0] = ('while', cond, p[6])

    def p_do_while_stmt(self, p):
        'do_while_stmt : DO enter_loop block exit_loop WHILE LPAREN expression RPAREN SEMICOLON'
        cond = p[7]   # (tipo, valor)

        if cond[0] != 'boolean':
            self._semantic_error(
                f"La condición del 'do-while' debe ser 'boolean', "
                f"se encontró '{cond[0]}' (línea {p.lineno(5)})"
            )

        p[0] = ('do_while', p[3], cond)

    # ==================================================================
    # Funciones y records  (semántica completa en P3-parte2)
    # ==================================================================

    def p_function_decl_typed(self, p):
        'function_decl : type_spec ID LPAREN param_list_opt RPAREN block'
        p[0] = ('func_decl', p[1], p[2], p[4], p[6])

    def p_function_decl_void(self, p):
        'function_decl : VOID ID LPAREN param_list_opt RPAREN block'
        p[0] = ('func_decl', 'void', p[2], p[4], p[6])

    def p_param_list_opt(self, p):
        '''param_list_opt : param_list
                          | lambda'''
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
                          | lambda'''
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

    # ==================================================================
    # Tipos
    # ==================================================================

    def p_type_spec_basic(self, p):
        '''type_spec : INT
                     | FLOAT
                     | CHAR
                     | BOOLEAN'''
        p[0] = p[1]

    def p_type_spec_record(self, p):
        'type_spec : ID'
        p[0] = ('type_id', p[1])

    # ==================================================================
    # Expresiones — devuelven (tipo, valor)
    # ==================================================================

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
        left  = p[1]   # (tipo, valor)
        op    = p[2]
        right = p[3]   # (tipo, valor)

        t_res = self._check_binop(op, left[0], right[0])

        if t_res is None:
            self._semantic_error(
                f"Operación '{op}' no válida entre "
                f"'{left[0]}' y '{right[0]}' (línea {p.lineno(2)})"
            )
            p[0] = (None, None)
        else:
            p[0] = (t_res, None)

    def p_expression_unary(self, p):
        '''expression : MINUS expression %prec UMINUS
                      | PLUS expression %prec UPLUS
                      | NOT expression'''
        op   = p[1]
        expr = p[2]   # (tipo, valor)

        t_res = self._check_unop(op, expr[0])

        if t_res is None:
            self._semantic_error(
                f"Operador '{op}' no válido sobre "
                f"'{expr[0]}' (línea {p.lineno(1)})"
            )
            p[0] = (None, None)
        else:
            val = None
            if expr[1] is not None:
                if op == '-':   val = -expr[1]
                elif op == '+': val = expr[1]
                elif op == '!': val = not expr[1]
            p[0] = (t_res, val)

    def p_expression_postfix(self, p):
        'expression : postfix_expression'
        p[0] = p[1]

    # ------------------------------------------------------------------
    # Cadena lvalue -> postfix -> expression
    # Se mantiene de P2 para resolver el conflicto reduce/reduce con ID
    # ------------------------------------------------------------------

    def p_postfix_from_primary(self, p):
        'postfix_expression : primary_expression'
        p[0] = p[1]

    def p_postfix_from_lvalue(self, p):
        'postfix_expression : lvalue'
        lval = p[1]
        t    = self._lvalue_type(lval)
        val  = self.symbols[lval[1]][1] if lval[0] == 'var' and lval[1] in self.symbols else None
        p[0] = (t, val)

    def p_postfix_expression_call(self, p):
        'postfix_expression : ID LPAREN argument_list_opt RPAREN'
        # Semántica de llamadas a función: P3-parte2
        p[0] = (None, None)

    def p_primary_new(self, p):
        'primary_expression : NEW ID LPAREN argument_list_opt RPAREN'
        # Semántica de registros: P3-parte2
        p[0] = (('type_id', p[2]), None)

    def p_primary_group(self, p):
        'primary_expression : LPAREN expression RPAREN'
        p[0] = p[2]

    def p_argument_list_opt(self, p):
        '''argument_list_opt : argument_list
                             | lambda'''
        p[0] = p[1] if p[1] is not None else []

    def p_argument_list_single(self, p):
        'argument_list : expression'
        p[0] = [p[1]]

    def p_argument_list_rec(self, p):
        'argument_list : argument_list COMMA expression'
        p[0] = p[1] + [p[3]]

    # ------------------------------------------------------------------
    # Literales — directos a expression, una función por tipo (estilo profesor)
    # ------------------------------------------------------------------

    def p_literal_int_expression(self, p):
        'expression : INT_VALUE'
        p[0] = ('int', p[1])

    def p_literal_float_expression(self, p):
        'expression : FLOAT_VALUE'
        p[0] = ('float', p[1])

    def p_literal_char_expression(self, p):
        'expression : CHAR_VALUE'
        p[0] = ('char', p[1])

    def p_literal_bool_expression(self, p):
        '''expression : TRUE
                      | FALSE'''
        p[0] = ('boolean', p[1])

    # ==================================================================
    # Vacío
    # ==================================================================

    def p_lambda(self, p):
        'lambda :'
        p[0] = None

    # ==================================================================
    # Error sintáctico
    # ==================================================================

    def p_error(self, p):
        self.has_errors = True
        if p is None:
            print("[ERROR SINTÁCTICO] Fin de fichero inesperado")
            return
        col = getattr(p, 'col_start', '?')
        print(f"[ERROR SINTÁCTICO] Token '{p.type}' inesperado "
              f"en línea {p.lineno}, columna {col}")

    # ==================================================================
    # API pública
    # ==================================================================

    def parse(self, input_text):
        self.has_errors = False
        self.symbols = {}
        self.loop_depth = 0
        self.lexer.input(input_text)
        return self.parser.parse(
            input=input_text,
            lexer=self.lexer.lexer,
            tokenfunc=self.lexer.token,
            tracking=True
        )

    # ==================================================================
    # Métodos privados de ayuda semántica
    # ==================================================================

    def _semantic_error(self, msg):
        self.has_errors = True
        print(f"[ERROR SEMÁNTICO] {msg}")

    def _compatible(self, dest, src):
        """True si src puede asignarse a dest (igual o widening permitido)."""
        if dest == src:
            return True
        if dest in self.widening_order and src in self.widening_order:
            return self.widening_order.index(src) <= self.widening_order.index(dest)
        return False

    def _widen(self, t1, t2):
        """Tipo más general entre t1 y t2, o None si incompatibles."""
        if t1 == t2:
            return t1
        if t1 in self.widening_order and t2 in self.widening_order:
            return self.widening_order[max(self.widening_order.index(t1),
                                          self.widening_order.index(t2))]
        return None

    def _check_binop(self, op, t1, t2):
        """Tipo resultado de op sobre t1 y t2 con widening. None si inválido."""
        w = self._widen(t1, t2)
        if w is not None and w in self.op_types.get(op, {}):
            return self.op_types[op][w]
        return None

    def _check_unop(self, op, t):
        """Tipo resultado del operador unario op sobre tipo t. None si inválido."""
        if op in ('+', '-') and t in ('int', 'float', 'char'):
            return t
        if op == '!' and t == 'boolean':
            return 'boolean'
        return None

    def _lvalue_type(self, lval):
        """Tipo de un lvalue desde self.symbols. field_access: P3-parte2."""
        if lval[0] == 'var':
            name = lval[1]
            if name not in self.symbols:
                self._semantic_error(
                    f"La variable '{name}' no ha sido declarada previamente"
                )
                return None
            return self.symbols[name][0]
        elif lval[0] == 'field_access':
            return None   # se completará con la tabla de registros
        return None
    