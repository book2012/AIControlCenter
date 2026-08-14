"""Replaceable notification transport observations."""

from .telegram import TelegramNotificationAdapter, build_telegram_notification_adapter

__all__ = ("TelegramNotificationAdapter", "build_telegram_notification_adapter")
