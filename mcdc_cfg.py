from mcdc_compile_blocks import get_blocks
from mcdc_disassm_blocks import process_file
from mcdc_tool_definitions import ASTEntry, BBInfo, BasicBlock, FunctionBlocks, BoolExpression
from mcdc_tool_dwarf import TracePoint, ExprTraceInfo
import logging
import argparse
import contextlib
from copy import copy
from dataclasses import dataclass
from pprint import pprint, pformat

log = logging.getLogger(__name__)

# TODO
log.setLevel(logging.DEBUG)


def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="MC/DC Control Flow Graph analyzer")
    parser.add_argument("executable", help="Path to the target executable file")
    parser.add_argument("compile_commands", help="Path to the compile_commands.json file")
    args = parser.parse_args()

    log.info("Decompilling...")
    decompiled = process_file(args.executable, None)
    log.info("Compilling...")
    compiled = get_blocks(args.compile_commands, None)

    for cu in compiled.keys():
        log.info(f"Processing CU {cu}")
        comp: BBInfo = compiled[cu]
        decomp: BBInfo = decompiled[cu]

        for comp_func in comp.function_blocks:
            log.info(f"  Processing function '{comp_func.function_name}'")
            decomp_func = decomp.find_function(comp_func.function_name)
            comparator = CFGComparator()
            res = comparator.compare_graphs(decomp_func.root_block, comp_func.root_block)
            log.info(f"  Equal: {res}")
            tps = comparator.get_trace_points()


@dataclass
class IncidenceEntry:
    idx: int
    comp: BasicBlock
    decomp: BasicBlock
    inverse: bool = False
    next_idx: int = None
    alt_idx: int = None

    @property
    def sast(self):
        return self.comp.sast

    @property
    def instr_range(self):
        return self.decomp.insns


