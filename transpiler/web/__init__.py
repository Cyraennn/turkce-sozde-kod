"""Tarayıcı arayüzü: `trc --arayuz` yerel bir sunucu açar ve sayfayı tarayıcıda gösterir."""

from .server import make_server, serve

__all__ = ["make_server", "serve"]
