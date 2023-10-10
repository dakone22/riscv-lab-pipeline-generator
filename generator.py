import csv
import os
import sys
from pathlib import Path

from typing import List

from parsing.tabular_list import parse


def average_signal_data_by_tick(data):
    data_index_by_cyc_cnt = {}

    for index, cyc_cnt in enumerate(data["/tb/cyc_cnt"]):
        if cyc_cnt.isnumeric():
            tick = int(cyc_cnt, 2)
            if tick not in data_index_by_cyc_cnt.keys():
                data_index_by_cyc_cnt[tick] = list()
            data_index_by_cyc_cnt[tick].append(index)

    data_index_list = sorted(data_index_by_cyc_cnt.items(), key=lambda item: item[0])

    return [(cyc_cnt, index_list[len(index_list) // 2]) for cyc_cnt, index_list in data_index_list]


class CommandProcessingManager:
    def __init__(self):
        self.completed_commands: List[CommandProcessing] = []
        self.active_commands: List[CommandProcessing] = []
        self.current_tick = 0

    def set_tick(self, tick: int):
        self.current_tick = tick

    def new_fetch(self, address: int, id: int):
        command = CommandProcessing(address, id)
        command.fetch(self.current_tick)
        self.active_commands.append(command)

    def _find_command(self, address: int, id: int):
        for command in self.active_commands:
            if command.address == address and command.id == id:
                return command
        raise Warning(f"Not find command <pc={hex(address)}, id={id}>!")

    def dispatching_complete(self, address: int, id: int, instruction: int):
        command = self._find_command(address, id)
        if not command:
            raise Exception(f"Tried to dispatch command <pc={hex(address)}, id={id}>, but not found it!")

        command.dispatch(self.current_tick, instruction)

    def decoding(self, address: int, id: int, wait: bool):
        command = self._find_command(address, id)
        if not command:
            raise Exception(f"Tried to decode command <pc={hex(address)}, id={id}>, but not found it!")

        command.decode(self.current_tick, wait)

    def issue_conflict(self, address: int, id: int):
        command = self._find_command(address, id)
        if not command:
            raise Exception(f"Tried to issue_conflict command <pc={hex(address)}, id={id}>, but not found it!")

        command.issue_conflict(self.current_tick)

    def issue_bu(self, address: int, id: int):
        command = self._find_command(address, id)
        if not command:
            raise Exception(f"Tried to issue_bu command <pc={hex(address)}, id={id}>, but not found it!")

        command.issue_bu(self.current_tick)
        self.completed_commands.append(self.active_commands.pop(self.active_commands.index(command)))

    def issue_alu(self, address: int, id: int):
        command = self._find_command(address, id)
        if not command:
            raise Exception(f"Tried to issue_alu command <pc={hex(address)}, id={id}>, but not found it!")

        command.issue_alu(self.current_tick)
        self.completed_commands.append(self.active_commands.pop(self.active_commands.index(command)))

    def issue_lsu(self, address: int, id: int):
        command = self._find_command(address, id)
        if not command:
            raise Exception(f"Tried to issue_lsu command <pc={hex(address)}, id={id}>, but not found it!")

        command.issue_lsu(self.current_tick)
        self.completed_commands.append(self.active_commands.pop(self.active_commands.index(command)))

    def flush(self):
        for command in self.active_commands:
            command.cancel(self.current_tick)
        self.completed_commands.extend(self.active_commands)
        self.active_commands.clear()


class CommandProcessing:
    def __init__(self, address: int, id: int):
        self.address = address
        self.instruction: int = 0
        self.id = id
        self.stage = "fetching"
        self.history = {}

    def _fill_wait_gap(self, tick):
        for t in range(max(self.history.keys()) + 1, tick):
            self.history[t] = "W"

    def cancel(self, tick):
        self._fill_wait_gap(tick)

        if tick in self.history.keys() and (self.history[tick] == "D" or self.history[tick] == "F"):
            self.history[tick] += "X"
        else:
            self.history[tick] = "X"
        self.stage = "canceled"

    def fetch(self, tick):
        if self.stage != "fetching":
            raise Exception(f"Wrong time fetch for command {self}")

        self.stage = "dispatching"
        self.history[tick] = "F"

    def dispatch(self, tick, instruction):
        if self.stage != "dispatching":
            raise Exception(f"Wrong time dispatch for command {self}")

        self.stage = "decoding"
        self.history[tick] = "ID"

        self.instruction = instruction

    def decode(self, tick, wait):
        if self.stage != "decoding":
            raise Exception(f"Wrong time decode for command {self}")

        self._fill_wait_gap(tick)

        if wait:
            self.history[tick] = "W"
        else:
            self.stage = "issuing"
            self.history[tick] = "D"

    def issue_conflict(self, tick):
        if self.stage != "issuing":
            raise Exception(f"Wrong time issue_conflict for command {self}")

        self.history[tick] = "C"

    def _issue(self):
        if self.stage != "issuing":
            raise Exception(f"Wrong time issue for command {self}")

        self.stage = "complete"

    def issue_bu(self, tick):
        self._issue()
        self.history[tick] = "B"

    def issue_alu(self, tick):
        self._issue()
        self.history[tick] = "AL"

    def issue_lsu(self, tick):
        self._issue()
        self.history[tick] = "M1"
        self.history[tick + 1] = "M2"
        self.history[tick + 2] = "M3"

    def __str__(self):
        return f"<Command pc={hex(self.address)}, id={self.id}, history={self.history}>"


def generate_pipeline(input_path: Path):
    data = parse(input_path)
    data_by_tick = average_signal_data_by_tick(data)

    def to_int(value: str, base: int = 2) -> "int | None":
        if not value.isnumeric():
            return None
        return int(value, base)

    def to_hex(data) -> "str | None":
        if data is None:
            return None
        return hex(data)

    manager = CommandProcessingManager()

    for cyc_cnt, index in data_by_tick:
        manager.set_tick(cyc_cnt)

        def get(name: str) -> str:
            return data[name][index]

        def get_int(name: str, base: int = 2) -> "int | None":
            return to_int(get(name), base)

        cyc_cnt = get_int("/tb/cyc_cnt")
        print(f"Tick: {cyc_cnt}")

        # Fetching
        pc = get_int("/tb/uut/cpu/fetch_block/pc")
        print(f"PC: {to_hex(pc)}")

        id = get_int("/tb/uut/cpu/id_block/pc_id")
        print(f"pc_id: {id}")

        pc_id_assigned = get_int("/tb/uut/cpu/fetch_block/pc_id_assigned") == 1

        if pc_id_assigned:
            manager.new_fetch(pc, id)

        # ID (диспетчеризация)
        pc_table = [to_int(_pc) for _pc in get("/tb/uut/cpu/id_block/pc_table")]
        fetch_complete = get_int("/tb/uut/cpu/fetch_block/fetch_complete") == 1
        if fetch_complete:
            # WARNING: assume that if `fetch_complete` is positive,
            #          the command identifier will be the previous one (id - 1),
            #          although this may not always be the case
            dispatching_id = (id - 1) % 8
            dispatching_pc = pc_table[dispatching_id]
            fetch_instruction = get_int("/tb/uut/cpu/fetch_block/fetch_instruction")
            manager.dispatching_complete(dispatching_pc, dispatching_id, fetch_instruction)

        # Decode
        decode = get("/tb/uut/cpu/id_block/decode")

        decode_id = to_int(decode[0])
        decode_pc = to_int(decode[1])

        decode_valid = to_int(decode[3]) == 1
        decode_addr_valid = to_int(decode[4]) == 1
        decode_advance = get("/tb/uut/cpu/id_block/decode_advance") == "St1"
        if decode_valid and decode_addr_valid:
            assert pc_table[decode_id] == decode_pc
            print(f"decode_pc: {to_hex(decode_pc)}")
            manager.decoding(decode_pc, decode_id, wait=not decode_advance)

        # Issue
        rs1_conflict = get("/tb/uut/cpu/decode_and_issue_block/rs1_conflict")
        rs2_conflict = get("/tb/uut/cpu/decode_and_issue_block/rs2_conflict")

        issue = get("/tb/uut/cpu/decode_and_issue_block/issue")
        issue_pc = to_int(issue[0])
        issue_id = to_int(issue[9])
        issue_stage_valid = to_int(issue[10]) == 1
        if issue_stage_valid:
            print(f"issue.pc: {to_hex(issue_pc)}")
            print(f"issue.id: {issue_id}")

            alu_new_request = get_int("/tb/uut/cpu/decode_and_issue_block/unit_issue[0]/new_request") == 1
            lsu_new_request = get_int("/tb/uut/cpu/decode_and_issue_block/unit_issue[1]/new_request") == 1
            bu_new_request = get_int("/tb/uut/cpu/decode_and_issue_block/unit_issue[2]/new_request") == 1
            print(f"new_request[3]: {alu_new_request}, {lsu_new_request}, {bu_new_request}")

            if not any([alu_new_request, lsu_new_request, bu_new_request]):
                assert (rs1_conflict or rs2_conflict)
                manager.issue_conflict(issue_pc, issue_id)
            else:
                if bu_new_request:
                    manager.issue_bu(issue_pc, issue_id)
                elif alu_new_request:
                    manager.issue_alu(issue_pc, issue_id)
                elif lsu_new_request:
                    manager.issue_lsu(issue_pc, issue_id)

        flush = get_int("/tb/uut/cpu/gc_unit_block/gc_fetch_flush") == 1
        if flush:
            print(f"flush: {flush}")
            manager.flush()

        print()

    return len(data_by_tick), manager.completed_commands


def get_input_path() -> Path:
    if len(sys.argv) < 2:
        raise Exception("First argument required: input filename!")

    input_path = Path(sys.argv[1])

    assert os.path.isfile(input_path)

    return input_path


if __name__ == "__main__":
    main()
