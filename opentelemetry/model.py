from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from opentelemetry.proto.common.v1 import common_pb2
from opentelemetry.proto.logs.v1 import logs_pb2
from opentelemetry.proto.trace.v1 import trace_pb2


@dataclass
class LogRecord:
    span_id: str
    trace_id: str
    unix_nano_ts: int
    keyvalues: dict

    def build_meta(self):
        return self.keyvalues | {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "timestamp": datetime.fromtimestamp(self.unix_nano_ts / 1_000_000_000).strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __hash__(self) -> int:
        # very stupid exclude policy
        data = [v for k, v in self.keyvalues.items() if "id" not in k.lower()]
        return hash(str(data))

    @staticmethod
    def from_proto(data: logs_pb2.LogRecord):
        return LogRecord(
            span_id=data.span_id,
            trace_id=data.trace_id,
            unix_nano_ts=data.time_unix_nano,
            keyvalues={
                attr.key: _any_value_to_str(attr.value) for attr in data.attributes
            }
        )


@dataclass
class SpanRecord:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    unix_nano_start_at: int
    unix_nano_end_at: int
    logs: List[LogRecord]

    def build_meta(self):
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "timestamp": datetime.fromtimestamp(self.unix_nano_end_at / 1_000_000_000).strftime("%Y-%m-%d %H:%M:%S"),
        }

    @staticmethod
    def from_proto(data: trace_pb2.Span, logs: List[LogRecord]):
        return SpanRecord(
            trace_id=data.trace_id,
            span_id=data.span_id,
            parent_span_id=data.parent_span_id,
            name=data.name,
            unix_nano_start_at=data.start_time_unix_nano,
            unix_nano_end_at=data.end_time_unix_nano,
            logs=logs,
        )


def _any_value_to_str(any_val: common_pb2.AnyValue) -> str:
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
        return f'[{", ".join(list(map(_any_value_to_str, any_val.array_value.values)))}]'
    elif any_val.kvlist_value is not None:
        kvlist = []
        for kv in any_val.kvlist_value.values:
            kvlist.append(f"{kv.key}: {_any_value_to_str(kv.value)}")
        return f'{{{", ".join(kvlist)}}}'
    else:
        return "Unsupported value type"


@dataclass
class Trace:
    trace_id: str
    unix_nano_start_at: int
    unix_nano_end_at: int
    spans: List[SpanRecord]
