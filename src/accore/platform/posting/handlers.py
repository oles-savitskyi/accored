from __future__ import annotations

from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.object import ObjectInstance

from .context import PostingContext
from .movement_set import MovementSet


class PostingHandler(Protocol):
    def post(self, context: PostingContext) -> MovementSet: ...


class PostingHandlerResolver(Protocol):
    def resolve(self, document: ObjectInstance) -> PostingHandler: ...


class MappingPostingHandlerResolver:
    def __init__(self, handlers: dict[Identifier, PostingHandler]) -> None:
        self._handlers = dict(handlers)

    def resolve(self, document: ObjectInstance) -> PostingHandler:
        try:
            return self._handlers[document.object_type.metadata_identity()]
        except KeyError as exc:
            raise KeyError("No Posting Handler is registered for the document type.") from exc
