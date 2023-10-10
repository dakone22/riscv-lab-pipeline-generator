import csv
import os
import sys
from pathlib import Path

from generator import generate_pipeline, get_input_path


def main() -> Path:
    input_path = get_input_path()
    ticks, completed_commands = generate_pipeline(input_path)

    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        output_path = Path(os.path.splitext(input_path)[0] + ".csv")

    tick_count = ticks
    with open(output_path, 'w', newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Command', 'Code', 'id'] + list(map(str, range(1, tick_count))))
        for command in completed_commands:
            tick_line = [""] * tick_count
            for tick, c in command.history.items():
                tick_line[tick - 1] = c
            row = [hex(command.address)[2:], hex(command.instruction)[2:].rjust(8, "0"), command.id] + tick_line
            writer.writerow(row)

    return output_path


if __name__ == '__main__':
    main()
