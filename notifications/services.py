from notifications.models import Notification


def notify(recipient, type, message, url):
    return Notification.objects.create(
        recipient=recipient, type=type, message=message, url=url
    )
