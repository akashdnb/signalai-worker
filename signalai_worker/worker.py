import asyncio
import logging

from signalai_worker.runtime import WorkerRuntime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


async def main() -> None:
    runtime = WorkerRuntime()
    loop = asyncio.get_running_loop()

    for signal_name in ("SIGINT", "SIGTERM"):
        try:
            import signal

            loop.add_signal_handler(getattr(signal, signal_name), runtime.stop)
        except (NotImplementedError, RuntimeError):
            pass

    await runtime.run()


if __name__ == "__main__":
    asyncio.run(main())
