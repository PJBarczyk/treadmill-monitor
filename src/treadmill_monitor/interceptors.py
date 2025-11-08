import sys
from collections.abc import Callable, Iterable

from treadmill_monitor.serializers import UpdateSerializer

from loguru import logger

from treadmill_monitor.gui import Gui
from treadmill_monitor.models import TreadmillUpdate


class UpdateInterceptor:
    """
    Base class for treadmill update interceptors.
    """

    def intercept(
        self, update: TreadmillUpdate, next: Callable[[TreadmillUpdate], None]
    ):
        """
        Intercept a treadmill update, potentially modifying its key, value, dropping it or performing side effects.
        """
        next(update)


def run_interceptor_chain(
    interceptors: Iterable[UpdateInterceptor],
    update: TreadmillUpdate,
):
    """Run a chain of update interceptors."""

    def build_chain(
        interceptors: Iterable[UpdateInterceptor],
        final: Callable[[TreadmillUpdate], None],
    ) -> Callable[[TreadmillUpdate], None]:
        if not interceptors:
            return final

        first, *rest = interceptors

        def next_in_chain(update: TreadmillUpdate):
            first.intercept(update, build_chain(rest, final))

        return next_in_chain

    def final_handler(update: TreadmillUpdate):
        pass  # No-op final handler

    chain = build_chain(interceptors, final_handler)
    chain(update)


class LoggingInterceptor(UpdateInterceptor):
    def __init__(self, level: str | int = "DEBUG"):
        self.level = level

    def intercept(
        self, update: TreadmillUpdate, next: Callable[[TreadmillUpdate], None]
    ):
        logger.log(self.level, f"Treadmill update: {update.key} = {update.value}")
        next(update)


class ResumableInterceptor(UpdateInterceptor):
    """
    Interceptor that makes certain treadmill update values resumable by accumulating their values across resets.
    """

    def __init__(self, keys_to_accumulate: Iterable[str]):
        self.keys_to_acumulate = keys_to_accumulate
        self.active = dict()
        self.accumulate = dict()

    def intercept(
        self, update: TreadmillUpdate, next: Callable[[TreadmillUpdate], None]
    ):
        if update.key not in self.keys_to_acumulate:
            next(update)
            return

        if update.value == 0 and self.active.get(update.key, False):
            last_value = self.active.pop(update.key)
            self.accumulate[update.key] = (
                self.accumulate.get(update.key, 0) + last_value
            )
            logger.info(
                f"Detected reset for '{update.key}'. Accumulated value is now {self.accumulate[update.key]}."
            )

        self.active[update.key] = update.value
        next(
            TreadmillUpdate(
                timestamp=update.timestamp,
                key=update.key,
                value=update.value + self.accumulate.get(update.key, 0),
            )
        )


class StdoutInterceptor(UpdateInterceptor):
    """
    Interceptor that logs updates to stdout in CSV format of `timestamp,key,value`.
    """

    def __init__(self, output_format: UpdateSerializer):
        self.output_format = output_format

    def intercept(
        self, update: TreadmillUpdate, next: Callable[[TreadmillUpdate], None]
    ):
        serialized = self.output_format.serialize(update)
        print(serialized, file=sys.stdout, flush=True)
        next(update)


class GuiUpdateInterceptor(UpdateInterceptor):
    """
    Interceptor that pushes updates to a GUI monitor.
    """

    def __init__(self, gui: Gui):
        self.gui = gui

    def intercept(
        self, update: TreadmillUpdate, next: Callable[[TreadmillUpdate], None]
    ):
        self.gui.push_update(update)
        next(update)
