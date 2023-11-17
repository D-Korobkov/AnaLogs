protoc --python_out=pyi_out:. \
 opentelemetry/proto/common/v1/common.proto \
 opentelemetry/proto/resource/v1/resource.proto \
 opentelemetry/proto/logs/v1/logs.proto \
 opentelemetry/proto/metrics/v1/metrics.proto \
 opentelemetry/proto/trace/v1/trace.proto
