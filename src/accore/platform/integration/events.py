from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.posting.events import (
    DocumentPosted,
    DocumentReposted,
    DocumentUnposted,
)

from .contract import (
    ContractVersion,
    IntegrationContractIdentity,
    IntegrationContractKind,
    IntegrationSecurityRequirement,
)

_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EventContract:
    """Immutable metadata describing a published business event."""

    identity: IntegrationContractIdentity
    security_requirement: IntegrationSecurityRequirement | None = None

    def __post_init__(self) -> None:
        if self.identity.kind is not IntegrationContractKind.EVENT:
            raise ValueError("Event contract identity must have EVENT kind.")


@dataclass(frozen=True, slots=True)
class EventEnvelope[E]:
    """Immutable envelope around an event payload and its publication metadata."""

    event_identity: IntegrationContractIdentity
    event_id: Identifier
    occurred_at: datetime
    payload: E
    source: str
    correlation_identity: Identifier | None = None

    def __post_init__(self) -> None:
        if self.event_identity.kind is not IntegrationContractKind.EVENT:
            raise ValueError("Event envelope identity must have EVENT kind.")
        if not isinstance(self.event_id, Identifier):
            raise TypeError("Event id must be an Identifier.")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("Event occurrence time must be timezone-aware.")
        if not self.source.strip():
            raise ValueError("Event source must be non-empty.")


class EventPublisher(Protocol):
    """Publishes Integration event envelopes."""

    def publish(self, event: EventEnvelope[object]) -> None:
        """Publish an event to matching subscribers."""
        ...


class EventSubscriber(Protocol):
    """Consumes an Integration event envelope."""

    def handle(self, event: EventEnvelope[object]) -> None:
        """Handle a published event."""
        ...


class InMemoryEventDispatcher:
    """Synchronous, non-durable dispatcher that isolates subscriber failures."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._subscribers: dict[IntegrationContractIdentity, list[EventSubscriber]] = {}

    def subscribe(
        self,
        event_identity: IntegrationContractIdentity,
        subscriber: EventSubscriber,
    ) -> None:
        """Register a subscriber for one exact event contract identity."""
        if event_identity.kind is not IntegrationContractKind.EVENT:
            raise ValueError("Subscriptions require an EVENT contract identity.")
        if not callable(getattr(subscriber, "handle", None)):
            raise TypeError("Subscriber must provide a callable handle(event) method.")
        with self._lock:
            subscribers = self._subscribers.setdefault(event_identity, [])
            if subscriber not in subscribers:
                subscribers.append(subscriber)

    def unsubscribe(
        self,
        event_identity: IntegrationContractIdentity,
        subscriber: EventSubscriber,
    ) -> bool:
        """Remove a subscriber; return whether it was registered."""
        with self._lock:
            subscribers = self._subscribers.get(event_identity)
            if not subscribers or subscriber not in subscribers:
                return False
            subscribers.remove(subscriber)
            if not subscribers:
                del self._subscribers[event_identity]
            return True

    def publish(self, event: EventEnvelope[object]) -> None:
        """Deliver synchronously to a snapshot of exact-identity subscribers."""
        with self._lock:
            subscribers = tuple(self._subscribers.get(event.event_identity, ()))
        for subscriber in subscribers:
            try:
                subscriber.handle(event)
            except Exception:
                _logger.exception(
                    "Integration event subscriber failed for event %s (%s)",
                    event.event_id,
                    event.event_identity,
                )


_DEFAULT_POSTING_EVENT_IDENTITIES: dict[type[object], IntegrationContractIdentity] = {
    DocumentPosted: IntegrationContractIdentity(
        namespace="accore.posting",
        name="DocumentPosted",
        version=ContractVersion(1, 0),
        kind=IntegrationContractKind.EVENT,
    ),
    DocumentUnposted: IntegrationContractIdentity(
        namespace="accore.posting",
        name="DocumentUnposted",
        version=ContractVersion(1, 0),
        kind=IntegrationContractKind.EVENT,
    ),
    DocumentReposted: IntegrationContractIdentity(
        namespace="accore.posting",
        name="DocumentReposted",
        version=ContractVersion(1, 0),
        kind=IntegrationContractKind.EVENT,
    ),
}


class PostingEventBridge:
    """Adapts existing Posting events to Integration event envelopes."""

    def __init__(
        self,
        event_publisher: EventPublisher,
        event_identities: dict[type[object], IntegrationContractIdentity] | None = None,
        *,
        source: str = "accore.posting",
    ) -> None:
        if not source.strip():
            raise ValueError("Posting event source must be non-empty.")
        self._event_publisher = event_publisher
        self._event_identities = dict(
            _DEFAULT_POSTING_EVENT_IDENTITIES if event_identities is None else event_identities
        )
        if any(
            identity.kind is not IntegrationContractKind.EVENT
            for identity in self._event_identities.values()
        ):
            raise ValueError("Posting event mappings must use EVENT contract identities.")
        self._source = source

    def publish(self, event: object) -> None:
        """Translate supported Posting events and ignore unrelated event types."""
        identity = self._event_identities.get(type(event))
        if identity is None:
            return
        envelope = EventEnvelope(
            event_identity=identity,
            event_id=Identifier.new(),
            occurred_at=datetime.now(UTC),
            payload=event,
            source=self._source,
        )
        self._event_publisher.publish(envelope)


__all__ = [
    "EventContract",
    "EventEnvelope",
    "EventPublisher",
    "EventSubscriber",
    "InMemoryEventDispatcher",
    "IntegrationSecurityRequirement",
    "PostingEventBridge",
]
