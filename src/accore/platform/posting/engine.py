from __future__ import annotations

from accore.platform.object import ObjectInstance
from accore.platform.persistence.errors import PersistenceError, PersistenceIndeterminateError
from accore.platform.registers import MovementValidator

from .context import PostingClock, PostingContext, PostingPreparationContext, PostingServices
from .coordinator import (
    PostingLifecycleOutcome,
    PostingLifecycleResult,
    PostingResultCoordinator,
)
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
from .identity import DefaultPostingOperationIdentityFactory, PostingOperationIdentityFactory
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
        operation_identity_factory: PostingOperationIdentityFactory | None = None,
    ) -> None:
        self._handler_resolver = handler_resolver
        self._context_factory = context_factory
        self._movement_validator = movement_validator
        self._coordinator = result_coordinator
        self._events = event_publisher or NullPostingEventPublisher()
        self._operation_identity_factory = (
            operation_identity_factory or DefaultPostingOperationIdentityFactory()
        )

    def post(self, document: ObjectInstance) -> PostingResult:
        operation_identity = self._operation_identity_factory.new()
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
            plan = self._coordinator.prepare(
                document,
                movement_set,
                PostingPreparationContext(operation_identity=operation_identity),
            )
            result = self._coordinator.establish(document, movement_set, plan, operation_identity)
            return self._result_from_lifecycle(result, DocumentPosted(document.identity))
        except PersistenceIndeterminateError as exc:
            return PostingResult.indeterminate(PostingIndeterminateError(str(exc)))
        except PersistenceError as exc:
            return PostingResult.failure(PostingPersistenceError(str(exc)))
        except Exception as exc:  # noqa: BLE001
            return PostingResult.failure(PostingPersistenceError(str(exc)))

    def unpost(self, document: ObjectInstance) -> PostingResult:
        operation_identity = self._operation_identity_factory.new()
        try:
            result = self._coordinator.remove(document, operation_identity)
            return self._result_from_lifecycle(result, DocumentUnposted(document.identity))
        except PersistenceIndeterminateError as exc:
            return PostingResult.indeterminate(PostingIndeterminateError(str(exc)))
        except PersistenceError as exc:
            return PostingResult.failure(PostingPersistenceError(str(exc)))
        except Exception as exc:  # noqa: BLE001
            return PostingResult.failure(PostingPersistenceError(str(exc)))

    def repost(self, document: ObjectInstance) -> PostingResult:
        operation_identity = self._operation_identity_factory.new()
        try:
            context = self._context_factory.create(document)
            handler = self._handler_resolver.resolve(document)
            movement_set = handler.post(context)
            self._movement_validator.validate(movement_set)
        except Exception as exc:  # noqa: BLE001
            return PostingResult.failure(PostingHandlerError(str(exc)))

        try:
            plan = self._coordinator.prepare(
                document,
                movement_set,
                PostingPreparationContext(
                    operation_identity=operation_identity,
                    replacement_document_identity=document.identity,
                ),
            )
            removal = self._coordinator.remove(document, operation_identity)
            if removal.outcome is not PostingLifecycleOutcome.SUCCESS:
                return self._result_from_lifecycle(removal, None)
            establishment = self._coordinator.establish(
                document, movement_set, plan, operation_identity
            )
            return self._result_from_lifecycle(establishment, DocumentReposted(document.identity))
        except PersistenceIndeterminateError as exc:
            return PostingResult.indeterminate(PostingIndeterminateError(str(exc)))
        except PersistenceError as exc:
            return PostingResult.failure(PostingPersistenceError(str(exc)))
        except Exception as exc:  # noqa: BLE001
            return PostingResult.failure(PostingPersistenceError(str(exc)))

    def _result_from_lifecycle(
        self,
        result: PostingLifecycleResult,
        event: object | None,
    ) -> PostingResult:
        if result.outcome is PostingLifecycleOutcome.INDETERMINATE:
            return PostingResult.indeterminate(
                PostingIndeterminateError(str(result.error))
                if result.error is not None
                else PostingIndeterminateError("Posting lifecycle outcome is indeterminate.")
            )
        if result.outcome is PostingLifecycleOutcome.FAILURE:
            return PostingResult.failure(
                PostingPersistenceError(str(result.error))
                if result.error is not None
                else PostingPersistenceError("Posting lifecycle operation failed.")
            )
        if event is not None:
            self._events.publish(event)
        return PostingResult.success()
