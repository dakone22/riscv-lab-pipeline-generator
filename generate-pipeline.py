import csv


def word_positions(input_string):
    words = input_string.split()
    positions = {}
    start = 0

    for word in words:
        word_len = len(word)
        end = input_string.find(word, start)
        positions[end + word_len - 1] = word
        start = end + word_len

    return positions

def find_first_data_line(lines):
    for index, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line and stripped_line[0] == "0":
            return index

    raise Exception("First data line not found! Make sure first line of data starts with zero!")

WHITESPACE = [" ", ]

def get_value_by_end_index(line, end_index):
    start_index = end_index

    while start_index > 0 and line[start_index] not in WHITESPACE:
        start_index -= 1

    return line[start_index + 1: end_index + 1]


    # values = line.split()
    #
    # for value in values:
    #     if line.rindex(value, 0, end_index + 1) + len(value) - 1 == end_index:
    #         #if end_index == 51:
    #         #    print(value)
    #         return value
    #
    # return None

def replace_char_inside_braces(text, replacing_char, replaced_char):
    inside_braces_depth = 0
    chars = list(text)
    for index, char in enumerate(chars):
        if char == "{":
            inside_braces_depth += 1
        elif char == "}":
            inside_braces_depth -= 1
        if inside_braces_depth > 0 and char == replacing_char:  # whitespace
            chars[index] = replaced_char
    return "".join(chars)

SPLIT_CHAR = "_"

# def merge_bracet_values(lst):
#     merged_list = []
#     stack = []
#     nested_depth = 0

#     for item in lst:
#         if item.startswith('{'):
#             nested_depth += 1
#         elif item.endswith('}'):
#             nested_depth -= 1
#             if nested_depth == 0:
#                 stack.append(item)
#                 merged_list.append(SPLIT_CHAR.join(stack))
#                 continue
#         if nested_depth > 0:
#             stack.append(item)
#         else:
#             merged_list.append(item)

#     return merged_list


def unnest_braces(value):
    if not value.startswith("{"): 
        return value
    assert value.endswith("}")

    value = value[1: -1]
    
    value = replace_char_inside_braces(value, SPLIT_CHAR, " ")


    values = [replace_char_inside_braces(v, " ", SPLIT_CHAR) for v in value.split(SPLIT_CHAR)]
    #return values
    return list(map(unnest_braces, values))


