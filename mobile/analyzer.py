import pathlib
import re
from typing import List

from mobile.formatter import visualize_dot
from mobile.model import LogNode, Schema


def analyze_logs(log_file: pathlib.Path, out: pathlib.Path, schema_path: str):
    schema = Schema(schema_path)
    parents_list: List[LogNode] = []

    with open(log_file, "r") as file:
        has_match = False
        for line_number, line in enumerate(
                file.readlines()[schema.start_line: schema.end_line]
        ):
            if parents_list:
                for child_type in schema.relations[parents_list[-1].type]:
                    match = re.match(schema.log_types[child_type]["regexp"], line)
                    if match is not None:
                        has_match = True
                        log_content = match.groupdict()
                        parents_list[-1].add_child(
                            LogNode(
                                line_number=line_number,
                                type=child_type,
                                timestamp=log_content["timestamp"],
                                content=log_content["content"],
                            )
                        )

                        break

            if has_match:
                has_match = False
                continue

            for parent_type in schema.relations:
                match = re.match(schema.log_types[parent_type]["regexp"], line)
                if match is not None:
                    log_content = match.groupdict()
                    parents_list.append(
                        LogNode(
                            line_number=line_number,
                            type=parent_type,
                            timestamp=log_content["timestamp"],
                            content=log_content["content"],
                        )
                    )

    visualize_dot(parents_list, out)
