#!/usr/bin/env python3
import sys
import re

class Token:
    def __init__(self, type, value, line=0):
        self.type = type
        self.value = value
        self.line = line
    
    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.line = 1
        self.tokens = []
        
    def tokenize(self):
        keywords = {'int', 'if', 'else', 'while', 'for', 'return', 'void'}
        
        while self.pos < len(self.code):
            if self.code[self.pos].isspace():
                if self.code[self.pos] == '\n':
                    self.line += 1
                self.pos += 1
                continue
            
            # skip comments
            if self.pos + 1 < len(self.code) and self.code[self.pos:self.pos+2] == '//':
                while self.pos < len(self.code) and self.code[self.pos] != '\n':
                    self.pos += 1
                continue
            
            # numbers
            if self.code[self.pos].isdigit():
                num = ''
                while self.pos < len(self.code) and self.code[self.pos].isdigit():
                    num += self.code[self.pos]
                    self.pos += 1
                self.tokens.append(Token('NUMBER', int(num), self.line))
                continue
            
            # identifiers
            if self.code[self.pos].isalpha() or self.code[self.pos] == '_':
                ident = ''
                while self.pos < len(self.code) and (self.code[self.pos].isalnum() or self.code[self.pos] == '_'):
                    ident += self.code[self.pos]
                    self.pos += 1
                
                if ident in keywords:
                    self.tokens.append(Token('KEYWORD', ident, self.line))
                else:
                    self.tokens.append(Token('IDENT', ident, self.line))
                continue
            
            # strings
            if self.code[self.pos] == '"':
                self.pos += 1
                string = ''
                while self.pos < len(self.code) and self.code[self.pos] != '"':
                    if self.code[self.pos] == '\\' and self.pos + 1 < len(self.code):
                        self.pos += 1
                        if self.code[self.pos] == 'n':
                            string += '\n'
                        else:
                            string += self.code[self.pos]
                    else:
                        string += self.code[self.pos]
                    self.pos += 1
                self.pos += 1
                self.tokens.append(Token('STRING', string, self.line))
                continue
            
            # two char operators
            if self.pos + 1 < len(self.code):
                two_char = self.code[self.pos:self.pos+2]
                if two_char in ['==', '!=', '<=', '>=', '++', '--']:
                    self.tokens.append(Token('OP', two_char, self.line))
                    self.pos += 2
                    continue
            
            # single char
            char = self.code[self.pos]
            if char in '+-*/%=<>!':
                self.tokens.append(Token('OP', char, self.line))
            elif char in '();{},':
                self.tokens.append(Token('PUNCT', char, self.line))
            
            self.pos += 1
        
        return self.tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None
    
    def consume(self, expected_type=None, expected_value=None):
        if self.pos >= len(self.tokens):
            raise Exception("Unexpected end of input")
        
        token = self.tokens[self.pos]
        if expected_type and token.type != expected_type:
            raise Exception(f"Expected {expected_type}, got {token.type}")
        if expected_value and token.value != expected_value:
            raise Exception(f"Expected '{expected_value}', got '{token.value}'")
        
        self.pos += 1
        return token
    
    def parse(self):
        functions = []
        while self.pos < len(self.tokens):
            functions.append(self.parse_function())
        return {'type': 'Program', 'functions': functions}
    
    def parse_function(self):
        return_type = self.consume('KEYWORD')
        name = self.consume('IDENT')
        self.consume('PUNCT', '(')
        
        # skip params
        while self.peek() and not (self.peek().type == 'PUNCT' and self.peek().value == ')'):
            self.consume()
        
        self.consume('PUNCT', ')')
        self.consume('PUNCT', '{')
        
        body = []
        while not (self.peek() and self.peek().type == 'PUNCT' and self.peek().value == '}'):
            body.append(self.parse_statement())
        
        self.consume('PUNCT', '}')
        
        return {
            'type': 'Function',
            'return_type': return_type.value,
            'name': name.value,
            'body': body
        }
    
    def parse_statement(self):
        token = self.peek()
        
        if token.type == 'KEYWORD':
            if token.value == 'int':
                return self.parse_declaration()
            elif token.value == 'if':
                return self.parse_if()
            elif token.value == 'while':
                return self.parse_while()
            elif token.value == 'for':
                return self.parse_for()
            elif token.value == 'return':
                return self.parse_return()
        
        stmt = self.parse_expression_statement()
        return stmt
    
    def parse_declaration(self):
        self.consume('KEYWORD', 'int')
        name = self.consume('IDENT')
        
        init = None
        if self.peek() and self.peek().type == 'OP' and self.peek().value == '=':
            self.consume('OP', '=')
            init = self.parse_expression()
        
        self.consume('PUNCT', ';')
        return {'type': 'Declaration', 'name': name.value, 'init': init}
    
    def parse_if(self):
        self.consume('KEYWORD', 'if')
        self.consume('PUNCT', '(')
        condition = self.parse_expression()
        self.consume('PUNCT', ')')
        
        then_body = []
        if self.peek() and self.peek().type == 'PUNCT' and self.peek().value == '{':
            self.consume('PUNCT', '{')
            while not (self.peek() and self.peek().type == 'PUNCT' and self.peek().value == '}'):
                then_body.append(self.parse_statement())
            self.consume('PUNCT', '}')
        else:
            then_body.append(self.parse_statement())
        
        else_body = None
        if self.peek() and self.peek().type == 'KEYWORD' and self.peek().value == 'else':
            self.consume('KEYWORD', 'else')
            else_body = []
            if self.peek() and self.peek().type == 'PUNCT' and self.peek().value == '{':
                self.consume('PUNCT', '{')
                while not (self.peek() and self.peek().type == 'PUNCT' and self.peek().value == '}'):
                    else_body.append(self.parse_statement())
                self.consume('PUNCT', '}')
            else:
                else_body.append(self.parse_statement())
        
        return {'type': 'If', 'condition': condition, 'then': then_body, 'else': else_body}
    
    def parse_while(self):
        self.consume('KEYWORD', 'while')
        self.consume('PUNCT', '(')
        condition = self.parse_expression()
        self.consume('PUNCT', ')')
        
        body = []
        if self.peek() and self.peek().type == 'PUNCT' and self.peek().value == '{':
            self.consume('PUNCT', '{')
            while not (self.peek() and self.peek().type == 'PUNCT' and self.peek().value == '}'):
                body.append(self.parse_statement())
            self.consume('PUNCT', '}')
        else:
            body.append(self.parse_statement())
        
        return {'type': 'While', 'condition': condition, 'body': body}
    
    def parse_for(self):
        self.consume('KEYWORD', 'for')
        self.consume('PUNCT', '(')
        
        init = None
        if not (self.peek() and self.peek().type == 'PUNCT' and self.peek().value == ';'):
            if self.peek().type == 'KEYWORD' and self.peek().value == 'int':
                init = self.parse_declaration()
            else:
                init = self.parse_expression()
                self.consume('PUNCT', ';')
        else:
            self.consume('PUNCT', ';')
        
        condition = None
        if not (self.peek() and self.peek().type == 'PUNCT' and self.peek().value == ';'):
            condition = self.parse_expression()
        self.consume('PUNCT', ';')
        
        update = None
        if not (self.peek() and self.peek().type == 'PUNCT' and self.peek().value == ')'):
            update = self.parse_expression()
        self.consume('PUNCT', ')')
        
        body = []
        if self.peek() and self.peek().type == 'PUNCT' and self.peek().value == '{':
            self.consume('PUNCT', '{')
            while not (self.peek() and self.peek().type == 'PUNCT' and self.peek().value == '}'):
                body.append(self.parse_statement())
            self.consume('PUNCT', '}')
        else:
            body.append(self.parse_statement())
        
        return {'type': 'For', 'init': init, 'condition': condition, 'update': update, 'body': body}
    
    def parse_return(self):
        self.consume('KEYWORD', 'return')
        value = None
        if not (self.peek() and self.peek().type == 'PUNCT' and self.peek().value == ';'):
            value = self.parse_expression()
        self.consume('PUNCT', ';')
        return {'type': 'Return', 'value': value}
    
    def parse_expression_statement(self):
        expr = self.parse_expression()
        self.consume('PUNCT', ';')
        return {'type': 'ExprStmt', 'expr': expr}
    
    def parse_expression(self):
        expr = self.parse_comparison()
        
        if self.peek() and self.peek().type == 'OP' and self.peek().value == '=':
            self.consume('OP', '=')
            right = self.parse_expression()
            return {'type': 'Assign', 'left': expr, 'right': right}
        
        return expr
    
    def parse_comparison(self):
        left = self.parse_additive()
        
        while self.peek() and self.peek().type == 'OP' and self.peek().value in ['<', '>', '==', '!=', '<=', '>=']:
            op = self.consume('OP')
            right = self.parse_additive()
            left = {'type': 'BinOp', 'op': op.value, 'left': left, 'right': right}
        
        return left
    
    def parse_additive(self):
        left = self.parse_multiplicative()
        
        while self.peek() and self.peek().type == 'OP' and self.peek().value in ['+', '-']:
            op = self.consume('OP')
            right = self.parse_multiplicative()
            left = {'type': 'BinOp', 'op': op.value, 'left': left, 'right': right}
        
        return left
    
    def parse_multiplicative(self):
        left = self.parse_unary()
        
        while self.peek() and self.peek().type == 'OP' and self.peek().value in ['*', '/', '%']:
            op = self.consume('OP')
            right = self.parse_unary()
            left = {'type': 'BinOp', 'op': op.value, 'left': left, 'right': right}
        
        return left
    
    def parse_unary(self):
        if self.peek() and self.peek().type == 'OP' and self.peek().value in ['++', '--']:
            op = self.consume('OP')
            operand = self.parse_primary()
            return {'type': 'PreOp', 'op': op.value, 'operand': operand}
        
        expr = self.parse_primary()
        
        if self.peek() and self.peek().type == 'OP' and self.peek().value in ['++', '--']:
            op = self.consume('OP')
            return {'type': 'PostOp', 'op': op.value, 'operand': expr}
        
        return expr
    
    def parse_primary(self):
        token = self.peek()
        
        if token.type == 'NUMBER':
            self.consume()
            return {'type': 'Number', 'value': token.value}
        
        if token.type == 'STRING':
            self.consume()
            return {'type': 'String', 'value': token.value}
        
        if token.type == 'IDENT':
            name = self.consume()
            
            if self.peek() and self.peek().type == 'PUNCT' and self.peek().value == '(':
                self.consume('PUNCT', '(')
                args = []
                
                if not (self.peek() and self.peek().type == 'PUNCT' and self.peek().value == ')'):
                    args.append(self.parse_expression())
                    while self.peek() and self.peek().type == 'PUNCT' and self.peek().value == ',':
                        self.consume('PUNCT', ',')
                        args.append(self.parse_expression())
                
                self.consume('PUNCT', ')')
                return {'type': 'Call', 'name': name.value, 'args': args}
            
            return {'type': 'Var', 'name': name.value}
        
        if token.type == 'PUNCT' and token.value == '(':
            self.consume('PUNCT', '(')
            expr = self.parse_expression()
            self.consume('PUNCT', ')')
            return expr
        
        raise Exception(f"Unexpected token: {token}")

