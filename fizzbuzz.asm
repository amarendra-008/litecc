.data
str0: .asciiz "FizzBuzz
"
str1: .asciiz "Fizz
"
str2: .asciiz "Buzz
"
str3: .asciiz "
"

.text
.globl main

main:
    addi $sp, $sp, -8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    addi $sp, $sp, -4
    li $t0, 1
    sw $t0, -4($fp)
for0:
    lw $t0, -4($fp)
    addi $sp, $sp, -4
    sw $t0, 0($sp)
    li $t0, 100
    move $t1, $t0
    lw $t0, 0($sp)
    addi $sp, $sp, 4
    slt $t0, $t1, $t0
    xori $t0, $t0, 1
    beq $t0, $zero, endfor1
    addi $sp, $sp, -4
    addi $sp, $sp, -4
    lw $t0, -4($fp)
    addi $sp, $sp, -4
    sw $t0, 0($sp)
    li $t0, 3
    move $t1, $t0
    lw $t0, 0($sp)
    addi $sp, $sp, 4
    div $t0, $t1
    mfhi $t0
    sw $t0, -8($fp)
    lw $t0, -4($fp)
    addi $sp, $sp, -4
    sw $t0, 0($sp)
    li $t0, 5
    move $t1, $t0
    lw $t0, 0($sp)
    addi $sp, $sp, 4
    div $t0, $t1
    mfhi $t0
    sw $t0, -12($fp)
    lw $t0, -8($fp)
    addi $sp, $sp, -4
    sw $t0, 0($sp)
    li $t0, 0
    move $t1, $t0
    lw $t0, 0($sp)
    addi $sp, $sp, 4
    sub $t0, $t0, $t1
    slt $t2, $t0, $zero
    slt $t3, $zero, $t0
    or $t0, $t2, $t3
    xori $t0, $t0, 1
    beq $t0, $zero, else2
    lw $t0, -12($fp)
    addi $sp, $sp, -4
    sw $t0, 0($sp)
    li $t0, 0
    move $t1, $t0
    lw $t0, 0($sp)
    addi $sp, $sp, 4
    sub $t0, $t0, $t1
    slt $t2, $t0, $zero
    slt $t3, $zero, $t0
    or $t0, $t2, $t3
    xori $t0, $t0, 1
    beq $t0, $zero, else4
    la $t0, str0
    move $a0, $t0
    jal print_str
    j endif5
else4:
    la $t0, str1
    move $a0, $t0
    jal print_str
endif5:
    j endif3
else2:
    lw $t0, -12($fp)
    addi $sp, $sp, -4
    sw $t0, 0($sp)
    li $t0, 0
    move $t1, $t0
    lw $t0, 0($sp)
    addi $sp, $sp, 4
    sub $t0, $t0, $t1
    slt $t2, $t0, $zero
    slt $t3, $zero, $t0
    or $t0, $t2, $t3
    xori $t0, $t0, 1
    beq $t0, $zero, else6
    la $t0, str2
    move $a0, $t0
    jal print_str
    j endif7
else6:
    lw $t0, -4($fp)
    move $a0, $t0
    jal print_int
    la $t0, str3
    move $a0, $t0
    jal print_str
endif7:
endif3:
    lw $t0, -4($fp)
    move $t2, $t0
    addi $t0, $t0, 1
    sw $t0, -4($fp)
    move $t0, $t2
    j for0
endfor1:
    li $t0, 0
    move $v0, $t0
    j main_exit
main_exit:
    move $sp, $fp
    lw $fp, 0($sp)
    lw $ra, 4($sp)
    addi $sp, $sp, 8
    jr $ra


print_int:
    li $v0, 1
    syscall
    jr $ra

print_str:
    li $v0, 4
    syscall
    jr $ra