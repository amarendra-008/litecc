int main() {
    int i;
    for (i = 1; i <= 100; i++) {
        int by3;
        int by5;
        
        by3 = i % 3;
        by5 = i % 5;
        
        if (by3 == 0) {
            if (by5 == 0) {
                print_str("FizzBuzz\n");
            } else {
                print_str("Fizz\n");
            }
        } else {
            if (by5 == 0) {
                print_str("Buzz\n");
            } else {
                print_int(i);
                print_str("\n");
            }
        }
    }
    
    return 0;
}