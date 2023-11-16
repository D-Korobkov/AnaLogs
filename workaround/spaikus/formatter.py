from datetime import datetime
from typing import List, Dict, Optional

from query_expr import bool_expr


def time_from_ns(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1_000_000_000).strftime("%Y-%m-%d %H:%M:%S")


class Log:
    def __init__(
        self, id: int, span_id: int, trace_id: int, timestamp: int, data: dict
    ):
        self.id = id
        self.span_id = span_id
        self.trace_id = trace_id
        self.timestamp = timestamp
        self.data = data

    def build_meta(self):
        return self.data | {
            "id": self.id,
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "timestamp": time_from_ns(self.timestamp),
        }

    def __str__(self) -> str:
        return f"{self.id}: {str(self.data)}"

    def __hash__(self) -> int:
        # very stupid exclude policy
        data = [v for k, v in self.data.items() if "id" not in k.lower()]
        return hash(str(data))


class Span:
    def __init__(
        self,
        span_id: int,
        trace: "Trace",
        name: str,
        start_at: int,
        end_at: int,
        parent: "Optional[Span]" = None,
    ):
        self.id = span_id
        self.trace = trace
        self.name = name
        self.start_at = start_at
        self.end_at = end_at

        self.parent = parent
        self.children: "List[Span]" = []
        self.nodes: "List[Log]" = []

        self.hash = None

    def __str__(self) -> str:
        return f"({str(self.parent)} <- -> {str(self.children)}: {self.nodes})"

    def compute_hash(self, ordered=False) -> None:
        for c in self.children:
            c.compute_hash(ordered)

        if ordered:
            self.hash = hash(
                (
                    str([hash(n) for n in self.nodes]),
                    str(sorted([hash(c) for c in self.children])),
                )
            )

        else:
            self.hash = hash(
                (
                    str([hash(n) for n in self.nodes]),
                    str([hash(c) for c in self.children]),
                )
            )

    def __hash__(self) -> int:
        if self.hash is None:
            self.compute_hash()

        return self.hash


class Trace:
    def __init__(self, trace_id, start_at: int):
        self.id = trace_id
        self.start_at = start_at
        self.spans_order = []
        self.spans: "Dict[int, Span]" = {}
        self.hash = None

    def compute_hash(self, ordered=False) -> None:
        hashes = [
            hash(self.spans[span_id])
            for span_id in self.spans_order
            if self.spans[span_id].parent is None
        ]

        if ordered:
            hashes.sort()

        self.hash = hash(str(hashes))

    def __hash__(self) -> int:
        if self.hash is None:
            self.compute_hash()

        return self.hash


class DotFormatter:
    def __init__(self, filter: "bool_expr"):
        self.filter = filter
        self.traces_order = []
        self.traces: "Dict[int, Trace]" = {}
        self.log_id = 0

    def add_trace(self, trace_id: int, start_at: int) -> "Trace":
        if trace_id in self.traces:
            trace = self.traces[trace_id]
            trace.start_at = min(start_at, trace.start_at)
            return trace

        self.traces_order += [trace_id]
        self.traces[trace_id] = Trace(trace_id, start_at)
        return self.traces[trace_id]

    def add_span(
        self,
        span_id: int,
        trace_id: int,
        name: str,
        start_at: int,
        end_at: int,
        parent_id: "Optional[int]" = None,
        update_on_conflict=False,
    ) -> "Span":
        trace = self.add_trace(trace_id, start_at)

        if span_id in trace.spans:
            span = trace.spans[span_id]
            span.start_at = min(start_at, span.start_at)
            span.end_at = min(end_at, span.end_at)
            if not update_on_conflict:
                return span

            span.name = name

        else:
            trace.spans_order += [span_id]
            trace.spans[span_id] = Span(span_id, trace, name, start_at, end_at)
            span = trace.spans[span_id]

        if parent_id is not None:
            self.set_span_parent(span, parent_id)

        return span

    def set_span_parent(self, span: "Span", parent_id: int) -> None:
        assert span.parent is None
        parent = self.add_span(
            parent_id,
            span.trace.id,
            f"<span_{span.id} parent>",
            span.start_at,
            span.end_at,
            update_on_conflict=False,
        )

        span.parent = parent
        parent.children += [span]

    def add_log(
        self, span_id: int, trace_id: int, timestamp: int, kwargs: dict
    ) -> "Optional[Log]":
        log = Log(self.log_id, span_id, trace_id, timestamp, kwargs)

        if not self.filter.does_match(log.build_meta()):
            return None

        trace = self.add_trace(trace_id, timestamp)
        span = self.add_span(
            span_id,
            trace_id,
            f"<log_{log.id} parent>",
            timestamp,
            timestamp,
            None,
            update_on_conflict=False,
        )

        span.nodes += [log]
        self.log_id += 1
        return log

    def compute_hashes(self, ordered=False) -> None:
        for trace in self.traces.values():
            trace.compute_hash(ordered)

    def get_traces_order(self, grouped=False) -> "List[int]":
        if grouped:
            return [trace.id for trace in list(set(self.traces.values()))]

        else:
            return self.traces_order

    def vis(self, grouped=False) -> str:
        if len(self.traces) == 0:
            return ""

        res = "digraph D {\n"

        for trace_id in self.get_traces_order(grouped):
            trace = self.traces[trace_id]
            spans = trace.spans

            if grouped:
                trace.compute_hash()

            res += f"subgraph cluster_trace_id_{trace_id} {{\n"
            res += f'label="trace: {trace_id} ({hash(trace)})";\n'
            res += "node [style=filled];\n"

            # print(f"trace_id {trace_id} ({hash(trace)}): {spans}")
            for span_id in DotFormatter.get_spans_order(trace, grouped):
                span = spans[span_id]
                if span.parent is not None:
                    continue
                res += DotFormatter.vis_span(span)
            res += "}\n"
        res += "}\n"

        return res

    @staticmethod
    def get_spans_order(trace: "Trace", grouped=False) -> "List[int]":
        if grouped:
            return [span.id for span in list(set(trace.spans.values()))]

        else:
            return trace.spans_order

    @staticmethod
    def vis_span(span: Span) -> str:
        res = f"subgraph cluster_span_id_{span.id} {{\n"
        res += f'label="span: {span.id} ({hash(span)})";\n'

        for n in span.nodes:
            res += f'{n.id} [label="{str(n)}"];\n'

        if len(span.nodes) > 1:
            res += " -> ".join([str(n.id) for n in span.nodes]) + ";\n"

        for c in span.children:
            res += DotFormatter.vis_span(c)

        res += "}\n"
        return res
