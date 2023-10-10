# riscv-lab-pipeline-generator
Скрипт для генерации трассы выполнения программы на микропроцессорном ядре Taiga для [ЛР1 Изучение принципов работы микропроцессорного ядра RISC-V](https://gitlab.com/sibragimov/riscv-lab/-/blob/main/main.adoc) 

## Использование

1. Запустить симуляцию в среде Modelsim (см. методичку по лабораторной работе)
2. Экспортировать данные симуляции:
   1. Активировать окно `List`: вкладка `View` -> `List`
      ![list-tab-activate](docs/list-tab-activate.png)
   2. Выделить все сигналы (`Ctrl+A`) на Wave-диаграмме и скопировать (`Ctrl+C`)
      ![select-and-copy-all-signals](docs/select-and-copy-all-signals.png)
   3. Перейти на вкладку `List` и вставить все сигналы (`Ctrl+V`)
      ![paste-signals-on-list-tab](docs/paste-signals-on-list-tab.png)
   4. Экспортировать: `File` -> `Export` -> `Tabular list...` и сохранить в виде файла формата `.lst`
      ![export-list-tab](docs/export-list-tab.png)
3. Запустить `generate-pipeline.py VarX.lst`, входной файл будет либо первым аргументом, либо файл `input.lst`.
4. Результаты будут в файле с названием входного файла и формата `.csv`, либо в файле `output.csv`
5. (_опционально_) Импортировать в Excel: `Данные` -> `Из текстового/CSV-файла`
   ![excel-import-csv](docs/excel-import-csv.png)

![excel-results](docs/excel-results.png)