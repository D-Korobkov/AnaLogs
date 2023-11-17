import re
from io import StringIO
from typing import List

from opentelemetry.model import Trace


def format_dot(traces: List[Trace]) -> str:
    dot_notation = StringIO()
    dot_notation.write('digraph {\n')
    dot_notation.write('compound=true;\n')
    for t_idx, trace in enumerate(traces):
        dot_notation.write(f'\tsubgraph cluster_trace_{t_idx} {{\n')
        dot_notation.write(f'\t\tlabel="Trace ID: {trace.trace_id}";\n')
        dot_notation.write(f'\t\tlabel="Duration: {(trace.unix_nano_end_at - trace.unix_nano_start_at) / 1_000_000}ms";\n')
        for s_idx, span in enumerate(trace.spans):
            dot_notation.write(f'\t\tsubgraph cluster_span_{span.span_id} {{\n')
            dot_notation.write(f'\t\tlabel="Span ID: {span.span_id}\\nName: {span.name}";\n')
            dot_notation.write(f'\t\t\tspan_begin_{span.span_id} [label="", style=invis];\n')
            for l_idx, log in enumerate(span.logs):
                dot_notation.write(
                    f'\t\t\tspan_{s_idx}_log_{l_idx} [label="{re.escape(str(log.keyvalues))}", shape=rectangle];\n')
            dot_notation.write(f'\t\t\tspan_end_{span.span_id} [label="", style=invis];\n')

            for l_idx in range(len(span.logs)):
                if 0 < l_idx < len(span.logs):
                    dot_notation.write(f'\t\t\tspan_{s_idx}_log_{l_idx - 1} -> span_{s_idx}_log_{l_idx};\n')
                if l_idx == 0:
                    dot_notation.write(f'\t\t\tspan_begin_{span.span_id} -> span_{s_idx}_log_{l_idx} [style=invis];\n')
                if l_idx + 1 == len(span.logs):
                    dot_notation.write(f'\t\t\tspan_{s_idx}_log_{l_idx} -> span_end_{span.span_id} [style=invis];\n')

            dot_notation.write('\t\t}\n')
        dot_notation.write("\t}\n")
        for s_idx, span in enumerate(trace.spans):
            if span.parent_span_id:
                dot_notation.write(
                    f'\tspan_end_{span.parent_span_id} -> span_begin_{span.span_id} [minlen=2, ltail=cluster_span_{span.parent_span_id}, lhead=cluster_span_{span.span_id}];\n')

    dot_notation.write("}")

    return dot_notation.getvalue()
