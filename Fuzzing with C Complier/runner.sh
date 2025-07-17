flex project.l
bison -d project.y
afl-cc lex.yy.c y.tab.c -o compiler_afl -lm

mkdir -p inputs
echo "int main() { return 0; }" > inputs/test.c

afl-fuzz -i inputs -o outputs ./compiler_afl @@
