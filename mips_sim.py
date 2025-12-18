#!/usr/bin/env python3
import sys
import re

class MIPSInterpreter:
    def __init__(self):
        self.regs = [0] * 32
        self.reg_names = {
            '$zero': 0, '$at': 1,
            '$v0': 2, '$v1': 3,
            '$a0': 4, '$a1': 5, '$a2': 6, '$a3': 7,
            '$t0': 8, '$t1': 9, '$t2': 10, '$t3': 11,
            '$t4': 12, '$t5': 13, '$t6': 14, '$t7': 15,
            '$s0': 16, '$s1': 17, '$s2': 18, '$s3': 19,
            '$s4': 20, '$s5': 21, '$s6': 22, '$s7': 23,
            '$t8': 24, '$t9': 25,
            '$k0': 26, '$k1': 27,
            '$gp': 28, '$sp': 29, '$fp': 30, '$ra': 31
        }
        self.memory = {}
        self.data_strings = {}
        self.labels = {}
        self.pc = 0
        self.instructions = []
        self.running = True
    
    def get_reg(self, name):
        if name in self.reg_names:
            idx = self.reg_names[name]
            if idx == 0:
                return 0
            return self.regs[idx]
        raise Exception(f"Unknown register: {name}")
    
    def set_reg(self, name, value):
        if name in self.reg_names:
            idx = self.reg_names[name]
            if idx != 0:
                self.regs[idx] = value & 0xFFFFFFFF
    
    def read_mem(self, addr):
        word = 0
        for i in range(4):
            byte = self.memory.get(addr + i, 0)
            word |= (byte << (i * 8))
        return word
    
    def write_mem(self, addr, word):
        for i in range(4):
            self.memory[addr + i] = (word >> (i * 8)) & 0xFF
    
    def parse_offset_reg(self, operand):
        match = re.match(r'(-?\d+)\((\$\w+)\)', operand)
        if match:
            offset = int(match.group(1))
            reg = match.group(2)
            return offset, reg
        raise Exception(f"Invalid offset(reg): {operand}")
    
    def load_program(self, asm_code):
        lines = asm_code.split('\n')
        in_data = False
        in_text = False
        current_string_label = None
        current_string = ""
        
        for line in lines:
            orig_line = line
            line = line.strip()
            
            if line == '.data':
                in_data = True
                in_text = False
                continue
            elif line == '.text' or line.startswith('.globl'):
                in_data = False
                in_text = True
                if current_string_label:
                    self.data_strings[current_string_label] = current_string
                    current_string_label = None
                    current_string = ""
                continue
            
            if not line or line.startswith('#'):
                continue
            
            if in_data:
                match = re.match(r'(\w+):\s*\.asciiz\s*"(.*)', orig_line)
                if match:
                    if current_string_label:
                        self.data_strings[current_string_label] = current_string
                    
                    current_string_label = match.group(1)
                    rest = match.group(2)
                    if rest.endswith('"'):
                        current_string = rest[:-1]
                        current_string = current_string.replace('\\n', '\n').replace('\\t', '\t')
                        self.data_strings[current_string_label] = current_string
                        current_string_label = None
                        current_string = ""
                    else:
                        current_string = rest + '\n'
                elif current_string_label:
                    if orig_line.rstrip().endswith('"'):
                        current_string += orig_line.rstrip()[:-1]
                        current_string = current_string.replace('\\n', '\n').replace('\\t', '\t')
                        self.data_strings[current_string_label] = current_string
                        current_string_label = None
                        current_string = ""
                    else:
                        current_string += orig_line + '\n'
            
            elif in_text:
                if ':' in line and not line.strip().startswith('#'):
                    label_match = re.match(r'(\w+):', line)
                    if label_match:
                        label = label_match.group(1)
                        self.labels[label] = len(self.instructions)
                        rest = line[line.index(':')+1:].strip()
                        if rest and not rest.startswith('#'):
                            self.instructions.append(rest)
                    continue
                
                if line and not line.startswith('.'):
                    self.instructions.append(line)
        
        self.set_reg('$sp', 0x7ffffffc)
    
    def run(self):
        if 'main' not in self.labels:
            raise Exception("No main function found")
        
        self.pc = self.labels['main']
        max_iter = 100000
        iterations = 0
        
        while self.running and iterations < max_iter:
            if self.pc >= len(self.instructions):
                break
            
            inst = self.instructions[self.pc].strip()
            if not inst or inst.startswith('#'):
                self.pc += 1
                continue
            
            self.execute(inst)
            iterations += 1
    
    def execute(self, inst):
        if '#' in inst:
            inst = inst[:inst.index('#')]
        inst = inst.strip()
        
        parts = inst.split()
        if not parts:
            self.pc += 1
            return
        
        op = parts[0]
        
        operands = []
        for part in parts[1:]:
            operands.extend(part.split(','))
        operands = [o.strip() for o in operands if o.strip()]
        
        if op == 'li':
            self.set_reg(operands[0], int(operands[1]))
        
        elif op == 'la':
            label = operands[1]
            if label in self.data_strings:
                addr = 0x10000000 + len(label)
                self.set_reg(operands[0], addr)
                string = self.data_strings[label]
                for i, char in enumerate(string):
                    self.memory[addr + i] = ord(char)
                self.memory[addr + len(string)] = 0
            else:
                raise Exception(f"Unknown label: {label}")
        
        elif op == 'move':
            self.set_reg(operands[0], self.get_reg(operands[1]))
        
        elif op == 'add':
            val1 = self.get_reg(operands[1])
            val2 = self.get_reg(operands[2])
            self.set_reg(operands[0], val1 + val2)
        
        elif op == 'addi':
            val = self.get_reg(operands[1])
            imm = int(operands[2])
            self.set_reg(operands[0], val + imm)
        
        elif op == 'sub':
            val1 = self.get_reg(operands[1])
            val2 = self.get_reg(operands[2])
            self.set_reg(operands[0], val1 - val2)
        
        elif op == 'mul':
            val1 = self.get_reg(operands[1])
            val2 = self.get_reg(operands[2])
            self.set_reg(operands[0], val1 * val2)
        
        elif op == 'div':
            val1 = self.get_reg(operands[0])
            val2 = self.get_reg(operands[1])
            if val2 == 0:
                raise Exception("Division by zero")
            self.lo = val1 // val2
            self.hi = val1 % val2
        
        elif op == 'mflo':
            self.set_reg(operands[0], getattr(self, 'lo', 0))
        
        elif op == 'mfhi':
            self.set_reg(operands[0], getattr(self, 'hi', 0))
        
        elif op == 'slt':
            val1 = self.get_reg(operands[1])
            val2 = self.get_reg(operands[2])
            if val1 & 0x80000000:
                val1 = val1 - 0x100000000
            if val2 & 0x80000000:
                val2 = val2 - 0x100000000
            self.set_reg(operands[0], 1 if val1 < val2 else 0)
        
        elif op == 'sltu':
            val1 = self.get_reg(operands[1])
            val2 = self.get_reg(operands[2])
            self.set_reg(operands[0], 1 if val1 < val2 else 0)
        
        elif op == 'and':
            val1 = self.get_reg(operands[1])
            val2 = self.get_reg(operands[2])
            self.set_reg(operands[0], val1 & val2)
        
        elif op == 'andi':
            val = self.get_reg(operands[1])
            imm = int(operands[2])
            self.set_reg(operands[0], val & imm)
        
        elif op == 'or':
            val1 = self.get_reg(operands[1])
            val2 = self.get_reg(operands[2])
            self.set_reg(operands[0], val1 | val2)
        
        elif op == 'xori':
            val = self.get_reg(operands[1])
            imm = int(operands[2])
            self.set_reg(operands[0], val ^ imm)
        
        elif op == 'lw':
            offset, reg = self.parse_offset_reg(operands[1])
            addr = self.get_reg(reg) + offset
            self.set_reg(operands[0], self.read_mem(addr))
        
        elif op == 'sw':
            offset, reg = self.parse_offset_reg(operands[1])
            addr = self.get_reg(reg) + offset
            val = self.get_reg(operands[0])
            self.write_mem(addr, val)
        
        elif op == 'beq':
            val1 = self.get_reg(operands[0])
            val2 = self.get_reg(operands[1])
            if val1 == val2:
                self.pc = self.labels[operands[2]]
                return
        
        elif op == 'bne':
            val1 = self.get_reg(operands[0])
            val2 = self.get_reg(operands[1])
            if val1 != val2:
                self.pc = self.labels[operands[2]]
                return
        
        elif op == 'j':
            self.pc = self.labels[operands[0]]
            return
        
        elif op == 'jal':
            if operands[0] == 'print_int':
                val = self.get_reg('$a0')
                if val & 0x80000000:
                    val = val - 0x100000000
                print(val, end='')
            elif operands[0] == 'print_str':
                addr = self.get_reg('$a0')
                chars = []
                i = 0
                while True:
                    byte = self.memory.get(addr + i, 0)
                    if byte == 0:
                        break
                    chars.append(chr(byte))
                    i += 1
                print(''.join(chars), end='')
            else:
                self.set_reg('$ra', self.pc + 1)
                if operands[0] in self.labels:
                    self.pc = self.labels[operands[0]]
                    return
        
        elif op == 'jr':
            if operands[0] == '$ra':
                target = self.get_reg('$ra')
                if target == 0:
                    self.running = False
                    return
                self.pc = target
                return
        
        elif op == 'nop':
            pass
        
        self.pc += 1

def main():
    if len(sys.argv) < 2:
        print("Usage: mips_sim.py <program.asm>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        code = f.read()
    
    sim = MIPSInterpreter()
    sim.load_program(code)
    sim.run()

if __name__ == '__main__':
    main()