import sys

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
    op = (instr >> 4) & 0xF
    opr = instr & 0xF
    rd = (opr >> 2) & 3
    rs = opr & 3
    if op == 0: return f"MOV R{rd},R{rs}"
    if op == 1: return f"ADDI R{rd},{opr&3}"
    if op == 2: return f"ADD R{rd},R{rs}"
    if op == 3: return f"LOAD R{rd},D{opr&3}"
    if op == 4: return f"STORE D{opr&3},R{rd}"
    if op == 5: return f"JMP {opr}"
    if op == 6: return f"JZ {opr}"
    if op == 7: return f"OUT R{rd}"
    return "????"

def cpu_step(reg, prog_mem, data_mem, pc, zf):
    instr = prog_mem[pc]
    op = (instr >> 4) & 0xF
    opr = instr & 0xF
    rd = (opr >> 2) & 3
    rs = opr & 3
    imm = opr & 3
    addr = opr & 0xF
    out_val = None
    halted = False
    jumped = False
    if op == 0:
        reg[rd] = reg[rs]
    elif op == 1:
        reg[rd] = (reg[rd] + imm) & 0xF
        zf = (reg[rd] == 0)
    elif op == 2:
        reg[rd] = (reg[rd] + reg[rs]) & 0xF
        zf = (reg[rd] == 0)
    elif op == 3:
        reg[rd] = data_mem[addr]
        zf = (reg[rd] == 0)
    elif op == 4:
        data_mem[addr] = reg[rd]
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
    return reg, data_mem, pc, zf, instr, out_val, halted

def bits4(val):
    return f"{val&0xF:04b}"

def run(program, max_cycles=200):
    prog_mem = [0] * 16
    for i, v in enumerate(program[:16]):
        prog_mem[i] = v & 0xFF
    data_mem = [0] * 16
    reg = [0, 0, 0, 0]
    pc = 0
    zf = False
    last_out = None
    cycle = 0
    while cycle < max_cycles:
        instr_now = prog_mem[pc]
        reg, data_mem, pc, zf, instr, out_val, halted = cpu_step(reg, prog_mem, data_mem, pc, zf)
        if out_val is not None:
            last_out = out_val
        cycle += 1
        reg_str = " ".join(f"R{i}={reg[i]}" for i in range(4))
        out_str = f"OUT={last_out}" if last_out is not None else "OUT=None"
        pc_before = (pc - 1) & 0xF if not (halted and (instr_now >> 4) == 5 and (instr_now & 0xF) == (pc - 1) & 0xF) else pc
        print(f"Step {cycle}  PC={pc_before}  {disasm(instr_now)}")
        print(f"Regs: {reg_str}  ZF={int(zf)}  {out_str}")
        prog_line = "Prog:"
        for i in range(16):
            if i == pc_before:
                prog_line += f" [{disasm(prog_mem[i])}]"
            else:
                prog_line += f" {disasm(prog_mem[i])}"
        print(prog_line)
        data_line = "Data:" + "".join(f" {data_mem[i]:2d}" for i in range(16))
        print(data_line)
        sys.stdout.flush()
        if halted:
            print("HALTED")
            break
        input()
    print("Done. Press Enter to exit.", end="")
    input()

def make_add_3_5():
    return [enc_addi(0,3), enc_addi(1,3), enc_addi(1,2), enc_add(0,1), enc_out(0), enc_jmp(5)]

def make_countdown():
    return [enc_addi(0,3), enc_addi(1,3), enc_addi(1,3), enc_addi(1,3), enc_addi(1,3), enc_addi(1,3), enc_out(0), enc_add(0,1), enc_jz(10), enc_jmp(6), enc_out(0), enc_jmp(11)]

def make_store_load():
    return [enc_addi(0,3), enc_addi(0,3), enc_store(0,3), enc_addi(0,1), enc_load(2,3), enc_add(0,2), enc_out(0), enc_jmp(7)]

PROGRAMS = {
    "1": ("Add 3+5, output 8", make_add_3_5),
    "2": ("Countdown 3..0", make_countdown),
    "3": ("Store/load, output 13", make_store_load),
}

if __name__ == "__main__":
    print("\nTiny RISC-4 CPU Simulator (Harvard architecture)")
    print("=" * 44)
    for k, (name, _) in PROGRAMS.items():
        print(f"  {k}) {name}")
    choice = input("\nChoose (1): ").strip() or "1"
    _, prog_fn = PROGRAMS.get(choice, PROGRAMS["1"])
    run(prog_fn())

