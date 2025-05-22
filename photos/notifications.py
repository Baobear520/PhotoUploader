import os
from abc import ABC, abstractmethod
import requests
from django.conf import settings


class NotificationSender(ABC):
    @abstractmethod
    def send(self, message: str) -> bool:
        """Отправляет сообщение. В классе-наследнике возвращает True при успехе."""
        pass


class TelegramSender(NotificationSender):
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    def send(self, message: str) -> bool:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message
        }
        response = requests.post(url, json=payload)
        return response.status_code == 200

class SlackSender(NotificationSender):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, message: str) -> bool:
        response = requests.post(self.webhook_url, json={"text": message})

        return response.status_code == 200


telegram_sender = TelegramSender(
    token=settings.TLG_BOT_TOKEN,
    chat_id=settings.TLG_CHAT_ID
)
slack_sender = SlackSender(
    webhook_url=settings.SLACK_WEBHOOK_URL
)

