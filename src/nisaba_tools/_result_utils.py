from __future__ import annotations

from typing import Protocol


class TextOutputResult(Protocol):
    supported: bool
    output_text: str | None
    reason: str | None


def output_text_or_raise(result: TextOutputResult, message: str) -> str:
    if not result.supported or result.output_text is None:
        if result.reason is not None:
            raise ValueError(result.reason)
        raise ValueError(message)
    return result.output_text
