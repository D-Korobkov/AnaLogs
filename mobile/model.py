from datetime import datetime
from typing import List, Mapping
import yaml

TIMESTAMP_PATTERN = "%d.%m.%Y-%H:%M:%S:%f"


class LogNode:
    def __init__(self, line_number: int, type: str, timestamp: str, content: str):
        self.line_number: int = line_number
        self.type: str = type
        self.timestamp: datetime = datetime.strptime(timestamp, TIMESTAMP_PATTERN)
        self.content = content
        self.children: List[LogNode] = []

    def __str__(self):
        return str(self.timestamp) + "\n" + str(self.type) + "\n" + str(self.content)

    def add_child(self, child):
        self.children.append(child)

    def get_node_id(self):
        return "node" + str(self.line_number)


class Schema:
    def __init__(self, yaml_path: str):
        with open(yaml_path, "r") as stream:
            yaml_map: Mapping = yaml.safe_load(stream)

        self.start_time: datetime = datetime.strptime(
            yaml_map.get("start_time"), TIMESTAMP_PATTERN
        )

        self.end_time: datetime = datetime.strptime(
            yaml_map.get("end_time"), TIMESTAMP_PATTERN
        )

        self.log_types: Mapping = yaml_map["log_types"]
        self.log_types2: Mapping = yaml_map["log_types"]

        # Словарь, где ключ имя родителя, а значение массив имена детей
        self.relations: Mapping = yaml_map["relations"]

        self.start_line: int = int(yaml_map.get("start_line"))
        self.end_line: int = int(yaml_map.get("end_line"))
