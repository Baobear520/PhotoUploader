import os
from abc import ABC, abstractmethod
import requests
from django.conf import settings


class NotificationSender(ABC):
    @abstractmethod
    def send(self, message: str) -> bool:
        """Отправляет сообщение. В классе-наследнике возвращает True при успехе."""
        pass


class TelegramAlert(NotificationSender):
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

class SlackAlert(NotificationSender):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, message: str) -> bool:
        response = requests.post(self.webhook_url, json={"text": message})

        return response.status_code == 200


# Фабрика для удобного создания sender'ов
def send_alert(sender: NotificationSender, message: str) -> bool:
    return sender.send(message)


telegram_sender = TelegramAlert(
    token=settings.TLG_BOT_TOKEN,
    chat_id=settings.TLG_CHAT_ID
)
