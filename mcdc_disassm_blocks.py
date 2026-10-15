from __future__ import annotations

import capstone
import cle
import logging
import argparse
import os
from mcdc_tool_definitions import ASTEntry, BBInfo, BasicBlock, FunctionBlocks
from pprint import pprint
from dataclasses import dataclass

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


@dataclass
class BlockData:
    start: int
    end: int
    insns: list[capstone.CsInsn]

    def __repr__(self) -> str:
        return f"<BlockData 0x{self.start:x} - 0x{self.end:x} ({len(self.insns)} instructions)>"


RET_INSTR = {capstone.arm64.ARM64_INS_RET}
GOTO_INSTR = {capstone.arm64.ARM64_INS_B, capstone.arm64.ARM64_INS_BR}
CMP_AND_BR_INSTR = {
    capstone.arm64.ARM64_INS_CBZ, capstone.arm64.ARM64_INS_CBNZ, capstone.arm64.ARM64_INS_TBZ,
    capstone.arm64.ARM64_INS_TBNZ
}
COND_SET_INSTR = {
    # Conditional sets
    capstone.arm64.ARM64_INS_CSEL,
    capstone.arm64.ARM64_INS_CSET,
    capstone.arm64.ARM64_INS_CSINC,
    capstone.arm64.ARM64_INS_CINV,
    capstone.arm64.ARM64_INS_CSNEG,
    capstone.arm64.ARM64_INS_CSINV,

    # Conditional swaps
    capstone.arm64.ARM64_INS_CASA,
    capstone.arm64.ARM64_INS_CASAL,
    capstone.arm64.ARM64_INS_CAS,
    capstone.arm64.ARM64_INS_CASL,
    capstone.arm64.ARM64_INS_CASAB,
    capstone.arm64.ARM64_INS_CASALB,
    capstone.arm64.ARM64_INS_CASB,
    capstone.arm64.ARM64_INS_CASLB,
    capstone.arm64.ARM64_INS_CASAH,
    capstone.arm64.ARM64_INS_CASALH,
    capstone.arm64.ARM64_INS_CASH,
    capstone.arm64.ARM64_INS_CASLH,
    capstone.arm64.ARM64_INS_CASPA,
    capstone.arm64.ARM64_INS_CASPAL,
    capstone.arm64.ARM64_INS_CASP,
    capstone.arm64.ARM64_INS_CASPL,
    capstone.arm64.ARM64_INS_CASPA,
    capstone.arm64.ARM64_INS_CASPAL,
    capstone.arm64.ARM64_INS_CASP,
    capstone.arm64.ARM64_INS_CASPL,
}
#TODO: Add Pauth variants
FCALL_INSTR = {capstone.arm64.ARM64_INS_BL, capstone.arm64.ARM64_INS_BLR}

EOB_INSTR = RET_INSTR | GOTO_INSTR | COND_SET_INSTR | FCALL_INSTR | CMP_AND_BR_INSTR


def collect_groups(insn: capstone.CsInsn) -> str:
    return "[" + " ".join([insn.group_name(x) for x in insn.groups]) + "]"


def split_into_blocks(insns: list[capstone.CsInsn]) -> list[BlockData]:
    ret: list[BlockData] = []
    cur: list[capstone.CsInsn] = []
    for insn in insns:
        cur.append(insn)
        if insn.id in EOB_INSTR:
            ret.append(BlockData(cur[0].address, cur[-1].address, cur))
            cur = []
    return ret


def get_block_by_addr(blocks: list[BasicBlock], addr: int) -> BasicBlock:
    for block in blocks:
        start = block.insns[0].address
        end = block.insns[-1].address
        if addr >= start and addr <= end:
            return block
    raise Exception(f"Can't find basic block for address 0x{addr:x}")


