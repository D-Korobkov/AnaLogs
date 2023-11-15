# Тестовые данные

## Где взять еще примеров

### Детский путь

Посмотреть примеры трейсов, логов, метрик
можно [тут](https://github.com/open-telemetry/opentelemetry-proto/blob/v1.0.0/examples/trace.json).
Не очень информативно, но хоть что-то. В этом же репозитории лежат `.proto` файлы с моделями событий.

### Путь самураев

Клонируем себе [репозиторий](https://github.com/open-telemetry/opentelemetry-demo) с демо-версией проекта.

#### Первый локальный запуск

- Команда `make start` запустит сборку всех контейнеров. Вероятно, оно упадет.
- Патчим по необходимости, до тех пор пока не запустится. Ниже описан опыт автора докмуента:
    - заменил образ прометеуса
      в `docker-compose.yml` – `quay.io/prometheus/prometheus:v2.47.2 --> bitnami/prometheus:latest`;
    - отключил health-чеки в `docker-compose.yml` у кафки – `test: exit 0`;
    - на несовместимость `opensearchproject/data-prepper` с `arm64` можно забить;
    - если очень хочется, можно попробовать при помощи `colima` запустить, но не советую;
    - если не работает `docker compose`, то во всем `Makefile` замените эту последовательность на `docker-compose`.
- Когда оно наконец-таки запустится, можно потыкать кнопки в интернет-магазине, но необязательно, ведь `load-generator`
  уже создает вам трафик.
- Команда `make stop` остановит все контейнеры.

#### Собрать файл со спанами и логами

В базовом варианте ваши трейсы попадают в jaeger, логи – в opensearch, метрики – в прометеус. Есть несколько вариантов
собрать эти сообщения в исходном виде:

- Пишем свой бекенд, который будет принимать http/grpc запросы или слушать кафку или ... (правильно, но сложно)
- Используем готовый [fileexporter](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/fileexporter):
  - в демо-проекте переходим в папку `src/otelcollector`;
  - открываем файл `otelcol-config-extras.yml`;
  - переопределяем экспортер и вновь исполняем `make run`.

```yaml
exporters:
  file/rotation_with_default_settings:
    path: /etc/exported-data.json
    rotation:
    format: json
    flush_interval: 5

service:
  pipelines:
    traces:
      exporters: [ spanmetrics, file/rotation_with_default_settings ]
    logs:
      exporters: [ file/rotation_with_default_settings, debug ]
```
