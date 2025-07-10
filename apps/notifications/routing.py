from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

websocket_urlpatterns = [
    # Add your websocket consumers here
    # Example: re_path(r'ws/somepath/$', SomeConsumer.as_asgi()),
]
