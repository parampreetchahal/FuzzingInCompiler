from lark import Lark, Transformer
import llvmlite.ir as ir
import llvmlite.binding as llvm

# Define grammar for the toy language
grammar = """
    start: stmt+
    stmt: "print" expr ";"       -> print_stmt
        | NAME "=" expr ";"      -> assign_stmt
    expr: expr "+" term          -> add
        | expr "-" term          -> sub
        | term
    term: term "*" factor        -> mul
        | term "/" factor        -> div
        | factor
    factor: NUMBER               -> number
          | NAME                 -> var
          | "(" expr ")"
    NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    NUMBER: /[0-9]+/
    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, parser="lalr")

class CodeGen(Transformer):
    def __init__(self):
        self.module = ir.Module(name="mini_compiler")
        self.builder = None
        self.func = None
        self.symbols = {}  # Store variable allocations

        # Create main function
        func_type = ir.FunctionType(ir.VoidType(), [], False)
        self.func = ir.Function(self.module, func_type, name="main")
        block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)

    def start(self, stmts):
        self.builder.ret_void()  # End function
        return self.module

    def print_stmt(self, args):
        value = args[0]
        print_func_type = ir.FunctionType(ir.VoidType(), [ir.IntType(32)], False)
        print_func = ir.Function(self.module, print_func_type, name="print")
        self.builder.call(print_func, [value])
        return value

    def assign_stmt(self, args):
        var_name = args[0]
        value = args[1]
        ptr = self.builder.alloca(ir.IntType(32), name=var_name)
        self.builder.store(value, ptr)
        self.symbols[var_name] = ptr
        return value

    def add(self, args):
        lhs = self.transform(args[0])  # Transform left operand
        rhs = self.transform(args[1])  # Transform right operand
        
        if not isinstance(lhs, ir.Value) or not isinstance(rhs, ir.Value):
            raise TypeError("Operands must be LLVM IR values")

        return self.builder.add(lhs, rhs)

    def sub(self, args):
        lhs = self.transform(args[0])
        rhs = self.transform(args[1])

        if not isinstance(lhs, ir.Value) or not isinstance(rhs, ir.Value):
            raise TypeError("Operands must be LLVM IR values")

        return self.builder.sub(lhs, rhs)

    def mul(self, args):
        lhs = self.transform(args[0])
        rhs = self.transform(args[1])

        if not isinstance(lhs, ir.Value) or not isinstance(rhs, ir.Value):
            raise TypeError("Operands must be LLVM IR values")

        return self.builder.mul(lhs, rhs)

    def div(self, args):
        lhs = self.transform(args[0])
        rhs = self.transform(args[1])

        if not isinstance(lhs, ir.Value) or not isinstance(rhs, ir.Value):
            raise TypeError("Operands must be LLVM IR values")

        return self.builder.sdiv(lhs, rhs)

    def number(self, args):
        """Convert numbers into LLVM IR constant integers."""
        return ir.Constant(ir.IntType(32), int(args[0]))

    def var(self, args):
        """Load variables from memory if they exist."""
        var_name = str(args[0])
        if var_name not in self.symbols:
            raise NameError(f"Variable '{var_name}' not defined")
        return self.builder.load(self.symbols[var_name], name=var_name)



# Compile input code
def compile_code(code):
    tree = parser.parse(code)
    codegen = CodeGen()
    llvm_ir = codegen.transform(tree)
    return llvm_ir

if __name__ == "__main__":
    sample_code = "x = 5 + 3; print x;"
    compiled_ir = compile_code(sample_code)
    print("Generated LLVM IR:\n", compiled_ir)