def link_blocks(blocks: list[BlockData]) -> list[BasicBlock]:
    ret: list[BasicBlock] = []
    prev: BasicBlock = None

    # First pass: link blocks in natural order
    for block in blocks:
        new_block = BasicBlock(None, "disassm", insns=block.insns)

        insn_id = new_block.insns[-1].id
        cc_id = new_block.insns[-1].cc

        if insn_id in RET_INSTR:
            new_block.type = "return"

        ret.append(new_block)
        if prev:
            prev.next = new_block

        prev = new_block

    # Second pass: fixup plain "b" instructions
    for block in ret:
        insn_id = block.insns[-1].id
        cc_id = block.insns[-1].cc
        if cc_id == capstone.arm64_const.ARM64_CC_INVALID and \
           insn_id == capstone.arm64_const.ARM64_INS_B:
            addr = block.insns[-1].operands[0].value.imm
            print(f"{block.insns[-1].address:x}: b addr is 0x{addr:x}")
            block.next = get_block_by_addr(ret, addr)

    # Third pass: handle conditionals
    # (probably can be folded in the second pass)
    for block in ret:
        insn_id = block.insns[-1].id
        cc_id = block.insns[-1].cc
        if cc_id != capstone.arm64_const.ARM64_CC_INVALID and \
           insn_id == capstone.arm64_const.ARM64_INS_B:
            addr = block.insns[-1].operands[0].value.imm
            print(f"{block.insns[-1].address:x}: b.<cond> addr is 0x{addr:x}")
            block.alt = get_block_by_addr(ret, addr)

        elif insn_id in CMP_AND_BR_INSTR:
            match insn_id:
                case capstone.arm64_const.ARM64_INS_CBZ | capstone.arm64_const.ARM64_INS_CBNZ:
                    op_idx = 1
                case capstone.arm64_const.ARM64_INS_TBZ | capstone.arm64_const.ARM64_INS_TBNZ:
                    op_idx = 2
                case _:
                    raise NotImplementedError(f"Unknown instruction: {block.insns[-1]}")
            addr = block.insns[-1].operands[op_idx].value.imm
            print(f"{block.insns[-1].address:x}: tbz/cbz addr is 0x{addr:x}")
            block.alt = get_block_by_addr(ret, addr)

        elif insn_id in COND_SET_INSTR:
            new_block = BasicBlock(None, "cont_instr", next=block.next)
            new_block.insns = block.insns
            block.alt = new_block
        elif insn_id == capstone.arm64_const.ARM64_INS_BR:
            raise NotImplementedError("Don't know how to handle BR :(")

    return ret


def process_func(loader: cle.Loader, func: cle.backends.elf.subprogram):
    data = loader.memory.load(func.low_pc, func.high_pc - func.low_pc)
    dis = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
    dis.detail = True
    insns: list[capstone.CsInsn] = list(dis.disasm(data, func.low_pc))
    blocks = split_into_blocks(insns)
    blocks = link_blocks(blocks)
    for block in blocks:
        print(block)


#        for i in block.insns:
#            print(i)
    dump_to_dot(func.name, func.name, blocks)


def dump_to_dot(fname: str, func_name: str, blocks: list[BasicBlock]):
    dot = open(fname + ".dot", "wt")
    seen_blocks = set()

    def recurse(block: BasicBlock):
        if block.id in seen_blocks:
            return
        seen_blocks.add(block.id)
        start = block.insns[0].address
        end = block.insns[-1].address

        dot.write(f'\t"{block.id}" [label="{block.type}:0x{start:x}-0x{end:x}"]\n')
        edges = f'\t"{block.id}"'
        if block.next:
            edges += f' -> "{block.next.id}"'
            if not block.next.id in seen_blocks:
                recurse(block.next)
        if block.alt:
            edges += f' -> "{block.alt.id}"'
            if not block.alt.id in seen_blocks:
                recurse(block.alt)
        edges += "\n"
        dot.write(edges)

    dot.write(f"digraph {func_name} {{\n")
    for block in blocks:
        recurse(block)
    dot.write("}\n")
    dot.close()


def process_file(fname: str, cu_name: str = None) -> BBInfo:
    loader = cle.Loader(fname, load_debug_info=True)
    elfe = loader.all_elf_objects[0]

    for cu in elfe.compilation_units:
        if os.path.basename(cu.name) in ("unwind-dw2.c", "unwind-dw2-fde-dip.c",
                                         "__aarch64_have_sme.c", "unwind-c.c", "lse-init.c",
                                         "lse.S", "__arm_za_disable.S", "__arm_tpidr2_save.S",
                                         "unordtf2.c", "sfp-exceptions.c", "letf2.c"):
            # Nothing good in libgcc internals
            continue
        print(f"{cu.name=}")
        if cu_name and cu_name != cu.name:
            continue
        for addr, func in cu.functions.items():
            if func.name in ("startup_cpu_idle_loop", "continue_new_vcpu", "efi_get_time",
                             "start_xen", "__div0"):
                continue
            print(f"Function @{addr:x} {func.name}")
            process_func(loader, func)


def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="MC/DC Dwarf basic block decompiler")

    parser.add_argument("executable", help="Path to the target executable file")

    parser.add_argument("-c", "--compile_unit", help="Compile Unit to process")

    args = parser.parse_args()

    process_file(args.executable, args.compile_unit)


if __name__ == "__main__":
    main()
