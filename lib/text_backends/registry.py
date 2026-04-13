"""Đăng ký backend văn bản và factory."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from lib.text_backends.base import TextBackend

_BACKEND_FACTORIES: dict[str, Callable[..., TextBackend]] = {}


def register_backend(name: str, factory: Callable[..., TextBackend]) -> None:
    """Đăng ký một hàm factory backend văn bản."""
    _BACKEND_FACTORIES[name] = factory


def create_backend(name: str, **kwargs: Any) -> TextBackend:
    """Tạo instance backend văn bản theo tên."""
    if name not in _BACKEND_FACTORIES:
        raise ValueError(f"Unknown text backend: {name}")
    return _BACKEND_FACTORIES[name](**kwargs)


def get_registered_backends() -> list[str]:
    """Trả về danh sách tên backend đã đăng ký."""
    return list(_BACKEND_FACTORIES.keys())
