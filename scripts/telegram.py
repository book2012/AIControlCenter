import time

from core.adapters.telegram.polling import TelegramPollingBot
from core.runtime.lifecycle import GracefulLifecycle


if __name__ == "__main__":
    lifecycle = GracefulLifecycle()
    lifecycle.install_signal_handlers()

    bot = TelegramPollingBot()

    while not lifecycle.should_stop():
        bot.run_once()
        time.sleep(bot.interval)
