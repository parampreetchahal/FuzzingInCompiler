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

    # Default transformer to unwrap nodes with a single child.
    def __default__(self, data, children, meta):
        if len(children) == 1:
            return children[0]
        return children

    def start(self, stmts):
        self.builder.ret_void()  # End function
        return self.module

    def print_stmt(self, args):
        value = args[0]
        printf_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
        printf = ir.Function(self.module, printf_ty, name="printf")
        
        # Create format string for printing integers
        format_str = "%d\n\0"
        format_str_global = ir.GlobalVariable(self.module, ir.ArrayType(ir.IntType(8), len(format_str)), name="format_str")
        format_str_global.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), len(format_str)), bytearray(format_str.encode("utf8")))
        format_str_global.global_constant = True
        
        # Get pointer to the format string
        fmt_ptr = self.builder.gep(format_str_global, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
        
        # Call printf
        self.builder.call(printf, [fmt_ptr, value])
        return value

    def assign_stmt(self, args):
        var_name = str(args[0])
        value = args[1]
        ptr = self.builder.alloca(ir.IntType(32), name=var_name)
        self.builder.store(value, ptr)
        self.symbols[var_name] = ptr
        return value

    def add(self, args):
        return self.builder.add(args[0], args[1])

    def sub(self, args):
        return self.builder.sub(args[0], args[1])

    def mul(self, args):
        return self.builder.mul(args[0], args[1])

    def div(self, args):
        return self.builder.sdiv(args[0], args[1])

    def number(self, args):
        return ir.Constant(ir.IntType(32), int(args[0]))

    def var(self, args):
        var_name = str(args[0])
        if var_name not in self.symbols:
            raise ValueError(f"Undefined variable '{var_name}'")
        return self.builder.load(self.symbols[var_name], var_name)

# Compile input code
def compile_code(code):
    tree = parser.parse(code)
    codegen = CodeGen()
    llvm_ir = codegen.transform(tree)
    return llvm_ir

def execute_ir(ir_code):
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    # Create a target machine representing the native architecture
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()

    # Compile the IR
    backing_mod = llvm.parse_assembly(str(ir_code))
    backing_mod.verify()

    # JIT Execution
    engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
    engine.finalize_object()
    engine.run_static_constructors()

    # Look up the 'main' function and execute
    func_ptr = engine.get_function_address("main")
    import ctypes
    main_func = ctypes.CFUNCTYPE(None)(func_ptr)
    print("\nExecution Output:")
    main_func()

if __name__ == "__main__":
    sample_code = "x = 5 + 3; print x;"
    compiled_ir = compile_code(sample_code)
    print("Generated LLVM IR:\n", compiled_ir)
    execute_ir(compiled_ir)
