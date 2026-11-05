from __future__ import annotations
from pprint import pprint
import argparse
import json
import multiprocessing
import os
import subprocess
from dataclasses import dataclass, fields
from typing import Unpack
from copy import copy

from mcdc_tool_definitions import ASTEntry, BBInfo, BasicBlock, FunctionBlocks, SAST, BoolExpression, BoolVar, NonBoolExpression

import mcdc_tool_parser


def main():
    parser = argparse.ArgumentParser(description="MC/DC AST Block Generator")

    parser.add_argument("compile_commands", help="Path to the compile_commands.json file")
    parser.add_argument("-c", "--compile_unit", help="Compile Unit to process")

    args = parser.parse_args()

    blocks = get_blocks(args.compile_commands, args.compile_unit)


SOURCE_SKIP_LIST = []


def get_blocks(compile_commands: str, compile_unit: str = None) -> dict(str, BBInfo):
    compilation_db = open(compile_commands, "rt")
    db = json.load(compilation_db)
    seen = []

    async_results: list[(str, multiprocessing.AsyncResult)] = []

    ret = {}
    with multiprocessing.Pool() as pool:
        for entry in db:
            f: str = entry["file"]
            work_dir: str = entry.get("directory", os.getcwd())
            rel_f: str = os.path.relpath(f, work_dir)

            if compile_unit and compile_unit != rel_f:
                continue
            if not f.endswith(".c"):
                continue
            if rel_f.startswith("tools/"):
                continue
            if rel_f in SOURCE_SKIP_LIST:
                continue
            args = entry["arguments"]
            if f in seen:
                continue
            seen.append(f)
            async_results.append((rel_f, pool.apply_async(handle_file, (rel_f, args))))

        print("Collecting async results...")
        for ar in async_results:
            bbinfo: BBInfo = ar[1].get()
            # for e in mcdcinfo.expressions:
            #     assert isinstance(e, BoolExpression)
            ret[bbinfo.compile_unit] = bbinfo
            for fb in bbinfo.function_blocks:
                dump_to_dot(fb.function_name + "_comp", fb.function_name, fb.root_block)
    return ret


def handle_file(fname: str, args: list[str]) -> BBInfo:

    def object_hook(data: dict):
        if "kind" in data:
            return ASTEntry(data)
        return data

    print(f"Parsing '{fname}'")

    ast_args = args.copy()

    if "-save-temps" in ast_args:
        ast_args.remove("-save-temps")
    ast_args.append("-Xclang")
    ast_args.append("-ast-dump=json")
    ast_args.append("-fsyntax-only")

    if "-c" in ast_args:
        ast_args.remove("-c")

    if "-S" in ast_args:
        ast_args.remove("-S")

    if "-o" in ast_args:
        pos = ast_args.index("-o")
        del ast_args[pos:pos + 2]
    print(ast_args)
    result = subprocess.run(ast_args, capture_output=True, check=True)
    data = json.loads(result.stdout, object_hook=object_hook)
    data.update_locations(fname, 1)
    return BBInfo(fname, process_root(data))


def process_root(root: ASTEntry) -> list[FunctionBlocks]:
    functions: list[FunctionBlocks] = []
    for ast in root.inner:
        if ast.kind == "FunctionDecl":
            functions.append(handle_function(ast))
    return functions


def dump_to_dot(fname: str, func_name: str, block: BasicBlock):
    dot = open(fname + ".dot", "wt")
    seen_blocks = set()

    def recurse(block: BasicBlock):
        if block.id in seen_blocks:
            return
        seen_blocks.add(block.id)

        dot.write(f'\t"{block.id}" [label="{block.type}"]\n')
        edges = f'\t"{block.id}"'
        if block.next:
            edges += f' -> "{block.next.id}" [taillabel="next"]'
            if not block.next.id in seen_blocks:
                recurse(block.next)
        edges += "\n"
        dot.write(edges)
        if block.alt:
            edges = f'\t"{block.id}"'
            edges += f' -> "{block.alt.id}" [taillabel="alt"]'
            if not block.alt.id in seen_blocks:
                recurse(block.alt)
            edges += "\n"
            dot.write(edges)

    dot.write(f"digraph {func_name} {{\n")
    recurse(block)
    dot.write("}\n")
    dot.close()


def handle_function(ast: ASTEntry) -> FunctionBlocks:
    cfg = CFGBuilder()
    root_block = cfg.process_ast(ast)

    #TODO?
    #    root_block.try_merge()
    return FunctionBlocks(ast, ast.data["name"], root_block)


@dataclass
class LogicOp:
    rhs: BasicBlock
    lhs: BasicBlock
    sast: SAST
    sast_idx = 0


