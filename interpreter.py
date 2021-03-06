import argparse
import sys
from enum import Enum

_SHOULD_LOG_SCOPE = False  # see '--scope' command line option
_SHOULD_LOG_STACK = False  # see '--stack' command line option
_SHOULD_LOG_LEXER = False  # see '--lexer' command line option
_SHOULD_LOG_VISITOR = False # see '--visitor' command line option
_SHOULD_LOG_MIPS = False # see '--mips' command line option


class ErrorCode(Enum):
    UNEXPECTED_TOKEN = 'Unexpected token'
    ID_NOT_FOUND     = 'Identifier not found'
    DUPLICATE_ID     = 'Duplicate id found'


class Error(Exception):
    def __init__(self, error_code=None, token=None, message=None):
        self.error_code = error_code
        self.token = token
        self.message = f'{self.__class__.__name__}: {message}'


class LexerError(Error):
    pass


class ParserError(Error):
    pass


class SemanticError(Error):
    pass





###############################################################################
#                                                                             #
#  LEXER                                                                      #
#                                                                             #
###############################################################################


class TokenType(Enum):
    # single-character token types
    PLUS          = '+'
    MINUS         = '-'
    MUL           = '*'
    FLOAT_DIV     = '/'
    LPAREN        = '('
    RPAREN        = ')'
    SEMI          = ';'
    DOT           = '.'
    COLON         = ':'
    COMMA         = ','
    LESS          = '<'
    LESSEQUAL     = '<='
    NOTEQUAL      = '<>'
    GREATER       = '>'
    GREATEREQUAL  = '>='
    EQUAL         = '='
    LBRACK        = '['
    RBRACK        = ']'
    QUOTE        = '\''
    # block of reserved words
    PROGRAM       = 'PROGRAM'  #start --see _build_reserved_keywords function for details
    INTEGER       = 'INTEGER'
    REAL          = 'REAL'
    CHAR          = 'CHAR'
    INTEGER_DIV   = 'DIV'
    VAR           = 'VAR'
    PROCEDURE     = 'PROCEDURE'
    BEGIN         = 'BEGIN'
    AND           = 'AND'
    ARRAY         = 'ARRAY'
    MOD           = 'MOD'
    DO            = 'DO'
    ELSE          = 'ELSE'
    IF            = 'IF'
    NOT           = 'NOT'
    OF            = 'OF'
    OR            = 'OR'
    ORD           = 'ORD'
    READ          = 'READ'
    READLN        = 'READLN'
    THEN          = 'THEN'
    WHILE         = 'WHILE'
    WRITE         = 'WRITE'
    WRITELN       = 'WRITELN'
    END           = 'END'      #end
    # misc
    ID            = 'ID'
    INTEGER_CONST = 'INTEGER_CONST'
    REAL_CONST    = 'REAL_CONST'
    STRING_CONST  = 'STRING_CONST'
    CHAR_CONST    = 'CHAR_CONST'
    ASSIGN        = ':='
    EOF           = 'EOF'


class Token:
    def __init__(self, type, value, lineno=None, column=None):
        self.type = type
        self.value = value
        self.lineno = lineno
        self.column = column

    def __str__(self):
        return 'Token({type}, {value}, position={lineno}:{column})'.format(
            type=self.type,
            value=repr(self.value),
            lineno=self.lineno,
            column=self.column,
        )

    def __repr__(self):
        return self.__str__()


def _build_reserved_keywords():
    tt_list = list(TokenType)
    start_index = tt_list.index(TokenType.PROGRAM)
    end_index = tt_list.index(TokenType.END)
    reserved_keywords = {
        token_type.value: token_type
        for token_type in tt_list[start_index:end_index + 1]
    }
    return reserved_keywords


RESERVED_KEYWORDS = _build_reserved_keywords()


