from __future__ import annotations

from accore.platform.object import ObjectInstance
from accore.platform.persistence.errors import PersistenceError, PersistenceIndeterminateError
from accore.platform.registers import MovementValidator

from .context import PostingClock, PostingContext, PostingServices
from .coordinator import PostingResultCoordinator
from .errors import (
    PostingHandlerError,
    PostingHandlerResolutionError,
    PostingIndeterminateError,
    PostingMovementValidationError,
    PostingPersistenceError,
)
from .events import (
    DocumentPosted,
    DocumentReposted,
    DocumentUnposted,
    NullPostingEventPublisher,
    PostingEventPublisher,
)
from .handlers import PostingHandlerResolver
from .result import PostingResult


class PostingContextFactory:
    def __init__(self, services: PostingServices, clock: PostingClock) -> None:
        self._services = services
        self._clock = clock

    def create(self, document: ObjectInstance) -> PostingContext:
        return PostingContext(
            document=document,
            metadata=document.context.runtime_context.configuration.published_metadata,
            services=self._services,
            clock=self._clock,
        )


class PostingEngine:
    def __init__(
        self,
        handler_resolver: PostingHandlerResolver,
        context_factory: PostingContextFactory,
        movement_validator: MovementValidator,
        result_coordinator: PostingResultCoordinator,
        event_publisher: PostingEventPublisher | None = None,
    ) -> None:
        self._handler_resolver = handler_resolver
        self._context_factory = context_factory
        self._movement_validator = movement_validator
        self._coordinator = result_coordinator
        self._events = event_publisher or NullPostingEventPublisher()

    def post(self, document: ObjectInstance) -> PostingResult:
        try:
            context = self._context_factory.create(document)
            handler = self._handler_resolver.resolve(document)
        except Exception as exc:  # noqa: BLE001
            return PostingResult.failure(PostingHandlerResolutionError(str(exc)))

        try:
            movement_set = handler.post(context)
        except Exception as exc:  # noqa: BLE001
            return PostingResult.failure(PostingHandlerError(str(exc)))

        try:
            self._movement_validator.validate(movement_set)
        except Exception as exc:  # noqa: BLE001
            return PostingResult.failure(PostingMovementValidationError(str(exc)))

        try:
            self._coordinator.establish(document, movement_set)
        except PersistenceIndeterminateError as exc:
            return PostingResult.indeterminate(PostingIndeterminateError(str(exc)))
        except PersistenceError as exc:
            return PostingResult.failure(PostingPersistenceError(str(exc)))
        except Exception as exc:  # noqa: BLE001
            return PostingResult.failure(PostingPersistenceError(str(exc)))

        self._events.publish(DocumentPosted(document.identity))
        return PostingResult.success()

    def unpost(self, document: ObjectInstance) -> PostingResult:
        try:
            self._coordinator.remove(document)
        except PersistenceIndeterminateError as exc:
            return PostingResult.indeterminate(PostingIndeterminateError(str(exc)))
        except PersistenceError as exc:
            return PostingResult.failure(PostingPersistenceError(str(exc)))
        except Exception as exc:  # noqa: BLE001
            return PostingResult.failure(PostingPersistenceError(str(exc)))

        self._events.publish(DocumentUnposted(document.identity))
        return PostingResult.success()

    def repost(self, document: ObjectInstance) -> PostingResult:
        try:
            context = self._context_factory.create(document)
            handler = self._handler_resolver.resolve(document)
            movement_set = handler.post(context)
            self._movement_validator.validate(movement_set)
            self._coordinator.establish(document, movement_set)
        except PersistenceIndeterminateError as exc:
            return PostingResult.indeterminate(PostingIndeterminateError(str(exc)))
        except PersistenceError as exc:
            return PostingResult.failure(PostingPersistenceError(str(exc)))
        except Exception as exc:  # noqa: BLE001
            return PostingResult.failure(PostingHandlerError(str(exc)))

        self._events.publish(DocumentReposted(document.identity))
        return PostingResult.success()
