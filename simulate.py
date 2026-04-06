import sys

# Instruction set
#
#  8-bit instruction word: [opcode 4 bits | operand 4 bits]
#
#  Opcode  Mnemonic   Operand layout      Effect
#  0       MOV        [rd:2][rs:2]        reg[rd] = reg[rs]
#  1       ADDI       [rd:2][imm:2]       reg[rd] = (reg[rd] + imm) & 0xF   imm 0-3
#  2       ADD        [rd:2][rs:2]        reg[rd] = (reg[rd] + reg[rs]) & 0xF
#  3       LOAD       [rd:2][addr:2]      reg[rd] = mem[addr]
#  4       STORE      [rd:2][addr:2]      mem[addr] = reg[rd]
#  5       JMP        [addr:4]            pc = addr (unconditional)
#  6       JZ         [addr:4]            if zero_flag: pc = addr
#  7       OUT        [rd:2][00]          display reg[rd]
#
#  Registers: R0-R3, each 4-bit.
#  Memory:    16 locations, each 8-bit (holds instructions or data).
#  Flags:     zero_flag set after ADDI, ADD, LOAD when result == 0.
#  Halt:      JMP to its own address (self-loop).

def enc_mov(rd, rs):
    return (0 << 4) | ((rd & 3) << 2) | (rs & 3)

def enc_addi(rd, imm):
    return (1 << 4) | ((rd & 3) << 2) | (imm & 3)

def enc_add(rd, rs):
    return (2 << 4) | ((rd & 3) << 2) | (rs & 3)

def enc_load(rd, addr):
    return (3 << 4) | ((rd & 3) << 2) | (addr & 3)

def enc_store(rd, addr):
    return (4 << 4) | ((rd & 3) << 2) | (addr & 3)

def enc_jmp(addr):
    return (5 << 4) | (addr & 0xF)

def enc_jz(addr):
    return (6 << 4) | (addr & 0xF)

def enc_out(rd):
    return (7 << 4) | ((rd & 3) << 2)

def disasm(instr):
    op  = (instr >> 4) & 0xF
    opr = instr & 0xF
    rd  = (opr >> 2) & 3
    rs  = opr & 3
    if op == 0: return f"MOV   R{rd}, R{rs}"
    if op == 1: return f"ADDI  R{rd}, {opr & 3}"
    if op == 2: return f"ADD   R{rd}, R{rs}"
    if op == 3: return f"LOAD  R{rd}, [mem{opr & 3}]"
    if op == 4: return f"STORE [mem{opr & 3}], R{rd}"
    if op == 5: return f"JMP   {opr}"
    if op == 6: return f"JZ    {opr}"
    if op == 7: return f"OUT   R{rd}"
    return "????"

def cpu_step(reg, mem, pc, zf):
    instr = mem[pc]
    op  = (instr >> 4) & 0xF
    opr = instr & 0xF
    rd  = (opr >> 2) & 3
    rs  = opr & 3
    imm  = opr & 3
    addr = opr & 0xF
    out_val = None
    halted  = False
    jumped  = False
    if op == 0:
        reg[rd] = reg[rs]
    elif op == 1:
        reg[rd] = (reg[rd] + imm) & 0xF
        zf = (reg[rd] == 0)
    elif op == 2:
        reg[rd] = (reg[rd] + reg[rs]) & 0xF
        zf = (reg[rd] == 0)
    elif op == 3:
        reg[rd] = mem[addr]
        zf = (reg[rd] == 0)
    elif op == 4:
        mem[addr] = reg[rd]
    elif op == 5:
        if addr == pc:
            halted = True
        else:
            pc = addr
            jumped = True
    elif op == 6:
        if zf:
            pc = addr
            jumped = True
    elif op == 7:
        out_val = reg[rd]
    if not jumped and not halted:
        pc = (pc + 1) & 0xF
    return reg, mem, pc, zf, instr, out_val, halted

OPNAMES = ["MOV ","ADDI","ADD ","LOAD","STOR","JMP ","JZ  ","OUT "]

def bits4(val):
    return format(val & 0xF, "04b")

