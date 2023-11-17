#!/bin/bash
python3 ./analogs.py --input-file="./examples/mobile/example.txt" --schema="./workaround/rybchits/schema.yaml" --log-source="android" --output-file="mobile-out.dot"
#python3 ./analogs.py --input-file="examples/opentelemetry/exported-data.json" --log-source="open-telemetry" --query='trace_id = "35667d967d8f04ee312a36f3e600b955"' --output-file="otel-out.dot"