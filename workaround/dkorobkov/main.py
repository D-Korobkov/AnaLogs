from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import google.protobuf.json_format as json_format

import opentelemetry.proto.common.v1.common_pb2 as common_pb2
import opentelemetry.proto.logs.v1.logs_pb2 as logs_pb2
import opentelemetry.proto.trace.v1.trace_pb2 as trace_pb2


@dataclass
class Log:
    timestamp_unix: int
    level: Optional[str]
    keys: list[str]
    values: list[str]


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    start_at_unix: int
    end_at_unix: int


@dataclass
class Trace:
    trace_id: str
    spans: list[Span]
    start_at_unix: int


def any_value_to_str(any_val: common_pb2.AnyValue) -> str:
    if any_val.string_value is not None:
        return str(any_val.string_value)
    elif any_val.bool_value is not None:
        return str(any_val.bool_value)
    elif any_val.int_value is not None:
        return str(any_val.int_value)
    elif any_val.double_value is not None:
        return str(any_val.double_value)
    elif any_val.bytes_value is not None:
        return str(any_val.bytes_value)
    elif any_val.array_value is not None:
        return f'[{", ".join(list(map(any_value_to_str, any_val.array_value.values)))}]'
    elif any_val.kvlist_value is not None:
        kvlist = []
        for kv in any_val.kvlist_value.values:
            kvlist.append(f"{kv.key}: {any_value_to_str(kv.value)}")
        return f'{{{", ".join(kvlist)}}}'
    else:
        return "Unsupported value type"


def format_dot(traces: list[Trace]) -> str:
    from io import StringIO
    dot_notation = StringIO()

    dot_notation.write("digraph G {")
    for t_idx, trace in enumerate(traces):
        # dot_notation.write(f'ts_{t_idx} [label="{datetime.fromtimestamp(trace.start_at_unix / 1_000_000_000)}"];')
        dot_notation.write(f"subgraph cluster_{t_idx} {{")
        dot_notation.write("node [shape=rectangle];")
        dot_notation.write(f'label = "Trace ID: {trace.trace_id}";')
        for span in trace.spans:
            dot_notation.write(f's_{t_idx}_{span.span_id} [label="Span ID: {span.span_id}\\nName: {span.name}"];')
            if span.parent_span_id is None or len(span.parent_span_id) == 0:
                pass
                # dot_notation.write(f'ts_{t_idx} -> s_{t_idx}_{span.span_id};')
            else:
                dot_notation.write(f"s_{t_idx}_{span.parent_span_id} -> s_{t_idx}_{span.span_id};")
        # if t_idx > 0:
        # dot_notation.write(f'ts_{t_idx - 1} -> ts_{t_idx};')
        dot_notation.write("}")
    dot_notation.write("}")

    return dot_notation.getvalue()


if __name__ == '__main__':
    logs_in_span = defaultdict(list)
    all_traces = []

    with open('../../examples/opentelemetry/exported-data.json', mode='r', encoding='utf-8') as f:
        spans_in_trace = defaultdict(list)
        for line in f:
            try:
                log_event = logs_pb2.LogsData()
                json_format.Parse(line, log_event)
                for rl in log_event.resource_logs:
                    for sl in rl.scope_logs:
                        for lr in sl.log_records:
                            logs_in_span[(lr.trace_id, lr.span_id)].append(
                                Log(
                                    timestamp_unix=lr.time_unix_nano,
                                    level=lr.severity_text,
                                    keys=list(map(lambda attr: attr.key, lr.attributes)),
                                    values=list(map(lambda attr: any_value_to_str(attr.value), lr.attributes)),
                                )
                            )
            except json_format.ParseError as e:
                span_event = trace_pb2.TracesData()
                json_format.Parse(line, span_event)
                for rs in span_event.resource_spans:
                    for ss in rs.scope_spans:
                        for span in ss.spans:
                            spans_in_trace[span.trace_id].append(
                                Span(
                                    trace_id=span.trace_id,
                                    span_id=span.span_id,
                                    parent_span_id=span.parent_span_id,
                                    name=span.name,
                                    start_at_unix=span.start_time_unix_nano,
                                    end_at_unix=span.end_time_unix_nano,
                                )
                            )

        all_traces = [
            Trace(
                trace_id=k,
                spans=v,
                start_at_unix=min(map(lambda s: s.start_at_unix, v)),
            ) for k, v in spans_in_trace.items()
        ]
        all_traces.sort(key=lambda trace: trace.start_at_unix)

        # print(spans_in_trace.keys())

    # for i, t in enumerate(all_traces):
    #     if len(t.spans) == 12:
    #         print(i)

    # d = dict()
    # for t in all_traces:
    #     d[len(t.spans)] = True
    # print(d.keys())

    with open('out.dot', mode='w', encoding='utf-8') as f:
        f.write(format_dot(all_traces[97:99]))
        # f.write(format_dot(all_traces[97:99]))