class CodeGen:
    def __init__(self):
        self.output = []
        self.data = []
        self.label_count = 0
        self.string_count = 0
        self.vars = {}
        self.stack_offset = 0
    
    def new_label(self, prefix="L"):
        label = f"{prefix}{self.label_count}"
        self.label_count += 1
        return label
    
    def add_string(self, s):
        label = f"str{self.string_count}"
        self.string_count += 1
        self.data.append(f'{label}: .asciiz "{s}"')
        return label
    
    def emit(self, code):
        self.output.append(code)
    
    def generate(self, ast):
        for func in ast['functions']:
            self.gen_function(func)
        
        result = [".data"]
        result.extend(self.data)
        result.append("")
        result.append(".text")
        result.append(".globl main")
        result.append("")
        result.extend(self.output)
        result.append("")
        result.append("print_int:")
        result.append("    li $v0, 1")
        result.append("    syscall")
        result.append("    jr $ra")
        result.append("")
        result.append("print_str:")
        result.append("    li $v0, 4")
        result.append("    syscall")
        result.append("    jr $ra")
        
        return "\n".join(result)
    
    def gen_function(self, func):
        self.emit(f"{func['name']}:")
        self.emit("    addi $sp, $sp, -8")
        self.emit("    sw $ra, 4($sp)")
        self.emit("    sw $fp, 0($sp)")
        self.emit("    move $fp, $sp")
        
        self.vars = {}
        self.stack_offset = 0
        
        for stmt in func['body']:
            self.gen_stmt(stmt)
        
        self.emit(f"{func['name']}_exit:")
        self.emit("    move $sp, $fp")
        self.emit("    lw $fp, 0($sp)")
        self.emit("    lw $ra, 4($sp)")
        self.emit("    addi $sp, $sp, 8")
        self.emit("    jr $ra")
        self.emit("")
    
    def gen_stmt(self, stmt):
        if stmt['type'] == 'Declaration':
            self.emit("    addi $sp, $sp, -4")
            self.stack_offset += 4
            self.vars[stmt['name']] = -self.stack_offset
            
            if stmt['init']:
                self.gen_expr(stmt['init'])
                self.emit(f"    sw $t0, {self.vars[stmt['name']]}($fp)")
        
        elif stmt['type'] == 'ExprStmt':
            self.gen_expr(stmt['expr'])
        
        elif stmt['type'] == 'If':
            else_lbl = self.new_label("else")
            end_lbl = self.new_label("endif")
            
            self.gen_expr(stmt['condition'])
            self.emit(f"    beq $t0, $zero, {else_lbl}")
            
            for s in stmt['then']:
                self.gen_stmt(s)
            
            self.emit(f"    j {end_lbl}")
            self.emit(f"{else_lbl}:")
            
            if stmt['else']:
                for s in stmt['else']:
                    self.gen_stmt(s)
            
            self.emit(f"{end_lbl}:")
        
        elif stmt['type'] == 'While':
            loop_lbl = self.new_label("while")
            end_lbl = self.new_label("endwhile")
            
            self.emit(f"{loop_lbl}:")
            self.gen_expr(stmt['condition'])
            self.emit(f"    beq $t0, $zero, {end_lbl}")
            
            for s in stmt['body']:
                self.gen_stmt(s)
            
            self.emit(f"    j {loop_lbl}")
            self.emit(f"{end_lbl}:")
        
        elif stmt['type'] == 'For':
            loop_lbl = self.new_label("for")
            end_lbl = self.new_label("endfor")
            
            if stmt['init']:
                if stmt['init']['type'] == 'Declaration':
                    self.gen_stmt(stmt['init'])
                else:
                    self.gen_expr(stmt['init'])
            
            self.emit(f"{loop_lbl}:")
            
            if stmt['condition']:
                self.gen_expr(stmt['condition'])
                self.emit(f"    beq $t0, $zero, {end_lbl}")
            
            for s in stmt['body']:
                self.gen_stmt(s)
            
            if stmt['update']:
                self.gen_expr(stmt['update'])
            
            self.emit(f"    j {loop_lbl}")
            self.emit(f"{end_lbl}:")
        
        elif stmt['type'] == 'Return':
            if stmt['value']:
                self.gen_expr(stmt['value'])
                self.emit("    move $v0, $t0")
            self.emit("    j main_exit")
    
    def gen_expr(self, expr):
        if expr['type'] == 'Number':
            self.emit(f"    li $t0, {expr['value']}")
        
        elif expr['type'] == 'String':
            label = self.add_string(expr['value'])
            self.emit(f"    la $t0, {label}")
        
        elif expr['type'] == 'Var':
            offset = self.vars[expr['name']]
            self.emit(f"    lw $t0, {offset}($fp)")
        
        elif expr['type'] == 'Assign':
            self.gen_expr(expr['right'])
            if expr['left']['type'] == 'Var':
                offset = self.vars[expr['left']['name']]
                self.emit(f"    sw $t0, {offset}($fp)")
        
        elif expr['type'] == 'BinOp':
            self.gen_expr(expr['left'])
            self.emit("    addi $sp, $sp, -4")
            self.emit("    sw $t0, 0($sp)")
            
            self.gen_expr(expr['right'])
            self.emit("    move $t1, $t0")
            
            self.emit("    lw $t0, 0($sp)")
            self.emit("    addi $sp, $sp, 4")
            
            op = expr['op']
            if op == '+':
                self.emit("    add $t0, $t0, $t1")
            elif op == '-':
                self.emit("    sub $t0, $t0, $t1")
            elif op == '*':
                self.emit("    mul $t0, $t0, $t1")
            elif op == '/':
                self.emit("    div $t0, $t1")
                self.emit("    mflo $t0")
            elif op == '%':
                self.emit("    div $t0, $t1")
                self.emit("    mfhi $t0")
            elif op == '<':
                self.emit("    slt $t0, $t0, $t1")
            elif op == '>':
                self.emit("    slt $t0, $t1, $t0")
            elif op == '==':
                self.emit("    sub $t0, $t0, $t1")
                self.emit("    slt $t2, $t0, $zero")
                self.emit("    slt $t3, $zero, $t0")
                self.emit("    or $t0, $t2, $t3")
                self.emit("    xori $t0, $t0, 1")
            elif op == '!=':
                self.emit("    sub $t0, $t0, $t1")
                self.emit("    sltu $t0, $zero, $t0")
                self.emit("    andi $t0, $t0, 1")
            elif op == '<=':
                self.emit("    slt $t0, $t1, $t0")
                self.emit("    xori $t0, $t0, 1")
            elif op == '>=':
                self.emit("    slt $t0, $t0, $t1")
                self.emit("    xori $t0, $t0, 1")
        
        elif expr['type'] == 'PreOp':
            var_name = expr['operand']['name']
            offset = self.vars[var_name]
            
            self.emit(f"    lw $t0, {offset}($fp)")
            if expr['op'] == '++':
                self.emit("    addi $t0, $t0, 1")
            else:
                self.emit("    addi $t0, $t0, -1")
            self.emit(f"    sw $t0, {offset}($fp)")
        
        elif expr['type'] == 'PostOp':
            var_name = expr['operand']['name']
            offset = self.vars[var_name]
            
            self.emit(f"    lw $t0, {offset}($fp)")
            self.emit("    move $t2, $t0")
            if expr['op'] == '++':
                self.emit("    addi $t0, $t0, 1")
            else:
                self.emit("    addi $t0, $t0, -1")
            self.emit(f"    sw $t0, {offset}($fp)")
            self.emit("    move $t0, $t2")
        
        elif expr['type'] == 'Call':
            if expr['name'] == 'print_int':
                self.gen_expr(expr['args'][0])
                self.emit("    move $a0, $t0")
                self.emit("    jal print_int")
            elif expr['name'] == 'print_str':
                self.gen_expr(expr['args'][0])
                self.emit("    move $a0, $t0")
                self.emit("    jal print_str")

def main():
    if len(sys.argv) < 2:
        print("Usage: toycc <input.c> [-o <output.asm>]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = "out.asm"
    
    if len(sys.argv) >= 4 and sys.argv[2] == '-o':
        output_file = sys.argv[3]
    
    with open(input_file, 'r') as f:
        code = f.read()
    
    try:
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens)
        ast = parser.parse()
        
        codegen = CodeGen()
        asm = codegen.generate(ast)
        
        with open(output_file, 'w') as f:
            f.write(asm)
        
        print(f"Compiled {input_file} -> {output_file}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()