import os
from pathlib import Path

import csv
import xlsxwriter

from generate_pipeline_csv import main as csv_main


def main():
    csv_file: Path = csv_main()

    # Replace 'output.xlsx' with the desired name of the output Excel file
    xlsx_file = Path(os.path.splitext(csv_file)[0] + ".xlsx")

    workbook = xlsxwriter.Workbook(xlsx_file)
    worksheet = workbook.add_worksheet()

    # Create a format for the column width
    # column_width_format = workbook.add_format({'width': 2.5})

    # Open and read the CSV file
    with open(csv_file, 'r') as csvfile:
        csvreader = csv.reader(csvfile)

        for row_num, row_data in enumerate(csvreader):
            # Write each cell value to the XLSX file
            for col_num, cell_value in enumerate(row_data):
                worksheet.write(row_num, col_num, cell_value)

    # Set the column width for all columns (except first two) to 2.5
    worksheet.set_column(0, 1, 10)
    worksheet.set_column(2, len(row_data) - 1, 2.5)

    # Close the workbook
    workbook.close()


if __name__ == '__main__':
    main()
