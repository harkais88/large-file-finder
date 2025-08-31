#!/usr/bin/python3
import argparse
import csv
import os
import sys
import textwrap
import warnings
from typing import Any, Final, Iterable, Literal

Unit = Literal["KB", "KiB", "MB", "MiB", "GB", "GiB", "TB", "TiB"]

# Reference: https://en.wikipedia.org/wiki/Byte
BYTES_CONVERSION_LOOKUP: Final[dict[Unit, int]] = {
    "KB": 1000,
    "KiB": 1024,
    "MB": 1000**2,
    "MiB": 1024 * 2,
    "GB": 1000**3,
    "GiB": 1024**3,
    "TB": 1000**4,
    "TiB": 1024**4,
}


class PathDoesNotExistError(FileNotFoundError):
    def __init__(self, path=None, *args, **kwargs):
        msg = "Provided path does not exist"
        if path is not None:
            msg += ": " + path
        super().__init__(msg, *args, **kwargs)


class CheckPathExistsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        path_to_check = values
        if not os.path.exists(path_to_check):
            raise PathDoesNotExistError(path=path_to_check)
        setattr(namespace, self.dest, values)


def get_arguments():
    parser = argparse.ArgumentParser(
        prog="find_large_files",
        description="A simple program to find large files under a provided path using the specified threshold",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--size",
        type=float,
        default=1.0,
        help="Specify the threshold size. Files larger than this size will be listed. "
        "Note that this size will be converted to bytes using the provided unit.",
    )
    parser.add_argument(
        "-u",
        "--unit",
        type=str,
        choices=["KB", "KiB", "MB", "GB", "MiB", "GiB", "TB", "TiB"],
        default="MB",
        help="Specify the size unit. Unit specified will be used with size to find the larger files.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        choices=["console", "file"],
        default="console",
        help="Specify the output type. Output can be shown to the console, or it can written to a file.",
    )
    parser.add_argument(
        "-ft",
        "--file-type",
        type=str,
        choices=["txt", "csv"],
        default="txt",
        help=textwrap.dedent(
            """\
        Specify the file type to store the output in. Possible outputs are as follows:-
            - Non-Verbose Txt Output: Shows only the paths that are found to be larger than the threshold.
            - Verbose Txt Output: Prints the Console Table Output.
            - Non-Verbose CSV Output: Stores the paths under a column named paths.
            - Verbose CSV Output: Stores the paths similar to the the verbose table output, only in CSV Format
        """
        ),
    )
    parser.add_argument(
        "-fn",
        "--file-name",
        type=str,
        default="large_files",
        help="Specify the filename to provide to the file where the output will be stored.",
    )
    parser.add_argument(
        "--store",
        action=CheckPathExistsAction,
        type=str,
        default=os.path.dirname(__file__),
        help="Specify where to store the file output. Defaults to the current directory."
        "Note that if the provided store file exists, this will be overwritten",
    )
    parser.add_argument(
        "-r",
        "--round",
        type=int,
        default=2,
        help="Specify the number of digits to show for the size output. "
        "By default, it will show 2 decimal digits. Change to 0 to get an integer value.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Specify the verbosity of the output. No verbosity will only show the table names as a list.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=str,
        action=CheckPathExistsAction,
        default=os.path.dirname(__file__),
        help="Specify the actual path to check it against. Defaults to the current directory.",
    )

    try:
        args = parser.parse_args()
    except PathDoesNotExistError as e:
        print("\nPathDoesNotExistError:", str(e), end="\n")
        sys.exit()

    return args


def get_threshold_in_bytes(size: float, unit: Unit = "MB") -> float:
    """Converts provided size into bytes based on unit provided"""
    return size * BYTES_CONVERSION_LOOKUP[unit]


def get_human_readable_size(size: float, unit: Unit = "MB", round_to: int = 2) -> str:
    """Converts bytes to a human readable format. Uses the unit provided for threshold"""

    converted_size = size / BYTES_CONVERSION_LOOKUP[unit]
    return str(round(converted_size, round_to)) + " " + unit