def render_frame(reg, mem, pc, zf, last_out, instr, cycle, halted):
    op  = (instr >> 4) & 0xF
    opr = instr & 0xF
    opname = OPNAMES[op] if op < len(OPNAMES) else "????"
    w = 56
    def row(content):
        return f"  \u2551  {content:<{w-4}}  \u2551"
    out = []
    out.append("")
    out.append(f"  \u2554{'':=<{w}}\u2557")
    out.append(f"  \u2551{'Tiny RISC-4 CPU':^{w}}\u2551")
    out.append(f"  \u2560{'':=<{w}}\u2563")
    out.append(row(f"Cycle: {cycle:>4}    PC: {pc:02d} [{bits4(pc)}]    ZF: {int(zf)}"))
    out.append(f"  \u2560{'':=<{w}}\u2563")
    reg_str = "  ".join(f"R{i}:[{bits4(v)}] ({v:2d})" for i, v in enumerate(reg))
    out.append(row(f"Registers:  {reg_str}"))
    out.append(f"  \u2560{'':=<{w}}\u2563")
    out.append(row(f"Fetched:  0x{instr:02X}  =  [{bits4(op)}|{bits4(opr)}]"))
    out.append(row(f"          opcode={op} ({opname})  operand={opr} [{bits4(opr)}]"))
    out.append(row(f"Decoded:  {disasm(instr)}"))
    out.append(f"  \u2560{'':=<{w}}\u2563")
    hdr = " ".join(f"{i:>3}" for i in range(16))
    out.append(row(f"mem:  {hdr}"))
    cells = []
    for i, m in enumerate(mem):
        cell = f"{m:02X}"
        if i == pc:
            cell = f"\033[7m{cell}\033[0m"
        cells.append(f"{cell:>3}")
    dat = " ".join(cells)
    out.append(row(f"      {dat}"))
    out.append(f"  \u2560{'':=<{w}}\u2563")
    out_str = f"{last_out:2d}  [{bits4(last_out)}]" if last_out is not None else "  (none)"
    out.append(row(f"Output display: {out_str}"))
    status = "HALTED" if halted else "running"
    out.append(row(f"Status: {status}"))
    out.append(f"  \u255a{'':=<{w}}\u255d")
    out.append("")
    return "\n".join(out)

def run(program, max_cycles=200):
    mem = [0] * 16
    for i, v in enumerate(program[:16]):
        mem[i] = v & 0xFF
    reg      = [0, 0, 0, 0]
    pc       = 0
    zf       = False
    last_out = None
    cycle    = 0
    print("\033[2J\033[H", end="")
    while cycle < max_cycles:
        instr_now = mem[pc]
        reg, mem, pc, zf, instr, out_val, halted = cpu_step(reg, mem, pc, zf)
        if out_val is not None:
            last_out = out_val
        cycle += 1
        frame = render_frame(reg, mem, pc, zf, last_out, instr_now, cycle, halted)
        print("\033[H", end="")
        print(frame)
        sys.stdout.flush()
        if halted:
            break
        input()
    print("\nExecution finished. Press Enter to exit.", end="")
    input()

def make_add_3_5():
    return [
        enc_addi(0, 3),
        enc_addi(1, 3),
        enc_addi(1, 2),
        enc_add(0, 1),
        enc_out(0),
        enc_jmp(5),
    ]

def make_countdown():
    return [
        enc_addi(0, 3),
        enc_addi(1, 3),
        enc_addi(1, 3),
        enc_addi(1, 3),
        enc_addi(1, 3),
        enc_addi(1, 3),
        enc_out(0),
        enc_add(0, 1),
        enc_jz(10),
        enc_jmp(6),
        enc_out(0),
        enc_jmp(11),
    ]

def make_store_load():
    return [
        enc_addi(0, 3),
        enc_addi(0, 3),
        enc_store(0, 3),
        enc_addi(0, 1),
        enc_load(2, 3),
        enc_add(0, 2),
        enc_out(0),
        enc_jmp(7),
    ]

PROGRAMS = {
    "1": ("Add 3 + 5, output 8",                  make_add_3_5),
    "2": ("Countdown 3 to 0, output each step",   make_countdown),
    "3": ("Store to memory, load it, output 13",  make_store_load),
}

if __name__ == "__main__":
    print("\n  Tiny RISC-4 CPU Simulator (step on Enter)")
    print("  " + "=" * 36)
    for k, (name, _) in PROGRAMS.items():
        print(f"  {k}) {name}")
    print()
    choice = input("  Choose program (1): ").strip() or "1"
    _, prog_fn = PROGRAMS.get(choice, PROGRAMS["1"])
    print()
    run(prog_fn())
