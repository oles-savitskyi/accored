from typing import Any

from accore.platform.posting.api import DefaultPostingAPI, PostingAPI
from accore.platform.posting.context import DocumentStateProvider, PostingContext, PostingServices
from accore.platform.posting.coordinator import (
    PostingLifecycleOutcome,
    PostingLifecycleResult,
    PostingResultCoordinator,
    PostingResultParticipant,
    PostingResultPlan,
    RegisterPostingPlan,
)
from accore.platform.posting.engine import PostingContextFactory, PostingEngine
from accore.platform.posting.errors import (
    PostingError,
    PostingHandlerError,
    PostingHandlerResolutionError,
    PostingIndeterminateError,
    PostingMovementValidationError,
    PostingPersistenceError,
    PostingValidationError,
)
from accore.platform.posting.events import (
    DocumentPosted,
    DocumentReposted,
    DocumentUnposted,
    NullPostingEventPublisher,
    PostingEventPublisher,
)
from accore.platform.posting.handlers import (
    MappingPostingHandlerResolver,
    PostingHandler,
    PostingHandlerResolver,
)
from accore.platform.posting.movement_set import MovementSet
from accore.platform.posting.register_coordinator import RegisterPostingResultCoordinator
from accore.platform.posting.result import PostingOutcome, PostingResult

__all__ = [
    "CompositePostingResultCoordinator",
    "DefaultPostingAPI",
    "DocumentPosted",
    "DocumentReposted",
    "DocumentStateProvider",
    "DocumentUnposted",
    "MappingPostingHandlerResolver",
    "MovementSet",
    "NullPostingEventPublisher",
    "PostingAPI",
    "PostingContext",
    "PostingContextFactory",
    "PostingEngine",
    "PostingError",
    "PostingEventPublisher",
    "PostingHandler",
    "PostingHandlerError",
    "PostingHandlerResolutionError",
    "PostingHandlerResolver",
    "PostingIndeterminateError",
    "PostingLifecycleOutcome",
    "PostingLifecycleResult",
    "PostingMovementValidationError",
    "PostingOutcome",
    "PostingPersistenceError",
    "PostingResult",
    "PostingResultCoordinator",
    "PostingResultParticipant",
    "PostingResultPlan",
    "PostingServices",
    "PostingValidationError",
    "RegisterPostingPlan",
    "RegisterPostingResultCoordinator",
    "ValuationPostingCoordinator",
]


def __getattr__(name: str) -> Any:
    if name == "CompositePostingResultCoordinator":
        from accore.platform.posting.composite_coordinator import CompositePostingResultCoordinator

        return CompositePostingResultCoordinator
    if name == "ValuationPostingCoordinator":
        from accore.platform.posting.valuation_coordinator import ValuationPostingCoordinator

        return ValuationPostingCoordinator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