class LargeFilesOutputHandler:
    def __init__(
        self,
        large_files: list[str | dict[str, str]],
        verbose: bool = False,
        output_to: Literal["console", "file"] = "console",
        file_type: Literal["txt", "csv"] = "txt",
        file_store: str = os.path.dirname(__file__),
        file_name: str | None = None,
    ):
        self.large_files = large_files
        self.output_to = output_to
        self.file_type = file_type

        self.file_name = file_name + "." + self.file_type
        self.file_store = file_store
        if os.path.isfile(self.file_store):
            if self.file_store.split(".")[1] != self.file_type:
                new_file_store = os.path.join(os.path.dirname(self.file_store), self.file_name)
                warnings.warn(
                    f"Specified store file is not of type {self.file_type}, "
                    f"storing output at {new_file_store} instead"
                )
                self.file_store = new_file_store
            if self.file_store.split(".")[0] != file_name:
                warnings.warn(
                    f"Output is being stored at {self.file_store.split('.')[0]} instead of {file_name}"
                )
        elif os.path.isdir(self.file_store):
            new_file_store = os.path.join(self.file_store, self.file_name)
            if os.path.exists(new_file_store):
                warnings.warn(f"{self.file_name} already exists, this will be overwritten.")
            self.file_store = new_file_store

        self.file = None
        if self.output_to == "file":
            print(f"Writing to file {self.file_store}.....")
            self.file = open(self.file_store, "w", newline=None if self.file_type == "txt" else "")
            if self.file_type == "csv":
                self.csv_writer = csv.writer(self.file)

        if not verbose:
            self.print_without_verbose()
        else:
            self.print_verbose()

    def __del__(self):
        if self.file is not None:
            self.file.close()

    def print(self, *args: Iterable[Any], end="\n"):
        """Prints the provided arguments to the specified output target.

        Note that the provided args will always be concatenated together.
        Also note that each argument will be casted to string, so expect
        errors to raise if for some reason the argument cannot be casted
        to a string value.
        """

        if self.output_to == "console":
            sys.stdout.write(" ".join(args) + end)
        elif self.output_to == "file":
            if self.file_type == "txt":
                self.file.write(" ".join(args) + end)
            elif self.file_type == "csv":
                self.csv_writer.writerow(*args)

    def print_without_verbose(self):
        if self.file_type == "txt":
            self.print("\nFiles and Directories found")
            self.print("----------------------------")
            self.print("\n".join(self.large_files))
        elif self.file_type == "csv":
            self.print("Paths")
            for large_file in self.large_files:
                self.print(large_file)

    def print_verbose(self):
        if self.file_type == "txt":
            self.print_table()
        elif self.file_type == "csv":
            headers = self.get_headers()
            self.print(headers)
            for data in self.large_files:
                self.print([data[header] for header in headers])

    def get_header_line_for_table(self):
        """Get the main header line for the table output

        The main idea behind generating this line is that the first
        center character of the header word should exist at the first
        center character of the divider lines. Therefore, this should
        be able to place the header nicely in the center.
        """

        leading_blanks = lambda header: " " * (
            ((self.print_table_config[header] + 2) // 2) - (len(header) // 2)
        )
        trailing_blanks = lambda header: " " * (
            (
                ((self.print_table_config[header] + 2) // 2)
                + (self.print_table_config[header] % 2 + 1)
            )
            - len(header[len(header) // 2 - 1 :])
        )
        return (
            "".join(
                [
                    "|" + leading_blanks(header) + header + trailing_blanks(header)
                    for header in self.headers
                ]
            )
            + "|"
        )

    def get_headers(self, inconsistent_headers=False):
        if not inconsistent_headers:
            headers = [key for key, _ in self.large_files[0].items()]
        else:
            headers = []
            for large_file in self.large_files:
                for key, _ in large_file.items():
                    if key not in headers:
                        headers.append(key)
        # Sorting the headers to avoid unexpected surprises
        headers = self.headers = sorted(headers)
        return headers

    def print_table(self, inconsistent_headers=False):
        headers = self.get_headers(inconsistent_headers=inconsistent_headers)

        self.print_table_config = {}
        for header in headers:
            max_data_length = len(str(max(self.large_files, key=lambda x: str(x[header]))[header]))
            self.print_table_config[header] = max_data_length

        # Printing the first line
        # Note: Adding +2 for considering the blank lines
        common_line = (
            "".join(["+" + "-" * (self.print_table_config[header] + 2) for header in headers]) + "+"
        )
        self.print(common_line)

        # Printing the header line
        # Note: This was a lot of guesswork...
        self.print(self.get_header_line_for_table())

        # Printing the third line
        self.print(common_line)

        # Printing the data itself
        for large_file in self.large_files:
            for header in headers:
                # TODO: Considering pushing data to the middle
                self.print("| " + large_file[header], end=" ")
            self.print(end="|\n")

        # And finally, the ending line
        self.print(common_line)


def main(args: argparse.ArgumentParser):
    path: str = args.path
    size: float = args.size
    unit: Unit = args.unit
    threshold = get_threshold_in_bytes(size, unit)

    large_list: list[str | dict[str, str]] = []
    for dirpath, dirnames, filenames in os.walk(path):
        # Checking size of directories first
        for dirname in dirnames:
            dir_path = os.path.join(dirpath, dirname)
            dir_size = os.path.getsize(dir_path)
            if dir_size > threshold:
                if not args.verbose:
                    large_list.append(dir_path)
                    continue
                dir_verbose_object = {
                    "name": dirname,
                    "type": "Directory",
                    "root": dirpath,
                    "path": dir_path,
                    "size": get_human_readable_size(dir_size, unit, args.round),
                }
                large_list.append(dir_verbose_object)

        # Then, we check the size of the files in the dirpath
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            file_size = os.path.getsize(file_path)
            if file_size > threshold:
                if not args.verbose:
                    large_list.append(file_path)
                    continue
                file_verbose_object = {
                    "name": filename,
                    "type": "File",
                    "root": dirpath,
                    "path": file_path,
                    "size": get_human_readable_size(file_size, unit, args.round),
                }
                large_list.append(file_verbose_object)

    print(f"Total Number of files larger than {size} {unit}: {len(large_list)}")
    if len(large_list) != 0:
        LargeFilesOutputHandler(
            large_files=large_list,
            verbose=args.verbose,
            output_to=args.output,
            file_name=args.file_name,
            file_type=args.file_type,
            file_store=args.store,
        )


if __name__ == "__main__":
    main(get_arguments())