class CFGBuilder:

    def __init__(self):
        self.cur: Optional[BasicBlock] = None
        self.next: Optional[BasicBlock] = None
        self.function_epilogue: Optional[BasicBlock] = None
        self.__next: list[BasicBlock] = []

    def push_next(self, next: Optional[BasicBlock] = None):
        self.__next.append(self.next)
        if next:
            self.next = next

    def pop_next(self):
        self.next = self.__next.pop()

    def insert_block(self, block: BasicBlock, set_next=True):
        if set_next:
            self.next = self.cur
        self.cur = block

    def process_ast(self, ast: ASTEntry) -> BasicBlock:
        assert ast.kind == "FunctionDecl"

        # Initialize the epilogue block
        self.function_epilogue = BasicBlock("epilogue")
        self.cur = self.function_epilogue

        for x in reversed(ast.inner):
            self.process(x)

        if self.cur:
            return self.cur
        return self.next

    def process_return(self, ast: ASTEntry):
        assert ast.kind == "ReturnStmt"
        # Maybe, we need to create a new block
        if self.cur != self.function_epilogue:
            block = BasicBlock("block_w_ret", None, self.function_epilogue)
            self.insert_block(block, set_next=False)
        else:
            block = self.cur

        # Process return value (if any)
        if ast.inner[0]:
            self.process(ast.inner[0])

        return block

    def process_compound_stmt(self, ast: ASTEntry):
        for child in reversed(ast.inner):
            self.process(child)
        return self.cur

    def process_if(self, ast: ASTEntry):
        # End the current block
        self.next = self.cur

        # Create false and then true branches. Both are pointing to the previous block.
        # New block for false branch
        false_block = False
        if len(ast.inner) == 3:
            self.cur = None
            self.push_next()
            false_block = self.process(ast.inner[2])
            self.pop_next()
            self.insert_block(false_block, set_next=False)
            false_block.type = f"false_branch({false_block.type})"
            false_block.next = self.next
        if not false_block:
            # Create dummy block
            # TODO: This was done to fix the problem with compiler that generates some code for else branch
            # even if there is no else branch.
            false_block = BasicBlock("dummy_false", None, self.next)
            # false_block = self.next

        # New block for true branch
        self.cur = None
        self.push_next()
        true_block = self.process(ast.inner[1])
        self.pop_next()
        self.insert_block(true_block, set_next=False)
        true_block.type = f"true_branch({true_block.type})"
        true_block.next = self.next
        #Now handle condition

        # Special case: if (a && ..) or if (a || ...)
        cond_op = ast.inner[0]
        if cond_op.is_logic_op():
            op_info = self.process_logic_op(cond_op, true_block, false_block)
            cond_block = op_info.rhs
        else:
            cond_block = BasicBlock("if", None, true_block, false_block)

        self.insert_block(cond_block, set_next=False)
        return cond_block

    def process_logic_op(self, ast: ASTEntry, true_block: BasicBlock,
                         false_block: BasicBlock) -> LogicOp:
        rhs = ast.inner[0]
        if rhs.is_logic_op():
            # TODO: Recurse in
            raise NotImplementedError()
        else:
            # TODO: This is not always a var
            rhs_sast = BoolVar(rhs.get_loc(), "TODO", rhs)
        # TODO: Use self.next right here?
        rhsblock = BasicBlock("rhs")
        # TODO: Update based on top-level SAST, somehow
        rhsblock.sast_idx = 0
        lhs = ast.inner[1]
        if lhs.is_logic_op():
            # TODO: Recurse in
            raise NotImplementedError()
        else:
            # TODO: This is not always a var
            lhs_sast = BoolVar(lhs.get_loc(), "TODO", lhs)
        # TODO: Use self.next right here?
        lhsblock = BasicBlock("lhs")
        # TODO: Update based on top-level SAST, somehow
        lhsblock.sast_idx = 1
        # TODO: Add option to pass/extend it on lower recursion levels
        sast = BoolExpression(ast.get_loc(), ast, rhs_sast,
                              BoolExpression.from_opcode(ast.data["opcode"]), lhs_sast)
        rhsblock.sast = sast
        lhsblock.sast = sast
        match ast.data["opcode"]:
            case "&&":
                rhsblock.next = lhsblock
                rhsblock.alt = false_block
                lhsblock.next = true_block
                lhsblock.alt = false_block
            case "||":
                rhsblock.next = true_block
                rhsblock.alt = lhsblock
                lhsblock.next = true_block
                lhsblock.alt = false_block
            case "!":
                raise NotImplementedError()
            case _:
                assert False
        return LogicOp(rhsblock, lhsblock, sast)

    def process_simple(self, ast: ASTEntry):
        for x in reversed(ast.inner):
            self.process(x)
        return self.cur

    def process(self, ast: ASTEntry) -> Optinal[BasicBlock]:
        print(f"Processing {ast.kind} at {ast.get_loc()}")

        handler = CFGBuilder.__handlers.get(ast.kind)
        if handler:
            return handler(self, ast)
        else:
            print(f"Don't know how to parse {ast.kind}")
            pprint(ast.data)
            raise NotImplementedError(f"Don't know how to parse {ast.kind}")

    def process_nop(self, ast: ASTEntry):
        return self.cur

    __handlers = {
        "ParmVarDecl": process_nop,
        "NoThrowAttr": process_nop,
        "NonNullAttr": process_nop,
        "RestrictAttr": process_nop,
        "BuiltinAttr": process_nop,
        "FormatAttr": process_nop,
        "AsmLabelAttr": process_nop,
        "ColdAttr": process_nop,
        "IntegerLiteral": process_nop,
        "ReturnStmt": process_return,
        "CompoundStmt": process_compound_stmt,
        "IfStmt": process_if,
        "CallExpr": process_simple,
        "ImplicitCastExpr": process_simple,
        "DeclRefExpr": process_simple,
    }


if __name__ == "__main__":
    main()
