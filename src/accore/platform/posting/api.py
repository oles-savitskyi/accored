from __future__ import annotations

from typing import Protocol

from accore.platform.object import ObjectInstance

from .engine import PostingEngine
from .identity import PostingOperationIdentity
from .result import PostingResult


class PostingAPI(Protocol):
    def post(self, document: ObjectInstance) -> PostingResult: ...
    def unpost(self, document: ObjectInstance) -> PostingResult: ...
    def repost(self, document: ObjectInstance) -> PostingResult: ...
    def recover(self, operation_identity: PostingOperationIdentity) -> PostingResult: ...


class DefaultPostingAPI:
    def __init__(self, engine: PostingEngine) -> None:
        self._engine = engine

    def post(self, document: ObjectInstance) -> PostingResult:
        return self._engine.post(document)

    def unpost(self, document: ObjectInstance) -> PostingResult:
        return self._engine.unpost(document)

    def repost(self, document: ObjectInstance) -> PostingResult:
        return self._engine.repost(document)

    def recover(self, operation_identity: PostingOperationIdentity) -> PostingResult:
        return self._engine.recover(operation_identity)
