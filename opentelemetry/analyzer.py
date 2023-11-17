import pathlib
from collections import defaultdict
from typing import Optional, Dict, Tuple

from google.protobuf import json_format

from opentelemetry.formatter import format_dot
from opentelemetry.model import LogRecord, SpanRecord, Trace
from opentelemetry.proto.logs.v1 import logs_pb2
from opentelemetry.proto.trace.v1 import trace_pb2
from querylang.query_expr import bool_expr


def analyze_spans_with_logs(input_file: pathlib.Path, output_file: pathlib.Path, event_filter: Optional[bool_expr]):
    log_records: Dict[Tuple[str, str], list[LogRecord]] = defaultdict(list)
    with open(input_file, mode='r', encoding='utf-8') as f:
        for record in f:
            try:
                logs_data = logs_pb2.LogsData()
                json_format.Parse(record, logs_data)
                for rl in logs_data.resource_logs:
                    for sl in rl.scope_logs:
                        for lr in sl.log_records:
                            log_record = LogRecord.from_proto(lr)
                            if event_filter is not None and \
                                    not event_filter.does_match(log_record.build_meta()):
                                continue

                            log_records[(log_record.trace_id, log_record.span_id)].append(log_record)
            except json_format.ParseError:
                continue

    span_records: Dict[str, list[SpanRecord]] = defaultdict(list)
    with open(input_file, mode='r', encoding='utf-8') as f:
        for record in f:
            try:
                traces_data = trace_pb2.TracesData()
                json_format.Parse(record, traces_data)
                for rs in traces_data.resource_spans:
                    for ss in rs.scope_spans:
                        for span in ss.spans:
                            logs = log_records[(span.trace_id, span.span_id)]
                            logs.sort(key=lambda log: log.unix_nano_ts)
                            span_record = SpanRecord.from_proto(span, logs)
                            if event_filter is not None and \
                                    not event_filter.does_match(span_record.build_meta()):
                                continue

                            span_records[span.trace_id].append(span_record)
            except json_format.ParseError:
                continue

    traces = [
        Trace(
            trace_id=trace_id,
            unix_nano_start_at=min(map(lambda v: v.unix_nano_start_at, spans)),
            unix_nano_end_at=max(map(lambda v: v.unix_nano_end_at, spans)),
            spans=spans,
        )
        for trace_id, spans in span_records.items()
    ]

    with open(output_file, mode='w', encoding='utf-8') as f:
        f.write(format_dot(traces))
        # f.write(format_dot(span._records.values()[0]))
