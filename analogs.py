import argparse
import enum
import pathlib
from dataclasses import dataclass
from typing import Optional


class LogSource(enum.Enum):
    OTEL = 'open-telemetry'
    ANDROID = 'android'


@dataclass
class ProgArguments:
    input_file: pathlib.Path
    log_source: str
    query: Optional[str]
    output_file: pathlib.Path


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='AnaLogs',
        description='A visualization tool for your log file',
        epilog='You are awesome',
    )

    parser.add_argument('--input-file', dest='input_file', type=pathlib.Path, required=True,
                        help='Path to file with logs')
    parser.add_argument('--log-source', dest='log_source', type=str, required=True,
                        choices=[e.value for e in LogSource], help=f'Log records source')
    parser.add_argument('--query', dest='query', type=str, required=False,
                        help='''Boolean expression for log filtration.
                        Supported operations:
                        exact match (e.g. logLevel="INFO", severityNumber=2),
                        regexp match (e.g. severityNumber~[0-9]),
                        combinators and/or with braces (e.g. level="INFO" and (op="1" or op="2"))''')
    parser.add_argument('--output-file', dest='output_file', type=pathlib.Path, required=True,
                        help='Path to output file')
    args = parser.parse_args()

    return ProgArguments(**args.__dict__)


if __name__ == "__main__":
    prog_args = parse_arguments()
    print(prog_args)