def main():
    with open("input.lst", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # split into headers lines and data lines
    first_data_line_index = find_first_data_line(lines)
    header_lines, data_lines = lines[:first_data_line_index], lines[first_data_line_index:]

    # fix multivalues in {}
    for index, data_line in enumerate(data_lines):
        data_lines[index] = replace_char_inside_braces(data_line, " ", SPLIT_CHAR)

    # get headers' ends
    headers_by_ends = {}
    for line in header_lines:
        headers_by_ends.update(word_positions(line))
    
    # collect all data by headers
    data = {}
    for end_index, header in headers_by_ends.items():
        data[header] = []
        for data_line in data_lines:
            value = get_value_by_end_index(data_line, end_index)
            value = unnest_braces(value)
            data[header].append(value)

    # print(data)

    data_index_by_cyc_cnt = {}

    for index, cyc_cnt in enumerate(data["/tb/cyc_cnt"]):
        if cyc_cnt.isnumeric():
            tick = int(cyc_cnt, 2)
            if tick not in data_index_by_cyc_cnt.keys():
                data_index_by_cyc_cnt[tick] = list()
            data_index_by_cyc_cnt[tick].append(index)

    data_index_list = sorted(data_index_by_cyc_cnt.items(), key=lambda item: item[0])

    # data_index_by_cyc_cnt = {}
    #
    # for index, cyc_cnt in enumerate(data["/tb/cyc_cnt"]):
    #     if cyc_cnt.isnumeric():
    #         data_index_by_cyc_cnt[int(cyc_cnt, 2)] = index
    #         # if data_entry not in _cyc_cnt:
    #         #     _cyc_cnt.add(data_entry)
    #         #     data_index_list.append(index)
    #
    # data_index_list = sorted(data_index_by_cyc_cnt.items(), key=lambda item: item[0])
    #
    export_data_by_address_merged = []
    active_commands = {}  # command: (start_tick, ["F", "ID", "W", "D", "AL"])

    def to_int2(value: str) -> "int | None":
        if not value.isnumeric():
            return None
        return int(value, 2)

    def to_hex(data: "str | None") -> "str | None":
        if data is None:
            return None
        return hex(data)

    for cyc_cnt, index_list in data_index_list:
        print(active_commands)
        index = index_list[len(index_list) // 2]

        def get(name: str) -> str:
            return data[name][index]

        def get_int(name: str) -> "int | None":
            return to_int2(get(name))


        cyc_cnt = get_int("/tb/cyc_cnt")
        print(f"Tick: {cyc_cnt}")

        pc = get_int("/tb/uut/cpu/fetch_block/pc")
        print(f"PC: {to_hex(pc)}")

        #if pc in active_commands.keys(): break
        active_commands[pc] = [cyc_cnt, ["F", "ID"]]

        decode = get("/tb/uut/cpu/id_block/decode")
        decode_pc = to_int2(decode[1])
        decode_advance = get("/tb/uut/cpu/id_block/decode_advance") == "St1"
        print(f"decode_pc: {to_hex(decode_pc)}")
        print(f"decode_done: {(decode_advance)}")
        if decode_pc in active_commands.keys() and cyc_cnt - active_commands[decode_pc][0] >= 2:
            if decode_advance:
                waited_ticks = cyc_cnt - active_commands[decode_pc][0]  - 2
                active_commands[decode_pc][1].extend(["W"] * waited_ticks + ["D"])

        issue = get("/tb/uut/cpu/decode_and_issue_block/issue")
        issue_pc = to_int2(issue[0])
        print(f"issue.pc: {to_hex(issue_pc)}")

        new_request_0 = get_int("/tb/uut/cpu/decode_and_issue_block/unit_issue[0]/new_request")
        new_request_1 = get_int("/tb/uut/cpu/decode_and_issue_block/unit_issue[1]/new_request")
        new_request_2 = get_int("/tb/uut/cpu/decode_and_issue_block/unit_issue[2]/new_request")

        print(f"new_request[3]: {new_request_0}, {new_request_1}, {new_request_2}")
        if new_request_2 == 1:
            last = "B"
        elif new_request_0 == 1:
            last = "AL"
        elif new_request_1 == 1:
            last = "M"
        elif new_request_0 == 0 and new_request_1 == 0 and new_request_2 == 0:
            last = "C"
        else:
            raise Exception("Unknown new requests")
        if issue_pc in active_commands.keys() and (active_commands[issue_pc][1][-1] == "D" or active_commands[issue_pc][1][-1] == "C") and cyc_cnt - active_commands[issue_pc][0] >= 3:
            if last != "M":
                active_commands[issue_pc][1].append(last)
            else:
                active_commands[issue_pc][1].extend(["M1", "M2", "M3"])

            if last != "C":
                start_tick, jobs = active_commands[issue_pc]

                export_data_by_address_merged.append((issue_pc, {start_tick+index: job for index, job in enumerate(jobs)}))
                print(f"exporting {export_data_by_address_merged[-1]}")

                active_commands.pop(issue_pc)
            #for key, value in active_commands.items():
            #    export_data_by_address_merged.append((key, value))
            #active_commands = dict()

        flush = get_int("/tb/uut/cpu/gc_unit_block/gc_fetch_flush")
        print(f"flush: {bool(flush)}")

        if flush:
            active_commands[pc] = [cyc_cnt, ["F"]]
            for command in active_commands.keys():
                #active_commands[command][1][-1] = "X"
                start_tick, jobs = active_commands[command]
                jobs.extend(["W"] * (cyc_cnt - start_tick - len(jobs) + 1))
                last = "X"
                if jobs[-1] == "D":
                    last = "DX"
                elif jobs[-1] == "F":
                    last = "FX"
                jobs[-1] = last
                export_data_by_address_merged.append((command, {start_tick+index: job for index, job in enumerate(jobs)}))
                print(f"exporting {export_data_by_address_merged[-1]}")

            active_commands = {} # active_commands[issue_pc] = None
            continue

        print()

    # print(
    #     list(
    #         map(
    #             str,
    #             range(
    #                 1,
    #                 max(
    #                     active_commands.items(),
    #                     key=lambda item:
    #                         max(item[1].keys())
    #                 )+1
    #             )
    #         )
    #     )
    # )
    tick_len = len(data_index_list) + 1
    with open('export.csv', 'w', newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Command'] + list(map(str, range(1, tick_len))))
        for command, items in export_data_by_address_merged:
            row = [hex(command)] + [""] * tick_len
            for tick, c in items.items():
                row[tick] = c
            writer.writerow(row)


if __name__ == "__main__":
    main()
