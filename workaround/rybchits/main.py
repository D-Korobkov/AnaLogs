import re, sys, yaml

from datetime import datetime
from graphviz import Digraph
from typing import Mapping, List

TIMESTAMP_PATTERN = "%d.%m.%Y-%H:%M:%S:%f"

class LogNode:
    def __init__(self, line_number: int, type : str, timestamp: str, content: str):
        self.line_number : int = line_number
        self.type : str = type
        self.timestamp : datetime = datetime.strptime(timestamp, TIMESTAMP_PATTERN)
        self.content = content
        self.children : List[LogNode] = []

    def __str__(self):
        return str(self.timestamp) + "\n" + str(self.type) + "\n" + str(self.content)

    def add_child(self, child):
        self.children.append(child)

    def get_node_id(self):
        return "node" + str(self.line_number)

class Schema:
    def __init__(self, yaml_path: str):
        with open(yaml_path, "r") as stream:
            yaml_map : Mapping = yaml.safe_load(stream)
        stream.close()

        self.start_time : datetime = datetime.strptime(yaml_map.get('start_time'), TIMESTAMP_PATTERN)
        self.end_time : datetime = datetime.strptime(yaml_map.get('end_time'), TIMESTAMP_PATTERN)

        self.log_types: Mapping = yaml_map['log_types']
        self.log_types2: Mapping = yaml_map['log_types']

        # Словарь, где ключ имя родителя, а значение массив имена детей
        self.relations: Mapping = yaml_map['relations']

        self.start_line : int = int(yaml_map.get('start_line'))
        self.end_line : int = int(yaml_map.get('end_line'))


def vizualizate(nodes: List[LogNode]):
    dot = Digraph(comment='A Logs Graph')
    dot.attr(rankdir="TB")
    
    for parent_index, parent_node in enumerate(nodes):
        with dot.subgraph() as sub:
            sub.node(parent_node.get_node_id(), str(parent_node), shape="rectangle")

            if parent_index != 0:
                dot.edge(nodes[parent_index-1].get_node_id(), parent_node.get_node_id(), color="red", constraint = 'false')

            for child_index, child_node in enumerate(parent_node.children):
                sub.node(child_node.get_node_id(), str(child_node))

                if (child_index == 0):
                    sub.edge(parent_node.get_node_id(), child_node.get_node_id())
                else:
                    sub.edge(parent_node.children[child_index-1].get_node_id(), child_node.get_node_id())        
  
    dot.format = 'png'
    dot.render('GraphLogs.dot', view = True)


def main():
    if len(sys.argv) < 2:
        print("Missing some input files")
        return
    
    # Файл с логами
    log_file_path = sys.argv[1]

    # Файл со схемой
    schema = Schema(sys.argv[2])

    parents_list: List[LogNode] = []

    with open(log_file_path, "r") as file:

        has_match = False
        for line_number, line in enumerate(file.readlines()[schema.start_line : schema.end_line]):

            if len(parents_list) != 0:
                for child_type in schema.relations[parents_list[-1].type]:
                    match = re.match(schema.log_types[child_type]['regexp'], line)
                    if match != None:
                        has_match = True
                        log_content = match.groupdict()
                        parents_list[-1].add_child(LogNode(line_number=line_number, type=child_type, timestamp=log_content['timestamp'], content=log_content['content']))
                        break

            if has_match:
                has_match = False
                continue
            
            for parent_type in schema.relations:
                match = re.match(schema.log_types[parent_type]['regexp'], line)
                if match != None:
                    log_content = match.groupdict()
                    parents_list.append(LogNode(line_number=line_number, type=parent_type, timestamp=log_content['timestamp'], content=log_content['content']))

    file.close()

    vizualizate(parents_list)

if __name__ == '__main__':
    main()