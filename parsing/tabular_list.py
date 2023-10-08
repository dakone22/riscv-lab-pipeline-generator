from pathlib import Path


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


SPLIT_CHAR = "?"


def unnest_braces(value):
    if not value.startswith("{"):
        return value
    assert value.endswith("}")

    value = value[1: -1]

    value = replace_char_inside_braces(value, SPLIT_CHAR, " ")

    values = [replace_char_inside_braces(v, " ", SPLIT_CHAR) for v in value.split(SPLIT_CHAR)]
    # return values
    return list(map(unnest_braces, values))


def parse(filename: Path) -> dict:
    with open(filename, "r", encoding="utf-8") as f:
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

    return data
