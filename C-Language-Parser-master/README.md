# C-Language-Parser

A complete Parser for C-Language using **Lex and Yacc**, extended to **compile and execute valid C code** just like a mini-compiler.

---

## INTRODUCTION
___________________________________

A parser is a compiler or interpreter component that breaks data into smaller elements for easy translation into another language. It takes input as a sequence of tokens and builds a data structure — usually a parse tree or abstract syntax tree (AST).

The main job of a parser for a programming language is to read the source program and discover its structure.

Lex and Yacc automate this process by breaking it into subtasks:

1. **Lex (Lexical Analyzer):** Splits the source code into tokens.  
2. **Yacc (Parser Generator):** Builds the hierarchical structure using grammar rules.

---

### 🔹 Lex - A Lexical Analyzer Generator

Lex generates a C program that partitions the input stream based on defined regular expressions. Each match triggers a user-defined C code fragment, enabling token-based parsing.

---

### 🔹 Yacc - Yet Another Compiler-Compiler

Yacc creates a parser in C based on grammar production rules. Each rule is tied to an action (C code) that executes when the rule is matched. It works with Lex to process tokens and ensure syntactic correctness.

---

### ✅ What This Project Does

This parser detects **syntactic correctness** of a given C-language program. If the program is valid:

- It confirms parsing success.
- Then it compiles the same program using `gcc`.
- Finally, it executes the compiled binary and shows the result on the terminal — **just like a real C compiler**.

In case of syntax errors, the parser:

- Reports the line number of the error.
- Shows the unexpected token and expected alternatives to help debug.

> ⚠️ **Note:** Semantic correctness is not checked — uninitialized or undeclared variables won’t raise errors during parsing.

---

## REQUIREMENTS & INSTALLATION
___________________________________

These instructions are for Debian-based systems like **Ubuntu** or **Fedora**.

### Install Flex and Bison:

**Ubuntu:**
```bash
sudo apt-get install flex
sudo apt-get install bison
```

## EXECUTION STEPS

### 🔧 Manual Compilation

**1. Compile Yacc (Bison) File:**
```bash
bison -d project.y
```

Generates:

project.tab.c

project.tab.h

2. Compile Lex File:


```bash
flex project.l
```
Generates:

lex.yy.c

3. Compile the Parser Executable:

```bash
gcc lex.yy.c project.tab.c -o parser -lm
```

4. Run the Parser with a C Program (e.g., test.c):

```bash
./parser < test.c
```
```output
Parsing Successful
```

🚀 Shell Script Automation
Automate all of the above using run.sh:

```bash
chmod +x compile_and_run.sh
./compile_and_run.sh test.c
```

What run.sh does:

Runs the parser

If valid, compiles the C file using gcc

Executes the compiled binary and prints the output

🧾 Outputs
✅ On Success:

```output
Parsing Successful!
Compiling with GCC...
Execution Result:
<your program output>
❌ On Syntax Error:
```

```nginx
Parsing Failed
Line Number: 19 syntax error, unexpected '{', expecting ';' or ','
```

❓ FAQ
Q: What if my code uses undeclared variables or uninitialized values?
A: The parser will still report it as syntactically correct. Semantic errors are not handled yet.

Q: Can I declare variables anywhere in a block?
A: No, declarations must appear at the start of a code block, before any executable statements.

✅ Summary of What We've Done So Far
✅ Built a working C-language parser using Lex & Yacc

✅ Integrated syntax error reporting with line numbers

✅ Added grammar rules for C constructs: declarations, loops, expressions, etc.

✅ Implemented shell automation to:

Parse the file

Compile it with gcc

Run and display output

🎯 This provides a mini compiler experience, ideal for:

Educational purposes

Experimentation

Building a full-fledged compiler

🛣️ Roadmap Ideas (Optional Next Steps)
🧠 Add semantic analysis (type checking, declaration checks)

⚙️ Generate intermediate representation (IR) or assembly

🌐 Integrate with a simple GUI or web frontend
```
