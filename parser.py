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

        # Normalizamos el tipo:
        # 'int' se queda como 'int'
        # ('type_id', 'Point') pasa a ser 'Point'
        typ_name = self._type_name(typ)

        # Comprobamos que el tipo exista:
        # - básico: int, float, char, boolean
        # - record previamente declarado: Point, Line, etc.
        if not self._type_exists(typ):
            self._semantic_error(
                f"El tipo '{typ_name}' de la variable '{name}' no existe"
            )
            p[0] = ('decl', typ_name, [name])
            return

        if tail is None:
            # Ejemplo:
            # int x;
            # Point p;
            if name in self.symbols:
                self._semantic_error(
                    f"La variable '{name}' ya ha sido declarada previamente"
                )
            else:
                self.symbols[name] = (typ_name, self._default_value(typ_name))

            p[0] = ('decl', typ_name, [name])

        elif tail[0] == 'init':
            # Ejemplo:
            # int x = 5;
            # Point p = new Point(1, 2);
            expr     = tail[1]   # (tipo, valor)
            expr_typ = expr[0]
            expr_typ_name = self._type_name(expr_typ)

            if name in self.symbols:
                self._semantic_error(
                    f"La variable '{name}' ya ha sido declarada previamente"
                )

            elif not self._compatible(typ_name, expr_typ_name):
                self._semantic_error(
                    f"No se puede inicializar '{name}' (tipo '{typ_name}') "
                    f"con una expresión de tipo '{expr_typ_name}'"
                )
                self.symbols[name] = (typ_name, self._default_value(typ_name))

            else:
                self.symbols[name] = (typ_name, self._cast_value_to_type(expr[1], typ_name))

            p[0] = ('decl_init', typ_name, name, expr)

        else:
            # Ejemplo:
            # int a, b;
            # Point p1, p2;
            ids = [name] + tail[1]

            for n in ids:
                if n in self.symbols:
                    self._semantic_error(
                        f"La variable '{n}' ya ha sido declarada previamente"
                    )
                else:
                    self.symbols[n] = (typ_name, self._default_value(typ_name))

            p[0] = ('decl', typ_name, ids)

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
                self._set_lvalue_value(lval, self._cast_value_to_type(expr[1], lval_typ))

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
        expr = p[2]

        if self.current_function is None:
            self._semantic_error(
                f"'return' solo puede usarse dentro de una función (línea {p.lineno(1)})"
            )
            p[0] = ('return', expr)
            return

        self.current_function['return_stmt_seen'] = True

        function_name = self.current_function['name']
        return_type = self.current_function['return_type']
        expr_type = self._type_name(expr[0])

        if return_type == 'void':
            self._semantic_error(
                f"La función void '{function_name}' no puede devolver un valor "
                f"(línea {p.lineno(1)})"
            )
        elif not self._compatible(return_type, expr_type):
            self._semantic_error(
                f"La función '{function_name}' debe devolver '{return_type}', "
                f"pero devuelve '{expr_type}' (línea {p.lineno(1)})"
            )
        else:
            self.current_function['return_seen'] = True

        p[0] = ('return', expr)

    def p_return_stmt_void(self, p):
        'return_stmt : RETURN'

        if self.current_function is None:
            self._semantic_error(
                f"'return' solo puede usarse dentro de una función (línea {p.lineno(1)})"
            )
            p[0] = ('return', None)
            return

        self.current_function['return_stmt_seen'] = True
        function_name = self.current_function['name']
        return_type = self.current_function['return_type']

        if return_type == 'void':
            self._semantic_error(
                f"La función void '{function_name}' no puede incluir return "
                f"(línea {p.lineno(1)})"
            )
        else:
            self._semantic_error(
                f"La función '{function_name}' debe devolver un valor de tipo "
                f"'{return_type}' (línea {p.lineno(1)})"
            )

        p[0] = ('return', None)

    # ==================================================================
    # Control de flujo
    # ==================================================================

    def p_if_stmt(self, p):
        '''if_stmt : IF LPAREN expression RPAREN block
                   | IF LPAREN expression RPAREN block ELSE block'''
        self.has_control_or_functions = True
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
        self.has_control_or_functions = True
        cond = p[3]   # (tipo, valor)

        if cond[0] != 'boolean':
            self._semantic_error(
                f"La condición del 'while' debe ser 'boolean', "
                f"se encontró '{cond[0]}' (línea {p.lineno(1)})"
            )

        p[0] = ('while', cond, p[6])

    def p_do_while_stmt(self, p):
        'do_while_stmt : DO enter_loop block exit_loop WHILE LPAREN expression RPAREN SEMICOLON'
        self.has_control_or_functions = True
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

    def p_function_decl(self, p):
        'function_decl : function_header block'
        self.has_control_or_functions = True
        header = p[1]
        block = p[2]

        # Al terminar de analizar el bloque, todavía estamos dentro de la función.
        # Por eso aquí podemos comprobar si se ha visto un return.
        if header['valid'] and header['return_type'] != 'void':
            if (
                self.current_function is not None
                and not self.current_function['return_seen']
                and not self.current_function['return_stmt_seen']
            ):
                self._semantic_error(
                    f"La función '{header['name']}' debe devolver un valor de tipo "
                    f"'{header['return_type']}'"
                )

        # Restauramos los símbolos globales.
        self._exit_function_scope()

        # Registramos la función después de analizarla.
        if header['valid']:
            self.functions.setdefault(header['name'], []).append({
                'params': header['params'],
                'return': header['return_type']
            })

        p[0] = (
            'func_decl',
            header['return_type'],
            header['name'],
            header['params'],
            block
        )

    def p_function_header_typed(self, p):
        'function_header : type_spec ID LPAREN param_list_opt RPAREN'
        return_type = self._type_name(p[1])
        name = p[2]
        params = p[4]

        header = self._build_function_header(return_type, name, params)
        self._enter_function_scope(header)
        p[0] = header

    def p_function_header_void(self, p):
        'function_header : VOID ID LPAREN param_list_opt RPAREN'
        return_type = 'void'
        name = p[2]
        params = p[4]

        header = self._build_function_header(return_type, name, params)
        self._enter_function_scope(header)
        p[0] = header

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
        record_name = p[2]
        fields = p[4]

        if record_name in self.records:
            self._semantic_error(
                f"El record '{record_name}' ya ha sido declarado previamente"
            )
            p[0] = ('record_decl', record_name, fields)
            return

        field_names = set()
        processed_fields = []
        valid = True

        for field_type, field_name in fields:
            field_type_name = self._type_name(field_type)

            if field_name in field_names:
                self._semantic_error(
                    f"El campo '{field_name}' está repetido en el record '{record_name}'"
                )
                valid = False
            else:
                field_names.add(field_name)

            if not self._type_exists(field_type):
                self._semantic_error(
                    f"El tipo '{field_type_name}' del campo '{field_name}' "
                    f"no existe en el record '{record_name}'"
                )
                valid = False

            processed_fields.append((field_type_name, field_name))

        if valid:
            self.records[record_name] = processed_fields

        p[0] = ('record_decl', record_name, processed_fields)

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
            common_type = self._widen(left[0], right[0])
            val = self._eval_binop(op, left[1], right[1], common_type, t_res)
            p[0] = (t_res, val)

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
        val  = self._get_lvalue_value(lval)
        p[0] = (t, val)

    def p_postfix_expression_call(self, p):
        'postfix_expression : ID LPAREN argument_list_opt RPAREN'
        function_name = p[1]
        args = p[3]

        return_type = self._resolve_function_call(function_name, args, p.lineno(1))

        if return_type is None:
            p[0] = (None, None)
        else:
            p[0] = (return_type, None)

    def p_primary_new(self, p):
        'primary_expression : NEW ID LPAREN argument_list_opt RPAREN'
        record_name = p[2]
        args = p[4]

        if record_name not in self.records:
            self._semantic_error(
                f"El record '{record_name}' no ha sido declarado previamente"
            )
            p[0] = (record_name, None)
            return

        fields = self.records[record_name]

        if len(args) != len(fields):
            self._semantic_error(
                f"El constructor de '{record_name}' espera {len(fields)} argumento(s), "
                f"pero recibió {len(args)}"
            )
            p[0] = (record_name, self._default_value(record_name))
            return

        value = {}

        for i, ((field_type, field_name), arg) in enumerate(zip(fields, args), start=1):
            arg_type = arg[0]
            arg_value = arg[1]
            arg_type_name = self._type_name(arg_type)

            if not self._compatible(field_type, arg_type_name):
                self._semantic_error(
                    f"El argumento {i} de '{record_name}' para el campo '{field_name}' "
                    f"debe ser de tipo '{field_type}', pero se recibió '{arg_type_name}'"
                )
                value[field_name] = self._default_value(field_type)
            else:
                value[field_name] = arg_value

        p[0] = (record_name, value)

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
        self.records = {}
        self.functions = {}
        self.loop_depth = 0
        self.function_scope_stack = []
        self.current_function = None
        self.has_control_or_functions = False

        self.lexer.input(input_text)
        result = self.parser.parse(
            input=input_text,
            lexer=self.lexer.lexer,
            tokenfunc=self.lexer.token,
            tracking=True
        )

        if self.lexer.has_errors:
            self.has_errors = True

        return result

    # ==================================================================
    # Escritura de archivos de salida
    # ==================================================================

    def write_records_file(self, input_path):
        output_path = input_path.rsplit('.', 1)[0] + ".records"

        with open(output_path, "w", encoding="utf-8") as out:
            for record_name, fields in self.records.items():
                fields_text = ",".join(
                    f"{field_name}:{field_type}"
                    for field_type, field_name in fields
                )
                out.write(f"{record_name}:[{fields_text}]\n")

    def _format_symbol_value(self, value):
        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, dict):
            fields_text = ",".join(
                f"{field}:{self._format_symbol_value(field_value)}"
                for field, field_value in value.items()
            )
            return "{" + fields_text + "}"

        return str(value)

    def write_symbols_file(self, input_path):
        output_path = input_path.rsplit('.', 1)[0] + ".symbols"

        with open(output_path, "w", encoding="utf-8") as out:
            for name, (typ, value) in self.symbols.items():
                if self.has_control_or_functions:
                    out.write(f"{name}:{typ}\n")
                else:
                    value_text = self._format_symbol_value(value)
                    out.write(f"{name}:{typ},{value_text}\n")

    def write_functions_file(self, input_path):
        output_path = input_path.rsplit('.', 1)[0] + ".functions"

        with open(output_path, "w", encoding="utf-8") as out:
            for function_name, overloads in self.functions.items():
                for function in overloads:
                    params_text = ",".join(
                        f"{param_name}:{param_type}"
                        for param_type, param_name in function["params"]
                    )

                    return_type = function["return"]

                    out.write(
                        f"{function_name}:[{params_text}],{return_type}\n"
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

    def _type_name(self, typ):
        """Convierte un tipo interno a string.

        Básicos:
            'int' -> 'int'

        Records:
            ('type_id', 'Point') -> 'Point'
        """
        if isinstance(typ, tuple) and typ[0] == 'type_id':
            return typ[1]
        return typ


    def _type_exists(self, typ):
        """True si el tipo existe como básico o como record."""
        name = self._type_name(typ)
        return name in self.default_types or name in self.records

    def _default_value(self, typ):
        """Valor por defecto para tipos básicos y records."""
        name = self._type_name(typ)

        if name in self.default_types:
            return self.default_types[name]

        if name in self.records:
            value = {}
            for field_type, field_name in self.records[name]:
                value[field_name] = self._default_value(field_type)
            return value

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

    def _value_as_type(self, value, target_type):
        """Convierte un valor al tipo común usado para operar."""
        if value is None:
            return None

        target_type = self._type_name(target_type)

        if target_type == 'char':
            return value

        if target_type == 'int':
            if isinstance(value, str):
                return ord(value)
            return int(value)

        if target_type == 'float':
            if isinstance(value, str):
                return float(ord(value))
            return float(value)

        if target_type == 'boolean':
            return bool(value)

        return value


    def _eval_binop(self, op, left_value, right_value, common_type, result_type):
        """Evalúa una operación binaria si ambos operandos tienen valor."""
        if left_value is None or right_value is None or common_type is None:
            return None

        a = self._value_as_type(left_value, common_type)
        b = self._value_as_type(right_value, common_type)

        try:
            if op == '+':
                result = a + b
            elif op == '-':
                result = a - b
            elif op == '*':
                result = a * b
            elif op == '/':
                if b == 0:
                    return None
                if common_type == 'int':
                    result = a // b
                else:
                    result = a / b
            elif op == '>':
                return a > b
            elif op == '>=':
                return a >= b
            elif op == '<':
                return a < b
            elif op == '<=':
                return a <= b
            elif op == '==':
                return a == b
            elif op == '&&':
                return a and b
            elif op == '||':
                return a or b
            else:
                return None

            if result_type == 'char':
                if isinstance(result, str):
                    return result
                if isinstance(result, int) and 0 <= result <= 255:
                    return chr(result)
                return None

            return result

        except Exception:
            return None

    def _lvalue_type(self, lval):
        """Devuelve el tipo de un lvalue.

        Ejemplos:
            a       -> tipo de la variable a
            p.x     -> tipo del campo x dentro del record de p
            l.a.x   -> tipo del campo x dentro del campo a de l
        """
        if lval[0] == 'var':
            name = lval[1]

            if name not in self.symbols:
                self._semantic_error(
                    f"La variable '{name}' no ha sido declarada previamente"
                )
                return None

            return self.symbols[name][0]

        elif lval[0] == 'field_access':
            base_lval = lval[1]
            field_name = lval[2]

            base_type = self._lvalue_type(base_lval)

            if base_type is None:
                return None

            base_type_name = self._type_name(base_type)

            if base_type_name not in self.records:
                self._semantic_error(
                    f"No se puede acceder al campo '{field_name}' "
                    f"porque '{base_type_name}' no es un record"
                )
                return None

            for field_type, current_field_name in self.records[base_type_name]:
                if current_field_name == field_name:
                    return field_type

            self._semantic_error(
                f"El record '{base_type_name}' no tiene un campo llamado '{field_name}'"
            )
            return None

        return None

    def _get_lvalue_value(self, lval):
        """Devuelve el valor actual de un lvalue.

        Ejemplos:
            a       -> valor de a
            p.x     -> valor del campo x de p
            l.a.x   -> valor del campo x dentro del campo a de l
        """
        if lval[0] == 'var':
            name = lval[1]
            if name in self.symbols:
                return self.symbols[name][1]
            return None

        if lval[0] == 'field_access':
            base_lval = lval[1]
            field_name = lval[2]

            base_value = self._get_lvalue_value(base_lval)

            if isinstance(base_value, dict):
                return base_value.get(field_name)

            return None

        return None

    def _set_lvalue_value(self, lval, new_value):
        """Actualiza el valor de un lvalue.

        Ejemplos:
            a = 3       -> cambia el valor de a
            p.x = 10    -> cambia el campo x dentro de p
            l.a.x = 10  -> cambia el campo x dentro del campo a de l
        """
        if lval[0] == 'var':
            name = lval[1]
            if name in self.symbols:
                typ = self.symbols[name][0]
                self.symbols[name] = (typ, new_value)
            return

        if lval[0] == 'field_access':
            base_lval = lval[1]
            field_name = lval[2]

            base_value = self._get_lvalue_value(base_lval)

            if isinstance(base_value, dict) and field_name in base_value:
                base_value[field_name] = new_value

            return

    def _build_function_header(self, return_type, name, params):
        """Valida y prepara la cabecera de una función."""
        valid = True
        processed_params = []
        param_names = set()

        if return_type != 'void' and not self._type_exists(return_type):
            self._semantic_error(
                f"El tipo de retorno '{return_type}' de la función '{name}' no existe"
            )
            valid = False

        for param_type, param_name in params:
            param_type_name = self._type_name(param_type)

            if param_name in param_names:
                self._semantic_error(
                    f"El parámetro '{param_name}' está repetido en la función '{name}'"
                )
                valid = False
            else:
                param_names.add(param_name)

            if not self._type_exists(param_type):
                self._semantic_error(
                    f"El tipo '{param_type_name}' del parámetro '{param_name}' "
                    f"no existe en la función '{name}'"
                )
                valid = False

            processed_params.append((param_type_name, param_name))

        param_types = [param_type for param_type, _ in processed_params]

        if self._function_signature_exists(name, param_types):
            self._semantic_error(
                f"La función '{name}' con parámetros {param_types} "
                f"ya ha sido declarada previamente"
            )
            valid = False

        return {
            'name': name,
            'return_type': return_type,
            'params': processed_params,
            'valid': valid
        }

    def _function_signature_exists(self, name, param_types):
        """True si ya existe una función con mismo nombre y mismos tipos de parámetros."""
        for function in self.functions.get(name, []):
            existing_param_types = [param_type for param_type, _ in function['params']]
            if existing_param_types == param_types:
                return True
        return False

    def _enter_function_scope(self, header):
        """Crea un ámbito local para analizar el cuerpo de una función."""
        self.function_scope_stack.append((self.symbols.copy(), self.current_function))

        self.current_function = {
            'name': header['name'],
            'return_type': header['return_type'],
            'return_seen': False,
            'return_stmt_seen': False
        }

        for param_type, param_name in header['params']:
            if param_name not in self.symbols:
                self.symbols[param_name] = (param_type, self._default_value(param_type))

    def _exit_function_scope(self):
        """Restaura los símbolos que había antes de entrar en la función."""
        if self.function_scope_stack:
            self.symbols, self.current_function = self.function_scope_stack.pop()

    def _resolve_function_call(self, name, args, line):
        """Devuelve el tipo de retorno de una llamada a función, o None si es inválida."""
        if self.current_function is not None and self.current_function['name'] == name:
            self._semantic_error(
                f"No se permite recursión directa en la función '{name}' (línea {line})"
            )
            return None

        if name not in self.functions:
            self._semantic_error(
                f"La función '{name}' no ha sido declarada previamente (línea {line})"
            )
            return None

        arg_types = [self._type_name(arg[0]) for arg in args]
        candidates = self.functions[name]

        # 1. Buscar coincidencia exacta de tipos.
        exact_matches = []

        for function in candidates:
            param_types = [param_type for param_type, _ in function['params']]

            if param_types == arg_types:
                exact_matches.append(function)

        if len(exact_matches) == 1:
            return exact_matches[0]['return']

        # 2. Si no hay coincidencia exacta, buscar coincidencias compatibles con conversiones.
        compatible_matches = []

        for function in candidates:
            param_types = [param_type for param_type, _ in function['params']]

            if len(param_types) != len(arg_types):
                continue

            compatible = True

            for param_type, arg_type in zip(param_types, arg_types):
                if not self._compatible(param_type, arg_type):
                    compatible = False
                    break

            if compatible:
                compatible_matches.append(function)

        if len(compatible_matches) == 1:
            return compatible_matches[0]['return']

        if len(compatible_matches) > 1:
            self._semantic_error(
                f"La llamada a la función '{name}' con argumentos {arg_types} "
                f"es ambigua (línea {line})"
            )
            return None

        self._semantic_error(
            f"No existe ninguna función '{name}' compatible con argumentos "
            f"{arg_types} (línea {line})"
        )
        return None

    def _cast_value_to_type(self, value, target_type):
        """Convierte un valor al tipo destino para guardarlo en symbols."""
        if value is None:
            return None

        target_type = self._type_name(target_type)

        if target_type == 'int':
            if isinstance(value, str):
                return ord(value)
            return int(value)

        if target_type == 'float':
            if isinstance(value, str):
                return float(ord(value))
            return float(value)

        if target_type == 'char':
            return value

        if target_type == 'boolean':
            return value

        return value
