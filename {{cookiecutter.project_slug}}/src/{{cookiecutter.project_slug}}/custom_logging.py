# The logging setup in this file uses structlog-based formatter (`ProcessorFormatter`) to render both `logging`
# and `structlog` log entries, and then send rendered log strings to `logging` handlers. See
# https://www.structlog.org/en/stable/standard-library.html#rendering-using-structlog-based-formatters-within-logging
import logging

import structlog


shared_processors = [
    # If log level is too low, abort pipeline and throw away log entry.
    structlog.stdlib.filter_by_level,
    # Add the name of the logger to event dict.
    structlog.stdlib.add_logger_name,
    # Add log level to event dict.
    structlog.stdlib.add_log_level,
    # Perform %-style formatting.
    structlog.stdlib.PositionalArgumentsFormatter(),
    # Add a timestamp in ISO 8601 format.
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    # If the "stack_info" key in the event dict is true, remove it and
    # render the current stack trace in the "stack" key.
    structlog.processors.StackInfoRenderer(),
    # If the "exc_info" key in the event dict is either true or a
    # sys.exc_info() tuple, remove "exc_info" and render the exception
    # with traceback into the "exception" key.
    structlog.processors.format_exc_info,
    # If some value is in bytes, decode it to a Unicode str.
    structlog.processors.UnicodeDecoder(),
    # Add callsite parameters.
    structlog.processors.CallsiteParameterAdder(
        {
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
            structlog.processors.CallsiteParameter.THREAD_NAME,
            structlog.processors.CallsiteParameter.PROCESS_NAME,
        }
    ),
]


def setup_logging():
    structlog.configure(
        processors=shared_processors
        + [
            # This is needed to convert the event dict to data that can be processed by the `ProcessorFormatter`
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter
        ],
        # `logger_factory` is used to create wrapped loggers that are used for
        # OUTPUT. This one returns a `logging.Logger`. The final value (a JSON
        # string) from the final processor (`JSONRenderer`) will be passed to
        # the method of the same name as that you've called on the bound logger.
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Effectively freeze configuration after creating the first bound logger.
        cache_logger_on_first_use=True,
    )

    # The `ProcessorFormatter` has a `foreign_pre_chain` argument which is responsible for adding properties to
    # events from the standard library – in other words, those that do not originate from a structlog logger – and
    # which should in general match the processors argument to structlog.configure() so you get a consistent output.
    foreign_pre_chain = shared_processors + [
        # Add extra attributes of LogRecord objects to the event dictionary so that values passed in the extra
        # parameter of log methods pass through to log output.
        structlog.stdlib.ExtraAdder()
    ]

    root_logger = logging.getLogger()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "plain": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        # Remove _record & _from_structlog from the event dict.
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        structlog.dev.ConsoleRenderer(colors=False),
                    ],
                    "foreign_pre_chain": foreign_pre_chain,
                    "logger": root_logger,
                },
                "colored": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        # Remove _record & _from_structlog from the event dict.
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        structlog.dev.ConsoleRenderer(colors=True),
                    ],
                    "foreign_pre_chain": foreign_pre_chain,
                    "logger": root_logger,
                },
            },
            "handlers": {
                "default": {
                    "level": "INFO",
                    "class": "logging.StreamHandler",
                    "formatter": "colored",
                },
                "file": {
                    "level": "INFO",
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "filename": "app.log",
                    "formatter": "plain",
                    "when": "midnight",
                    "interval": 1,
                    "backupCount": 7,
                    "encoding": "utf-8",
                },
            },
            "root": {"handlers": ["default", "file"], "level": "DEBUG", "propagate": True},
            "loggers": {"uvicorn": {"level": "INFO", "handlers": ["default", "file"], "propagate": False}},
        }
    )