class CFGComparator:

    def __init__(self):
        self.sast: SAST = None
        self.incidence: list[IncidenceEntry] = None

    def __reset_sast(self):
        self.sast = None

    def compare_graphs(self, decomp: BasicBlock, comp: BasicBlock) -> list[IncidenceEntry]:
        incidence = self.__build_incidence_list(decomp, comp, [])
        if incidence:
            self.__fill_incidence_indexes(incidence)
            log.debug(pformat(incidence))
            self.incidence = incidence
            return incidence
        return None

    def __collect_tps(self, ince: IncidenceEntry) -> list[TracePoint]:
        # TODO: Revisit this
        # We will do breath-first search (?)
        queue = [ince]
        ret = []
        while queue:
            i = queue[0]
            del queue[0]
            ret.append(TracePoint(i.instr_range[-1].address, i.inverse, i.comp.sast))
            if self.incidence[i.next_idx].comp.sast == i.comp.sast:
                queue.append(self.incidence[i.next_idx])
            if i.alt_idx and self.incidence[i.alt_idx].comp.sast == i.comp.sast:
                queue.append(self.incidence[i.alt_idx])
        return ret

    def get_trace_points(self) -> list[ExprTraceInfo]:
        ret = []
        for i in self.incidence:
            if i.sast and i.comp.sast_idx == 0:
                self.__tps = []
                num_entries = i.sast.get_leafs()
                log.debug(f"{i.sast=} expecing {num_entries=}")
                tps = self.__collect_tps(i)
                ret.append(ExprTraceInfo(i.sast, tps))
        return ret

    @staticmethod
    def __comp_in_incidence(bb: BasicBlock, incidence: list[IncidenceEntry]) -> bool:
        for i in incidence:
            if i.comp == bb:
                return True
        return False

    @staticmethod
    def __find_comp_in_incidence(bb: BasicBlock, incidence: list[IncidenceEntry]) -> bool:
        for idx, i in enumerate(incidence):
            if i.comp == bb:
                return idx
        raise LookupError(bb)

    @staticmethod
    def __find_decomp_in_incidence(bb: BasicBlock, incidence: list[IncidenceEntry]) -> bool:
        for idx, i in enumerate(incidence):
            if i.decomp == bb:
                return idx
        raise LookupError(bb)

    @staticmethod
    def __fill_incidence_indexes(incidence: list[IncidenceEntry]):
        for inc in incidence:
            if not inc.comp.next:
                continue
            next_comp = CFGComparator.__find_comp_in_incidence(inc.comp.next, incidence)
            if inc.inverse:
                next_decomp = CFGComparator.__find_decomp_in_incidence(inc.decomp.alt, incidence)
            else:
                next_decomp = CFGComparator.__find_decomp_in_incidence(inc.decomp.next, incidence)

            if next_comp != next_decomp:
                raise Exception(f"Index mismatch: {next_comp=} {next_decomp=}")
            inc.next_idx = next_comp

            if not inc.comp.alt:
                continue
            alt_comp = CFGComparator.__find_comp_in_incidence(inc.comp.alt, incidence)
            if inc.inverse:
                alt_decomp = CFGComparator.__find_decomp_in_incidence(inc.decomp.next, incidence)
            else:
                alt_decomp = CFGComparator.__find_decomp_in_incidence(inc.decomp.alt, incidence)

            if alt_comp != alt_decomp:
                raise Exception(f"Index mismatch: {next_comp=} {next_decomp=}")
            inc.alt_idx = alt_comp

    def __build_incidence_list(self, decomp: BasicBlock, comp: BasicBlock,
                               incidence: list[IncidenceEntry]) -> list[IncidenceEntry]:

        # Are we already been here?
        if self.__comp_in_incidence(comp, incidence):
            return incidence

        # Create own copy of the incidence list
        incidence = copy(incidence)

        # Put self in the incidence list
        own_entry = IncidenceEntry(len(incidence), comp, decomp)
        incidence.append(own_entry)

        log.debug(f"Comparing {decomp} to {comp}")
        if (decomp.next is None) != (comp.next is None):
            log.error(f"{decomp.next is None=} != {comp.next is None=}  ({decomp=} {comp=})")
            return None
        if (decomp.alt is None) != (comp.alt is None):
            log.error(f"{decomp.alt is None=} != {comp.alt is None=}  ({decomp=} {comp=})")
            return None
        next_fail = False
        alt_fail = False
        incidence_backup = incidence
        if decomp.next and comp.next:
            res = self.__build_incidence_list(decomp.next, comp.next, incidence)
            log.debug(f"{decomp=} {comp=} : NEXT: {res=}")
            if not res:
                next_fail = True
            else:
                incidence = res
        if decomp.alt and comp.alt:
            res = self.__build_incidence_list(decomp.alt, comp.alt, incidence)
            log.debug(f"{decomp=} {comp=} : ALT: {res=}")
            if not res:
                alt_fail = True
            else:
                incidence = res

        # All is good, we can return updated incidence list
        log.debug(f"{decomp=} {comp=} : {next_fail=} {alt_fail=}")
        if not next_fail and not alt_fail:
            return incidence

        # Try reversing the order
        if next_fail and alt_fail:
            next_fail = False
            alt_fail = False
            incidence = incidence_backup
            log.debug(f"Trying inverse for {decomp} and {comp}")
            res = self.__build_incidence_list(decomp.next, comp.alt, incidence)
            log.debug(f"{decomp=} {comp=} : NEXT2: {res=}")
            if not res:
                next_fail = True
            else:
                incidence = res

            res = self.__build_incidence_list(decomp.alt, comp.next, incidence)
            log.debug(f"{decomp=} {comp=} : ALT: {res=}")
            if not res:
                alt_fail = True
            else:
                incidence = res
            log.debug(f"{decomp=} {comp=} : {next_fail=} {alt_fail=}")

            if not next_fail and not alt_fail:
                own_entry.inverse = True
                return incidence

        return None


if __name__ == "__main__":
    main()
