#include <stdio.h>

int main() {
    int a = 100;
    float b = 20.5;
    printf("enter a: ");
    scanf("%d",&a);
    if(a>10){
      printf("Sum: %f\n", a + b);
    }
    else{
      printf("No Bye");
    }
    
    return 0;
}