class Lexer:

    def __init__(self, text):
        self.quote_count = 0
        self.text = text
        # self.pos is index for self.text
        self.pos = 0
        self.current_char = self.text[self.pos]
        # token line number and column number
        self.lineno = 1
        self.column = 1


    def log(self, msg):
        if _SHOULD_LOG_LEXER:
            print(msg)


    def error(self):
        s = "Lexer error on '{lexeme}' line: {lineno} column: {column}".format(
            lexeme=self.current_char,
            lineno=self.lineno,
            column=self.column,
        )
        raise LexerError(message=s)

    def advance(self):
        """Advance the `pos` pointer and set the `current_char` variable."""
        if self.current_char == '\n':
            self.lineno += 1
            self.column = 0

        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # end of input
        else:
            self.current_char = self.text[self.pos]
            self.column += 1

    def look_at_next_char(self):
        look_at_next_char_pos = self.pos + 1
        if look_at_next_char_pos > len(self.text) - 1:
            return None
        else:
            return self.text[look_at_next_char_pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        while self.current_char != '}':
            self.advance()
        self.advance()  # for the closing curly brace

    def number(self):
        """Return a (multidigit) integer or float consumed from the input."""

        # Create a new token with current line and column number
        token = Token(type=None, value=None, lineno=self.lineno, column=self.column)

        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()

        if self.current_char == '.' and not self.look_at_next_char() == '.':
            result += self.current_char
            self.advance()

            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()

            token.type = TokenType.REAL_CONST
            token.value = float(result)
        else:
            token.type = TokenType.INTEGER_CONST
            token.value = int(result)
        self.log(f'Number : {token}')
        return token


    def string_builder(self):
        """Handles building strings"""
        # Create a new token with current line and column number
        token = Token(type=None, value=None, lineno=self.lineno, column=self.column)
        result = ''

        while self.current_char is not None and self.current_char != '\'':
            result += self.current_char
            self.advance()

        if self.current_char == '\'':
            self.advance()
            self.quote_count = 0
            token.type = TokenType.STRING_CONST
            token.value = result
            self.log(f'Token : {token}')
            return token

    def char_builder(self):
        """Handles building chars"""
        # Create a new token with current line and column number
        token = Token(type=None, value=None, lineno=self.lineno, column=self.column)
        char = ''

        char += self.current_char
        token.type = TokenType.CHAR_CONST
        token.value = char
        self.advance()

        return token



    def _id(self):
        """Handle identifiers and reserved keywords"""

        # Create a new token with current line and column number
        token = Token(type=None, value=None, lineno=self.lineno, column=self.column)

        value = ''

        # if self.current_char.i() and not (self.look_at_next_char().isalnum() or self.look_at_next_char().isalpha()):
        #     token.type = TokenType.CHAR_CONST
        #     token.value = value
        #     print(token)
        #     return token

        while self.current_char is not None and self.current_char.isalnum():
            value += self.current_char
            self.advance()

        token_type = RESERVED_KEYWORDS.get(value.upper())
        if token_type is None:
            token.type = TokenType.ID
            token.value = value
        else:
            # reserved keyword
            token.type = token_type
            token.value = value.upper()
        self.log(f'ID : {token}')
        return token

    def get_next_token(self):

        while self.current_char is not None:

            if self.current_char == ':' and self.look_at_next_char() == '=':
                token = Token(
                    type=TokenType.ASSIGN,
                    value=TokenType.ASSIGN.value,  # ':='
                    lineno=self.lineno,
                    column=self.column,
                )
                self.advance()
                self.advance()
                self.log(f'Token : {token}')
                return token

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if (self.current_char == '\''):
                self.advance()
                self.quote_count = 1
                return self.string_builder()


            if self.current_char == '{':
                self.advance()
                self.skip_comment()
                continue

            if self.current_char.isalpha():
                return self._id()

            if self.current_char.isdigit():
                return self.number()


            # for single-character token
            try:
                token_type = TokenType(self.current_char)
            except ValueError:
                # no enum member with value equal to self.current_char
                self.error()
            else:
                # create a token with a single-character lexeme as its value
                token = Token(
                    type=token_type,
                    value=token_type.value,  # e.g. ';', '.', etc
                    lineno=self.lineno,
                    column=self.column,
                )
                self.advance()
                self.log(f'Token : {token}')
                return token

        # EOF (end-of-file) token indicates that there is no more
        # input left for lexical analysis
        return Token(type=TokenType.EOF, value=None)




















###############################################################################
#                                                                             #
#  PARSER                                                                     #
#                                                                             #
###############################################################################
class AST:
    pass


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Str(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Relation(AST):
    def __init__(self, left, token, right):
        self.left = left
        self.token = token
        self.right = right


class IO(AST):
    def __init__(self, op, tk):
        self.value = tk.value
        self.token = self.op = op

class WRITE(AST):
    def __init__(self, op, tk):
        self.value = tk.value
        self.token = self.op = op

class READ(AST):
    def __init__(self, op, tk):
        self.value = tk
        self.token = self.op = op

class UnaryOp(AST):
    def __init__(self, op, expr):
        self.token = self.op = op
        self.expr = expr

class Array(AST):
    def __init__(self, start_len, end_len, type, members = []):
        self.start = start_len
        self.end = end_len
        self.value = type.value
        self.members = members

class Compound(AST):
    """Represents a 'BEGIN ... END' block"""
    def __init__(self):
        self.children = []


class Assign(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


# class Array_Assign(AST):
#     def __init__(self, left, op, array_place,right):
#         self.left = left
#         self.token = self.op = op
#         self.location = array_place
#         self.right = right


class Var(AST):
    """The Var node is constructed out of ID token."""
    def __init__(self, token):
        self.token = token
        self.value = token.value


class NoOp(AST):
    pass


class Program(AST):
    def __init__(self, name, block):
        self.name = name
        self.block = block


class Block(AST):
    def __init__(self, declarations, compound_statement):
        self.declarations = declarations
        self.compound_statement = compound_statement


class VarDecl(AST):
    def __init__(self, var_node, type_node):
        self.var_node = var_node
        self.type_node = type_node



class Type(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class Param(AST):
    def __init__(self, var_node, type_node):
        self.var_node = var_node
        self.type_node = type_node


class ProcedureDecl(AST):
    def __init__(self, proc_name, formal_params, block_node):
        self.proc_name = proc_name
        self.formal_params = formal_params  # a list of Param nodes
        self.block_node = block_node


class ProcedureCall(AST):
    def __init__(self, proc_name, actual_params, token):
        self.proc_name = proc_name
        self.actual_params = actual_params  # a list of AST nodes
        self.token = token
        # a reference to procedure declaration symbol
        self.proc_symbol = None

class IfStatement(AST):
    def __init__(self, token,expr, statement, else_statement=None):
        self.name = token
        self.expr = expr
        self.statement = statement
        self.elseStatement = else_statement

class WhileStatement(AST):
    def __init__(self, token, expr, statement):
        self.name = token
        self.expr = expr
        self.statement = statement



class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to the first token taken from the input
        self.current_token = self.get_next_token()

    def get_next_token(self):
        return self.lexer.get_next_token()

    def error(self, error_code, token):
        raise ParserError(
            error_code=error_code,
            token=token,
            message=f'{error_code.value} -> {token}',
        )

    def eat(self, token_type):
        # consume token if type match and move to the next token
        if self.current_token.type == token_type:
            self.current_token = self.get_next_token()
        else:
            self.error(
                error_code=ErrorCode.UNEXPECTED_TOKEN,
                token=self.current_token,
            )

    def program(self):
        """program : PROGRAM variable SEMI block DOT"""
        self.eat(TokenType.PROGRAM)
        var_node = self.variable()
        prog_name = var_node.value
        self.eat(TokenType.SEMI)
        block_node = self.block()
        program_node = Program(prog_name, block_node)
        self.eat(TokenType.DOT)
        return program_node

    def block(self):
        """block : declarations compound_statement"""
        declaration_nodes = self.declarations()
        compound_statement_node = self.compound_statement()
        node = Block(declaration_nodes, compound_statement_node)
        return node

    def declarations(self):
        """
        declarations : (VAR (variable_declaration SEMI)+)? procedure_declaration*
        """
        declarations = []

        if self.current_token.type == TokenType.VAR:
            self.eat(TokenType.VAR)
            while self.current_token.type == TokenType.ID:
                var_decl = self.variable_declaration()
                declarations.extend(var_decl)
                self.eat(TokenType.SEMI)

        while self.current_token.type == TokenType.PROCEDURE:
            proc_decl = self.procedure_declaration()
            declarations.append(proc_decl)

        return declarations

    def formal_parameters(self):
        """ formal_parameters : ID (COMMA ID)* COLON type_spec """
        param_nodes = []

        param_tokens = [self.current_token]
        self.eat(TokenType.ID)
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            param_tokens.append(self.current_token)
            self.eat(TokenType.ID)

        self.eat(TokenType.COLON)
        type_node = self.type_spec()
        #print(param_tokens)
        for param_token in param_tokens:
            param_node = Param(Var(param_token), type_node)
            param_nodes.append(param_node)

        return param_nodes


    def formal_parameter_list(self):
        """ formal_parameter_list : formal_parameters
                                  | formal_parameters SEMI formal_parameter_list
        """

        if not self.current_token.type == TokenType.ID:
            return []

        param_nodes = self.formal_parameters()

        while self.current_token.type == TokenType.SEMI:
            self.eat(TokenType.SEMI)
            param_nodes.extend(self.formal_parameters())

        return param_nodes

    def variable_declaration(self):
        """variable_declaration : ID (COMMA ID)* COLON type_spec"""
        var_nodes = [Var(self.current_token)]  # first ID
        self.eat(TokenType.ID)

        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            var_nodes.append(Var(self.current_token))
            self.eat(TokenType.ID)

        self.eat(TokenType.COLON)

        type_node = self.type_spec()
        var_declarations = [
            VarDecl(var_node, type_node)
            for var_node in var_nodes
        ]
        return var_declarations

    def procedure_declaration(self):
        """procedure_declaration :
             PROCEDURE ID (LPAREN formal_parameter_list RPAREN)? SEMI block SEMI
        """
        self.eat(TokenType.PROCEDURE)
        proc_name = self.current_token.value
        self.eat(TokenType.ID)
        formal_params = []

        if self.current_token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            formal_params = self.formal_parameter_list()
            self.eat(TokenType.RPAREN)

        self.eat(TokenType.SEMI)
        block_node = self.block()
        proc_decl = ProcedureDecl(proc_name, formal_params, block_node)
        self.eat(TokenType.SEMI)
        return proc_decl

    def type_spec(self):
        """type_spec : INTEGER
                     | REAL
                     | STRING_CONST
                     | CHAR
                     | ARRAY
        """
        token = self.current_token
        members = [] #TODO: grab members of array
        if self.current_token.type == TokenType.INTEGER:
            self.eat(TokenType.INTEGER)
        elif self.current_token.type == TokenType.REAL:
            self.eat(TokenType.REAL)
        elif self.current_token.type == TokenType.STRING_CONST:
            self.eat(TokenType.STRING_CONST)
        elif self.current_token.type == TokenType.CHAR:
            self.eat(TokenType.CHAR)
        elif self.current_token.type == TokenType.ARRAY:
            self.eat(TokenType.ARRAY)
            self.eat(TokenType.LBRACK)
            Start_len = self.current_token.value
            self.eat(TokenType.INTEGER_CONST)
            self.eat(TokenType.DOT)
            self.eat(TokenType.DOT)
            End_len = self.current_token.value
            self.eat(TokenType.INTEGER_CONST)
            self.eat(TokenType.RBRACK)
            self.eat(TokenType.OF)
            if self.current_token.type == TokenType.INTEGER:
                type = TokenType.INTEGER
                self.eat(TokenType.INTEGER)
            array = Array(Start_len, End_len, type, members)
            return array
        node = Type(token)
        return node

    def compound_statement(self):
        """
        compound_statement: BEGIN statement_list END
        """
        self.eat(TokenType.BEGIN)
        nodes = self.statement_list()
        self.eat(TokenType.END)

        root = Compound()
        for node in nodes:
            root.children.append(node)

        return root

    def statement_list(self):
        """
        statement_list : statement
                       | statement SEMI statement_list
        """
        node = self.statement()

        results = [node]

        while self.current_token.type == TokenType.SEMI:
            self.eat(TokenType.SEMI)
            results.append(self.statement())

        return results


    def get_write_parameter(self, io):
        #TODO: Change it so read and readln take in parameters
        if not self.current_token.type == TokenType.STRING_CONST:
            return []

        node = Str(self.current_token)
        self.eat(TokenType.STRING_CONST)

        while self.current_token.type == TokenType.SEMI:
            self.eat(TokenType.SEMI)
            param_nodes.extend(self.formal_parameters())

        return node

    def read_parameters(self):
        """ formal_parameters : ID (COMMA ID)* """
        param_nodes = []

        param_tokens = [self.current_token]
        self.eat(TokenType.ID)
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            param_tokens.append(self.current_token)
            self.eat(TokenType.ID)

        return param_tokens

    def get_read_parameter(self, io):
        if not self.current_token.type == TokenType.ID:
            return []

        param_nodes = self.read_parameters()
        while self.current_token.type == TokenType.SEMI:
            self.eat(TokenType.SEMI)
            param_nodes.extend(self.formal_parameters())

        return param_nodes


    def io_statement(self):
        """ IO Statement --> read '(' Param ')'
                          | readln  '(' Param ')'
                          | write '(' 'String' ')'
                          | writeln  '(' 'String' ')'
        """
        if self.current_token.type == TokenType.READ:
            read_tk = TokenType.READ
            self.eat(TokenType.READ)
            self.eat(TokenType.LPAREN)
            formal_params = self.get_read_parameter(read_tk)
            node = READ(read_tk, formal_params)
            self.eat(TokenType.RPAREN)
        elif self.current_token.type == TokenType.READLN:
            readln_tk = TokenType.READLN
            self.eat(TokenType.READLN)
            self.eat(TokenType.LPAREN)
            formal_params = self.get_read_parameter(readln_tk)
            node = READ(readln_tk, formal_params)
            self.eat(TokenType.RPAREN)
        elif self.current_token.type == TokenType.WRITE:
            write_tk = TokenType.WRITE
            self.eat(TokenType.WRITE)
            self.eat(TokenType.LPAREN)
            formal_params = self.get_write_parameter(write_tk)
            node = WRITE(write_tk, formal_params)
            self.eat(TokenType.RPAREN)
        elif self.current_token.type == TokenType.WRITELN:
            writeln_tk = TokenType.WRITELN
            self.eat(TokenType.WRITELN)
            self.eat(TokenType.LPAREN)
            formal_params = self.get_write_parameter(writeln_tk)
            node = WRITE(writeln_tk, formal_params)
            self.eat(TokenType.RPAREN)
        else:
            raise Exception('no match in io_statement')

        return node



    def statement(self):
        #TODO: add if, if/else, while statements
        """
        statement : compound_statement
                  | proccall_statement
                  | assignment_statement
                  | io_statement
                  | IF, IF/ELSE, WHILE
                  | empty
        """
        if self.current_token.type == TokenType.BEGIN:
            node = self.compound_statement()
        elif (self.current_token.type == TokenType.ID and
              self.lexer.current_char == '('
        ):
            node = self.proccall_statement()
        elif self.current_token.type == TokenType.ID:
            node = self.assignment_statement()

        elif self.current_token.type == TokenType.WRITELN or self.current_token.type == TokenType.WRITE or self.current_token.type == TokenType.READ or self.current_token.type == TokenType.READLN:
            node = self.io_statement()
        elif self.current_token.type == TokenType.IF:
            node = self.if_statement()
        elif self.current_token.type == TokenType.WHILE:
            node = self.while_statement()
        else:
            node = self.empty()
        return node

    def while_statement(self):
        """WHILE statement: while expr do Statement"""
        token = self.current_token.type
        self.eat(TokenType.WHILE)
        expr = self.relation_statement()
        self.eat(TokenType.DO)
        statement = self.statement()
        node = WhileStatement(token, expr, statement)
        return node



    def if_statement(self):
        """IF/ELSE statement: If expr THEN Statement [ELSE Statement]"""
        token = self.current_token.type
        self.eat(TokenType.IF)
        expr = self.relation_statement()
        self.eat(TokenType.THEN)
        statement = self.statement()
        if self.current_token.type == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            else_statement = self.statement()
            node = IfStatement(token ,expr, statement, else_statement)
            return node
        node = IfStatement(token, expr, statement, )
        return node

    def proccall_statement(self):
        """proccall_statement : ID LPAREN (expr (COMMA expr)*)? RPAREN"""
        token = self.current_token

        proc_name = self.current_token.value
        self.eat(TokenType.ID)
        self.eat(TokenType.LPAREN)
        actual_params = []
        if self.current_token.type != TokenType.RPAREN:
            node = self.expr()
            actual_params.append(node)

        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            node = self.expr()
            actual_params.append(node)

        self.eat(TokenType.RPAREN)

        node = ProcedureCall(
            proc_name=proc_name,
            actual_params=actual_params,
            token=token,
        )
        return node

    def assignment_statement(self):
        """
        assignment_statement : variable ASSIGN expr
        """
        left = self.variable()
        token = self.current_token
        # for array assign
        if token.value == '[':
            self.eat(TokenType.LBRACK)
            Array_Place = self.current_token
            self.eat(TokenType.INTEGER_CONST)
            self.eat(TokenType.RBRACK)
            self.eat(TokenType.ASSIGN)
            right = self.expr()
            node = Assign(left, token, right)
            return node
        self.eat(TokenType.ASSIGN)
        right = self.expr()
        node = Assign(left, token, right)
        return node

    def relation_statement(self):
        """
        assignment_statement : variable relation expr
        = , > , < , >= , <=, AND, OR
        """
        left = self.expr()
        token = self.current_token

        if self.current_token.type == TokenType.EQUAL:
            self.eat(TokenType.EQUAL)
        elif self.current_token.type == TokenType.LESS:
            self.eat(TokenType.LESS)
        elif self.current_token.type == TokenType.GREATER:
            self.eat(TokenType.GREATER)
        elif self.current_token.type == TokenType.LESSEQUAL:
            self.eat(TokenType.LESSEQUAL)
        elif self.current_token.type == TokenType.GREATEREQUAL:
            self.eat(TokenType.GREATEREQUAL)
        elif self.current_token.type == TokenType.AND:
            self.eat(TokenType.AND)
        elif self.current_token.type == TokenType.OR:
            self.eat(TokenType.OR)
        else:
            raise Exception('no match in relation_statement')

        right = self.expr()
        node = Relation(left, token, right)
        return node

    def variable(self):
        """
        variable : ID
        """
        node = Var(self.current_token)
        self.eat(TokenType.ID)
        return node

    def empty(self):
        """An empty production"""
        return NoOp()

    def expr(self):
        """
        expr : term ((PLUS | MINUS) term)*
        """
        #TODO: add boolean expr
        node = self.term()
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            if token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
            elif token.type == TokenType.MINUS:
                self.eat(TokenType.MINUS)

            node = BinOp(left=node, op=token, right=self.term())

        return node

    def term(self):
        """term : factor ((MUL | INTEGER_DIV | FLOAT_DIV) factor)*"""
        node = self.factor()
        while self.current_token.type in (
                TokenType.MUL,
                TokenType.INTEGER_DIV,
                TokenType.FLOAT_DIV,
        ):
            token = self.current_token
            if token.type == TokenType.MUL:
                self.eat(TokenType.MUL)
            elif token.type == TokenType.INTEGER_DIV:
                self.eat(TokenType.INTEGER_DIV)
            elif token.type == TokenType.FLOAT_DIV:
                self.eat(TokenType.FLOAT_DIV)

            node = BinOp(left=node, op=token, right=self.factor())

        return node

    def factor(self):
        """factor : PLUS factor
                  | MINUS factor
                  | INTEGER_CONST
                  | REAL_CONST
                  | LPAREN expr RPAREN
                  | variable
                  | STRING_CONST
                  | EQUAL
        """
        token = self.current_token
        if token.type == TokenType.PLUS:
            self.eat(TokenType.PLUS)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.MINUS:
            self.eat(TokenType.MINUS)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.INTEGER_CONST:
            self.eat(TokenType.INTEGER_CONST)
            return Num(token)
        elif token.type == TokenType.REAL_CONST:
            self.eat(TokenType.REAL_CONST)
            return Num(token)
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
        elif token.type == TokenType.STRING_CONST:
            self.eat(TokenType.STRING_CONST)
            return Str(token)
        # elif token.type == TokenType.EQUAL:
        #     self.eat(TokenType.EQUAL)
        #     return Equal(token)
        else:
            node = self.variable()
            return node

    def parse(self):
        """
        program : PROGRAM variable SEMI block DOT
        block : declarations compound_statement
        declarations : (VAR (variable_declaration SEMI)+)? procedure_declaration*
        variable_declaration : ID (COMMA ID)* COLON type_spec
        procedure_declaration :
             PROCEDURE ID (LPAREN formal_parameter_list RPAREN)? SEMI block SEMI
        formal_params_list : formal_parameters
                           | formal_parameters SEMI formal_parameter_list
        formal_parameters : ID (COMMA ID)* COLON type_spec
        type_spec : INTEGER | REAL
        compound_statement : BEGIN statement_list END
        statement_list : statement
                       | statement SEMI statement_list
        statement : compound_statement
                  | proccall_statement
                  | assignment_statement
                  | empty
        proccall_statement : ID LPAREN (expr (COMMA expr)*)? RPAREN
        assignment_statement : variable ASSIGN expr
        io_statement: writeln (param (,param)*) | write (param (,param)*) | readln (param (,param)*) | read (param (,param)*)
        empty :
        expr : term ((PLUS | MINUS) term)*
        term : factor ((MUL | INTEGER_DIV | FLOAT_DIV) factor)*
        factor : PLUS factor
               | MINUS factor
               | INTEGER_CONST
               | REAL_CONST
               | LPAREN expr RPAREN
               | variable
        variable: ID
        """
        node = self.program()
        if self.current_token.type != TokenType.EOF:
            self.error(
                error_code=ErrorCode.UNEXPECTED_TOKEN,
                token=self.current_token,
            )

        return node



















###############################################################################
#                                                                             #
#  Abstract Syntax Tree visitor                                               #
#                                                                             #
###############################################################################

class NodeVisitor:
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


    def log(self, msg):
        if _SHOULD_LOG_VISITOR:
            print(msg)












###############################################################################
#                                                                             #
#  SYMBOLS, TABLES, SEMANTIC ANALYSIS                                         #
#                                                                             #
###############################################################################

class Symbol:
    def __init__(self, name, type=None):
        self.name = name
        self.type = type


class VarSymbol(Symbol):
    def __init__(self, name, type):
        super().__init__(name, type)

    def __str__(self):
        return "<{class_name}(name='{name}', type='{type}')>".format(
            class_name=self.__class__.__name__,
            name=self.name,
            type=self.type,
        )

    __repr__ = __str__


class BuiltinTypeSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<{class_name}(name='{name}')>".format(
            class_name=self.__class__.__name__,
            name=self.name,
        )

class IO_Symbol(Symbol):
    def __init__(self, name, formal_params=None):
        super().__init__(name)
        # a list of VarSymbol objects
        self.formal_params = [] if formal_params is None else formal_params

    def __str__(self):
        return '<{class_name}(operation={name}, parameters={params})>'.format(
            class_name=self.__class__.__name__,
            name=self.name.op,
            params=self.formal_params,
        )

    __repr__ = __str__


class ARRAY_Symbol(Symbol):
    def __init__(self, start_len, end_len, type, members = []):
        super().__init__(name)

    def __str__(self):
        return '<{class_name}(Type={type}, Start_len={start}, End_len={end}, members ={members})>'.format(
            class_name=self.__class__.__name__,
            type=self.type,
            start=self.start_len,
            end= self.end_len,
            members = self.members
        )

    __repr__ = __str__

class IF_Symbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return '<{class_name}(name={name})>'.format(
            class_name=self.__class__.__name__,
            name=self.name
        )

    __repr__ = __str__


class WHILE_Symbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return '<{class_name}(name={name})>'.format(
            class_name=self.__class__.__name__,
            name=self.name
        )

    __repr__ = __str__

class ProcedureSymbol(Symbol):
    def __init__(self, name, formal_params=None):
        super().__init__(name)
        # a list of VarSymbol objects
        self.formal_params = [] if formal_params is None else formal_params
        # a reference to procedure's body (AST sub-tree)
        self.block_ast = None

    def __str__(self):
        return '<{class_name}(name={name}, parameters={params})>'.format(
            class_name=self.__class__.__name__,
            name=self.name,
            params=self.formal_params,
        )

    __repr__ = __str__


class ScopedSymbolTable:
    def __init__(self, scope_name, scope_level, enclosing_scope=None):
        self._symbols = {}
        self.scope_name = scope_name
        self.scope_level = scope_level
        self.enclosing_scope = enclosing_scope

    def _init_builtins(self):
        self.insert(BuiltinTypeSymbol('INTEGER'))
        self.insert(BuiltinTypeSymbol('REAL'))
        self.insert(BuiltinTypeSymbol('STRING_CONST'))
        self.insert(BuiltinTypeSymbol('ARRAY'))


    def __str__(self):
        h1 = 'SCOPE (SCOPED SYMBOL TABLE)'
        lines = ['\n', h1, '=' * len(h1)]
        for header_name, header_value in (
            ('Scope name', self.scope_name),
            ('Scope level', self.scope_level),
            ('Enclosing scope',
             self.enclosing_scope.scope_name if self.enclosing_scope else None
            )
        ):
            lines.append('%-15s: %s' % (header_name, header_value))
        h2 = 'Scope (Scoped symbol table) contents'
        lines.extend([h2, '-' * len(h2)])
        lines.extend(
            ('%7s: %r' % (key, value))
            for key, value in self._symbols.items()
        )
        lines.append('\n')
        s = '\n'.join(lines)
        return s

    __repr__ = __str__

    def log(self, msg):
        if _SHOULD_LOG_SCOPE:
            print(msg)

    def insert(self, symbol):
        self.log(f'Insert: {symbol.name}')
        self._symbols[symbol.name] = symbol

    def lookup(self, name, current_scope_only=False):
        self.log(f'Lookup: {name}. (Scope name: {self.scope_name})')
        symbol = self._symbols.get(name)

        if symbol is not None:
            return symbol

        if current_scope_only:
            return None

        if self.enclosing_scope is not None:
            return self.enclosing_scope.lookup(name)


class SemanticAnalyzer(NodeVisitor):
    def __init__(self):
        self.current_scope = None

    def log(self, msg):
        if _SHOULD_LOG_SCOPE:
            print(msg)

    def error(self, error_code, token):
        raise SemanticError(
            error_code=error_code,
            token=token,
            message=f'{error_code.value} -> {token}',
        )

    def visit_Block(self, node):
        for declaration in node.declarations:
            self.visit(declaration)
        self.visit(node.compound_statement)


    def visit_Str(self, node):
        type_name = node.value

    def visit_IO(self, node):
        param = node.value
        op = node.op
        IO_Symbol(op, param)
        self.current_scope.insert(op)

    def visit_READ(self, node):
        param = node.value
        op = node.op
        IO_Symbol(op, param)
        self.current_scope.insert(op)

    def visit_WRITE(self, node):
        param = node.value
        op = node.op
        IO_Symbol(op, param)
        self.current_scope.insert(op)


    def visit_Program(self, node):
        self.log('ENTER scope: global')
        global_scope = ScopedSymbolTable(
            scope_name='global',
            scope_level=1,
            enclosing_scope=self.current_scope,  # None
        )
        global_scope._init_builtins()
        self.current_scope = global_scope

        # visit subtree
        self.visit(node.block)

        self.log(global_scope)

        self.current_scope = self.current_scope.enclosing_scope
        self.log('LEAVE scope: global \n')

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_NoOp(self, node):
        pass

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_ProcedureDecl(self, node):
        proc_name = node.proc_name
        proc_symbol = ProcedureSymbol(proc_name)
        self.current_scope.insert(proc_symbol)

        self.log(f'ENTER scope: {proc_name}')
        # Scope for parameters and local variables
        procedure_scope = ScopedSymbolTable(
            scope_name=proc_name,
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope
        )
        self.current_scope = procedure_scope

        # Insert parameters into the procedure scope
        for param in node.formal_params:
            param_type = self.current_scope.lookup(param.type_node.value)
            param_name = param.var_node.value
            var_symbol = VarSymbol(param_name, param_type)
            self.current_scope.insert(var_symbol)
            proc_symbol.formal_params.append(var_symbol)

        self.visit(node.block_node)

        self.log(procedure_scope)

        self.current_scope = self.current_scope.enclosing_scope
        self.log(f'LEAVE scope: {proc_name}')

        # accessed by the interpreter when executing procedure call
        proc_symbol.block_ast = node.block_node

    def visit_VarDecl(self, node):
        type_name = node.type_node.value
        type_symbol = self.current_scope.lookup(type_name)

        var_name = node.var_node.value
        var_symbol = VarSymbol(var_name, type_symbol)

        # Signal an error if the table already has a symbol with the same name
        if self.current_scope.lookup(var_name, current_scope_only=True):
            self.error(
                error_code=ErrorCode.DUPLICATE_ID,
                token=node.var_node.token,
            )

        self.current_scope.insert(var_symbol)

    def visit_ARRAY(self, node):
        start = node.start
        end = node.end
        type = node.value
        members = node.members
        symbol = ARRAY_Symbol(start,end,type,members)
        self.current_scope.insert(symbol)


    def visit_Assign(self, node):
        # right-hand side
        self.visit(node.right)
        # left-hand side
        self.visit(node.left)


    def visit_Var(self, node):
        var_name = node.value
        var_symbol = self.current_scope.lookup(var_name)
        if var_symbol is None:
            self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.token)

    def visit_Num(self, node):
        pass

    def visit_UnaryOp(self, node):
        pass

    def visit_ProcedureCall(self, node):
        for param_node in node.actual_params:
            self.visit(param_node)

        proc_symbol = self.current_scope.lookup(node.proc_name)
        # accessed by the interpreter when executing procedure call
        node.proc_symbol = proc_symbol


    def visit_IfStatement(self, node):
        name = node.name
        symbol = IF_Symbol(name)
        self.current_scope.insert(symbol)

    def visit_WhileStatement(self, node):
        name = node.name
        symbol = IF_Symbol(name)
        self.current_scope.insert(symbol)























###############################################################################
#                                                                             #
#  INTERPRETER                                                                #
#                                                                             #
###############################################################################


class ARType(Enum):
    PROGRAM   = 'PROGRAM'
    PROCEDURE = 'PROCEDURE'


class CallStack:
    def __init__(self):
        self._records = []

    def push(self, ar):
        self._records.append(ar)

    def pop(self):
        return self._records.pop()

    def look_at_next_char(self):
        return self._records[-1]

    def __str__(self):
        s = '\n'.join(repr(ar) for ar in reversed(self._records))
        s = f'CALL STACK\n{s}\n\n'
        return s

    def __repr__(self):
        return self.__str__()


class ActivationRecord:
    def __init__(self, name, type, nesting_level):
        self.name = name
        self.type = type
        self.nesting_level = nesting_level
        self.members = {}
        self.counter = 0


    def __setitem__(self, key, value):
        self.members[key] = value

    def __getitem__(self, key):
        return self.members[key]

    def get(self, key):
        return self.members.get(key)

    def log(self, msg):
        if _SHOULD_LOG_MIPS:
            print(msg)

    def __str__(self):
        lines = [
            '{level}: {type} {name}'.format(
                level=self.nesting_level,
                type=self.type.value,
                name=self.name,
            )
        ]

        for name, val in self.members.items():
            lines.append(f'   {name:<20}: {val}')
            self.log(f'li $t{self.counter}, {val}\n')
            self.counter+=1
            #machine_code_out(val)
        s = '\n'.join(lines)
        return s


    def __repr__(self):
        return self.__str__()



class Interpreter(NodeVisitor):
    def __init__(self, tree):
        self.tree = tree
        self.call_stack = CallStack()

    def log(self, msg):
        if _SHOULD_LOG_STACK:
            print(msg)

    def visit_Program(self, node):
        program_name = node.name
        self.log(f'ENTER: PROGRAM {program_name}')
        ar = ActivationRecord(
            name=program_name,
            type=ARType.PROGRAM,
            nesting_level=1,
        )
        self.call_stack.push(ar)

        self.log(str(self.call_stack))

        self.visit(node.block)

        self.log(f'LEAVE: PROGRAM {program_name}')
        self.log(str(self.call_stack))

        self.call_stack.pop()

    def visit_Block(self, node):
        for declaration in node.declarations:
            self.visit(declaration)
        self.visit(node.compound_statement)

    def visit_VarDecl(self, node):
        # Do nothing
        pass

    def visit_Type(self, node):
        # Do nothing
        pass


    def visit_Str(self, node):
        type_name = node.value
        return type_name

    def visit_WRITE(self, node):
        param = node.value
        op = node.op
        #return param, op
        if  node.op == TokenType.WRITELN:
            self.log(f'{str(op).strip("TokenType.")} -> {param} \\n \n')
        else:
            self.log(f'{str(op).strip("TokenType.")} -> {param}\n')

    def visit_READ(self, node):
        param = node.value
        op = node.op
        #return param, op
        if  node.op == TokenType.READLN:
            self.log(f'{str(op).strip("TokenType.")} -> {param} \\n \n')
        else:
            self.log(f'{str(op).strip("TokenType.")} -> {param}\n')


    def visit_BinOp(self, node):
        if node.op.type == TokenType.PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == TokenType.MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == TokenType.MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == TokenType.INTEGER_DIV:
            return self.visit(node.left) // self.visit(node.right)
        elif node.op.type == TokenType.FLOAT_DIV:
            return float(self.visit(node.left)) / float(self.visit(node.right))

    def visit_Num(self, node):
        return node.value

    def visit_UnaryOp(self, node):
        op = node.op.type
        if op == TokenType.PLUS:
            return +self.visit(node.expr)
        elif op == TokenType.MINUS:
            return -self.visit(node.expr)

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Assign(self, node):
        var_name = node.left.value
        var_value = self.visit(node.right)

        ar = self.call_stack.look_at_next_char()
        ar[var_name] = var_value

    def visit_Var(self, node):
        var_name = node.value

        ar = self.call_stack.look_at_next_char()
        var_value = ar.get(var_name)

        return var_value

    def visit_NoOp(self, node):
        pass

    def visit_ProcedureDecl(self, node):
        pass

    def visit_ProcedureCall(self, node):
        proc_name = node.proc_name

        ar = ActivationRecord(
            name=proc_name,
            type=ARType.PROCEDURE,
            nesting_level=2,
        )

        proc_symbol = node.proc_symbol

        formal_params = proc_symbol.formal_params
        actual_params = node.actual_params

        for param_symbol, argument_node in zip(formal_params, actual_params):
            ar[param_symbol.name] = self.visit(argument_node)

        self.call_stack.push(ar)

        self.log(f'ENTER: PROCEDURE {proc_name}')
        self.log(str(self.call_stack))

        # evaluate procedure body
        self.visit(proc_symbol.block_ast)

        self.log(f'LEAVE: PROCEDURE {proc_name}')
        self.log(str(self.call_stack))

        self.call_stack.pop()


    def visit_IfStatement(self, node):
        # If part
        left_value = self.visit(node.expr.left)
        token = str(node.expr.token.type)
        right = node.expr.right.value
        # then Part
        # ar = self.call_stack.look_at_next_char()
        # print(ar)
        if token == 'TokenType.EQUAL':
            if left_value == right:
                left_value_then = node.statement.left.value
                token_then = node.statement.token.type
                right_then = node.statement.right.value
                self.log(f'IF Statement Result => {left_value_then}  : {right_then}\n')
            else:
                #else part
                left_value_else = node.elseStatement.left.value
                token_else = node.elseStatement.token.type
                right_else = node.elseStatement.right.value
                self.log(f'IF Statement Result => {left_value_else}  : {right_else}\n')

        if token == 'TokenType.LESS':
            if left_value < right:
                left_value_then = node.statement.left.value
                token_then = node.statement.token.type
                right_then = node.statement.right.value
                self.log(f'IF Statement Result => {left_value_then}  : {right_then}\n')
            else:
                #else part
                left_value_else = node.elseStatement.left.value
                token_else = node.elseStatement.token.type
                right_else = node.elseStatement.right.value
                self.log(f'IF Statement Result => {left_value_else}  : {right_else}\n')

        if token == 'TokenType.LESSEQUAL':
            if left_value <= right:
                left_value_then = node.statement.left.value
                token_then = node.statement.token.type
                right_then = node.statement.right.value
                self.log(f'IF Statement Result => {left_value_then}  : {right_then}\n')
            else:
                #else part
                left_value_else = node.elseStatement.left.value
                token_else = node.elseStatement.token.type
                right_else = node.elseStatement.right.value
                self.log(f'IF Statement Result => {left_value_else}  : {right_else}\n')

        if token == 'TokenType.GREATER':
            if left_value > right:
                left_value_then = node.statement.left.value
                token_then = node.statement.token.type
                right_then = node.statement.right.value
                self.log(f'IF Statement Result => {left_value_then}  : {right_then}\n')
            else:
                #else part
                left_value_else = node.elseStatement.left.value
                token_else = node.elseStatement.token.type
                right_else = node.elseStatement.right.value
                self.log(f'IF Statement Result => {left_value_else}  : {right_else}\n')

        if token == 'TokenType.GREATEREQUAL':
            if left_value >= right:
                left_value_then = node.statement.left.value
                token_then = node.statement.token.type
                right_then = node.statement.right.value
                self.log(f'IF Statement Result => {left_value_then}  : {right_then}\n')
            else:
                #else part
                left_value_else = node.elseStatement.left.value
                token_else = node.elseStatement.token.type
                right_else = node.elseStatement.right.value
                self.log(f'IF Statement Result => {left_value_else}  : {right_else}\n')


    def visit_WhileStatement(self, node):
        # While
        left_value = self.visit(node.expr.left)
        token = str(node.expr.token.type)
        right = node.expr.right.value
        # Do
        if token == 'TokenType.EQUAL':
            if left_value == right:
                left_value_then = node.statement.left.value
                token_then = node.statement.token.type
                right_then = node.statement.right.value
                self.log(f'While Statement Result => {left_value_then}  : {right_then}\n')

        if token == 'TokenType.GREATER':
            if left_value > right:
                left_value_then = node.statement.left.value
                token_then = node.statement.token.type
                right_then = node.statement.right.value
                self.log(f'While Statement Result => {left_value_then}  : {right_then}\n')

        if token == 'TokenType.GREATEREQUAL':
            if left_value >= right:
                left_value_then = node.statement.left.value
                token_then = node.statement.token.type
                right_then = node.statement.right.value
                self.log(f'While Statement Result => {left_value_then}  : {right_then}\n')

        if token == 'TokenType.LESS':
            if left_value < right:
                left_value_then = node.statement.left.value
                token_then = node.statement.token.type
                right_then = node.statement.right.value
                self.log(f'While Statement Result => {left_value_then}  : {right_then}\n')

        if token == 'TokenType.LESSEQUAL':
            if left_value <= right:
                left_value_then = node.statement.left.value
                token_then = node.statement.token.type
                right_then = node.statement.right.value
                self.log(f'While Statement Result => {left_value_then}  : {right_then}\n')

    def interpret(self):
        tree = self.tree
        if tree is None:
            return ''
        return self.visit(tree)















def main():
    parser = argparse.ArgumentParser(
        description='Mini Pascal Compiler'
    )
    parser.add_argument('inputfile', help='Pascal source file')
    parser.add_argument(
        '--scope',
        help='Print scope information',
        action='store_true',
    )
    parser.add_argument(
        '--stack',
        help='Print call stack',
        action='store_true',
    )
    parser.add_argument(
        '--lexer',
        help='Print lexer tokens',
        action='store_true',
    )
    parser.add_argument(
        '--visitor',
        help='Print lexer tokens',
        action='store_true',
    )
    parser.add_argument(
        '--mips',
        help='Print lexer tokens',
        action='store_true',
    )
    args = parser.parse_args()

    global _SHOULD_LOG_SCOPE, _SHOULD_LOG_STACK, _SHOULD_LOG_LEXER, _SHOULD_LOG_VISITOR, _SHOULD_LOG_MIPS
    _SHOULD_LOG_SCOPE, _SHOULD_LOG_STACK, _SHOULD_LOG_LEXER, _SHOULD_LOG_VISITOR, _SHOULD_LOG_MIPS  = args.scope, args.stack, args.lexer, args.visitor, args.mips

    text = open(args.inputfile, 'r').read()

    lexer = Lexer(text)
    try:
        parser = Parser(lexer)
        tree = parser.parse()
    except (LexerError, ParserError) as e:
        print(e.message)
        sys.exit(1)

    semantic_analyzer = SemanticAnalyzer()
    try:
        semantic_analyzer.visit(tree)
    except SemanticError as e:
        print(e.message)
        sys.exit(1)

    interpreter = Interpreter(tree)
    interpreter.interpret()


if __name__ == '__main__':
    main()
