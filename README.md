```bash
usage: find_large_files [-h] [-s SIZE] [-u {KB,KiB,MB,GB,MiB,GiB,TB,TiB}] [-o {console,file}] [-ft {txt,csv}] [-fn FILE_NAME]
                        [--store STORE] [-r ROUND] [-v]
                        [path]

A simple program to find large files under a provided path using the specified threshold

positional arguments:
  path                  Specify the actual path to check it against. Defaults to the current directory.

options:
  -h, --help            show this help message and exit
  -s SIZE, --size SIZE  Specify the threshold size. Files larger than this size will be listed. Note that this size will be converted to bytes using the provided unit.
  -u {KB,KiB,MB,GB,MiB,GiB,TB,TiB}, --unit {KB,KiB,MB,GB,MiB,GiB,TB,TiB}
                        Specify the size unit. Unit specified will be used with size to find the larger files.
  -o {console,file}, --output {console,file}
                        Specify the output type. Output can be shown to the console, or it can written to a file.
  -ft {txt,csv}, --file-type {txt,csv}
                        Specify the file type to store the output in. Possible outputs are as follows:-
                            - Non-Verbose Txt Output: Shows only the paths that are found to be larger than the threshold.
                            - Verbose Txt Output: Prints the Console Table Output.
                            - Non-Verbose CSV Output: Stores the paths under a column named paths.
                            - Verbose CSV Output: Stores the paths similar to the the verbose table output, only in CSV Format
  -fn FILE_NAME, --file-name FILE_NAME
                        Specify the filename to provide to the file where the output will be stored.
  --store STORE         Specify where to store the file output. Defaults to the current directory.Note that if the provided store file exists, this will be overwritten
  -r ROUND, --round ROUND
                        Specify the number of digits to show for the size output. By default, it will show 2 decimal digits. Change to 0 to get an integer value.
  -v, --verbose         Specify the verbosity of the output. No verbosity will only show the table names as a list.
```