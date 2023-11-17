import argparse
import enum
import pathlib
from dataclasses import dataclass
from textwrap import dedent
from typing import Optional

import opentelemetry.analyzer as otel_analyzer
import mobile.analyzer as mobile_analyzer
from querylang.query_expr import bool_expr


class LogSource(enum.Enum):
    OTEL = "open-telemetry"
    ANDROID = "android"


@dataclass
class ProgArguments:
    input_file: pathlib.Path
    log_source: str
    query: Optional[str]
    output_file: pathlib.Path
    schema_path: Optional[str]


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="AnaLogs",
        description="A visualization tool for your log file",
        epilog="You are awesome",
    )

    parser.add_argument(
        "--input-file",
        dest="input_file",
        type=pathlib.Path,
        required=True,
        help="Path to file with logs",
    )

    parser.add_argument(
        "--log-source",
        dest="log_source",
        type=str,
        required=True,
        choices=[e.value for e in LogSource],
        help="Log records source",
    )

    parser.add_argument(
        "--query",
        dest="query",
        type=str,
        required=False,
        help=dedent(
            """Boolean expression for log filtration.
            Supported operations:
            exact match (e.g. logLevel="INFO", severityNumber=2),
            regexp match (e.g. severityNumber~[0-9]),
            combinators and/or with braces (e.g. level="INFO" and (op="1" or op="2"))"""
        ),
    )

    parser.add_argument(
        "--output-file",
        dest="output_file",
        type=pathlib.Path,
        required=True,
        help="Path to output file",
    )

    parser.add_argument(
        "--schema",
        dest="schema_path",
        type=str,
        required=False,
        help="Schema for unstructured logs",
    )

    args = parser.parse_args()
    return ProgArguments(**args.__dict__)


if __name__ == "__main__":
    prog_args = parse_arguments()

    events_filter = None
    if prog_args.query is not None:
        events_filter = bool_expr.parseString(prog_args.query)[0]

    if prog_args.log_source == LogSource.OTEL.value:
        otel_analyzer.analyze_spans_with_logs(prog_args.input_file, prog_args.output_file, events_filter)
    elif prog_args.log_source == LogSource.ANDROID.value:
        mobile_analyzer.analyze_logs(prog_args.input_file, prog_args.output_file, prog_args.schema_path)
