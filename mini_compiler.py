from lark import Lark, Transformer
import llvmlite.ir as ir
import llvmlite.binding as llvm

# Define grammar for the toy language
grammar = """
    start: stmt+
    stmt: "print" expr ";"       -> print_stmt
        | NAME "=" expr ";"      -> assign_stmt
        | "input" NAME ";"       -> input_stmt
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
        func_type = ir.FunctionType(ir.IntType(32), [], False)
        self.func = ir.Function(self.module, func_type, name="main")
        block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)

        #Declare printf function
        printf_type = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
        self.printf = ir.Function(self.module, printf_type, name="printf")

        #Declare scanf function
        scanf_type = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
        self.scanf = ir.Function(self.module, scanf_type, name="scanf")

        # Create global strings for I/O
        self.fmt_str = ir.GlobalVariable(self.module, ir.ArrayType(ir.IntType(8), 4), name="fmt_str")
        self.fmt_str.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), 4), bytearray("%d\n\0", "utf8"))

        self.scanf_str = ir.GlobalVariable(self.module, ir.ArrayType(ir.IntType(8), 3), name="scanf_str")
        self.scanf_str.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), 3), bytearray("%d\0", "utf8"))

    # Default transformer to unwrap nodes with a single child.
    def __default__(self, data, children, meta):
        if len(children) == 1:
            return children[0]
        return children

    def start(self, stmts):
        self.builder.ret(ir.Constant(ir.IntType(32), 0))  # End function
        return self.module

    def print_stmt(self, args):
        value = args[0]
        fmt_ptr = self.builder.bitcast(self.fmt_str, ir.PointerType(ir.IntType(8)))
        self.builder.call(self.printf, [fmt_ptr, value])
        return value
    
    def input_stmt(self, args):
        var_name = args[0]
        ptr = self.builder.alloca(ir.IntType(32), name=var_name)
        self.symbols[var_name] = ptr
        fmt_ptr = self.builder.bitcast(self.scanf_str, ir.PointerType(ir.IntType(8)))
        self.builder.call(self.scanf, [fmt_ptr, ptr])
        return ptr
    
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
        dividend, divisor = args

    # Check if divisor is zero
        zero = ir.Constant(ir.IntType(32), 0)
        is_zero = self.builder.icmp_unsigned("==", divisor, zero)

        # Create blocks for handling the error
        error_block = self.func.append_basic_block(name="div_by_zero")
        continue_block = self.func.append_basic_block(name="continue")

        # Branch based on the condition
        self.builder.cbranch(is_zero, error_block, continue_block)

        # Error block (print message and exit)
        self.builder.position_at_end(error_block)
        error_msg = ir.GlobalVariable(self.module, ir.ArrayType(ir.IntType(8), 25), name="error_msg")
        error_msg.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), 25), bytearray("Error: Division by zero\n\0", "utf8"))

        error_ptr = self.builder.bitcast(error_msg, ir.PointerType(ir.IntType(8)))
        self.builder.call(self.printf, [error_ptr])
        self.builder.ret(ir.Constant(ir.IntType(32), -1))  # Exit with error code

        # Continue block (perform division)
        self.builder.position_at_end(continue_block)
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
    try:
        tree = parser.parse(code)
    except Exception as e:
        raise SyntaxError(f"Syntax error: {e}")

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
    main_func = ctypes.CFUNCTYPE(ctypes.c_int)(func_ptr)
    print("\nExecution Output:")
    main_func()

if __name__ == "__main__":
    sample_code = """
    input x;
    x=10/x;
    print x;
    """
    compiled_ir = compile_code(sample_code)
    print("Generated LLVM IR:\n", compiled_ir)

    # Execute the compiled code
    print("\nExecuting LLVM IR...")
    result = execute_ir(compiled_ir)
    print("Execution finished with return value:", result)