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

from mcdc_tool_definitions import ASTEntry, BBInfo, BasicBlock, FunctionBlocks


def main():
    parser = argparse.ArgumentParser(description="MC/DC AST Block Generator")

    parser.add_argument("compile_commands", help="Path to the compile_commands.json file")
    parser.add_argument("-c", "--compile_unit", help="Compile Unit to process")

    args = parser.parse_args()

    blocks = get_blocks(args.compile_commands, args.compile_unit)


SOURCE_SKIP_LIST = []


def get_blocks(compile_commands: str, compile_unit: str = None) -> dict(str, MCDCExprInfo):
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


@dataclass
class BuildState:
    prev: BasicBlock
    end: BasicBlock
    epilogue: BasicBlock
    true_outcome: BasicBlock = None
    false_outcome: BasicBlock = None

    def derive(self, **kwargs: Unpack[BuildState]):
        ret = copy(self)
        for field in fields(self):
            if field.name in kwargs:
                ret.__dict__[field.name] = kwargs[field.name]
                del kwargs[field.name]

        if kwargs:
            raise Exception(f"Unknown values left in kwargs: {kwargs}")

        return ret


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
    recurse(block)
    dot.write("}\n")
    dot.close()


def handle_function(ast: ASTEntry) -> FunctionBlocks:
    blocks: list[BasicBlock] = []
    entry = BasicBlock(ast, "entry")
    epilogue = BasicBlock(ast, "exit")
    state = BuildState(entry, epilogue, epilogue)
    for child in ast.inner:
        state = process_ast(child, state)
    return FunctionBlocks(ast, ast.data["name"], entry)


def handle_binary_operator(ast: ASTEntry, state: BuildState) -> BuildState:
    assert ast.kind == "BinaryOperator"
    op_code = ast.data["opcode"]
    match op_code:
        case "&&":
            new_state = process_ast(ast.inner[0], state)

            # Create a new block for the second expression
            block = BasicBlock(ast, op_code)
            new_state = new_state.derive(current=block)
            new_state = process_ast(ast.inner[1], new_state)
            block = BasicBlock(ast, op_code)
        case "||":
            left = process_ast(ast.inner[0])
            right = process_ast(ast.inner[1])
            block = BasicBlock(ast, op_code)
            pass
        case _:
            pprint(ast.data)
            raise NotImplementedError("OOPS")
    raise NotImplementedError("OOPS")
    return []


def handle_if(ast: ASTEntry, state: BuildState) -> BuildState:
    true_block = BasicBlock(ast, "true_branch", state.end)
    false_block = BasicBlock(ast, "false_branch", state.end)
    test_block = BasicBlock(ast.inner[0], "test_block", state.end)
    state = state.derive(true_outcome=true_block, false_outcome=false_block)
    return state


def process_ast(ast: ASTEntry, state: BuildState) -> BuildState:
    print(f"Procesing {ast.kind=}")
    match ast.kind:
        case "ParmVarDecl" | "NoThrowAttr" | "NonNullAttr" | "RestrictAttr" | "BuiltinAttr":
            # "Function info" stuff
            return state
        case "FormatAttr" | "AsmLabelAttr" | "ColdAttr":
            # ... continues
            return state
        case "IfStmt":
            return handle_if(ast, state)
        case "ReturnStmt":
            # After computing statement we are going
            # right to the exit of the function
            new_state = process_ast(ast.inner[0], state)
            new_state.prev.next = new_state.epilogue
            return new_state
        case "CompoundStmt" | "ImplicitCastExpr":
            new_state = state
            for child in ast.inner:
                new_state = process_ast(child, new_state)
                # TODO: update links?
            return new_state
        case "BinaryOperator":
            return handle_binary_operator(ast, state)
        case "IntegerLiteral":
            return state
        case "CallExpr":
            return state
        case _:
            print(f"Don't know how to parse {ast.kind}")
            pprint(ast.data)
            raise NotImplementedError(f"Don't know how to parse {ast.kind}")
            return next


if __name__ == "__main__":
    main()
