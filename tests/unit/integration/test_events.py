from __future__ import annotations

from datetime import UTC, datetime

import pytest

from accore.platform.foundation import Identifier
from accore.platform.integration import (
    ContractVersion,
    EventContract,
    EventEnvelope,
    InMemoryEventDispatcher,
    IntegrationContractIdentity,
    IntegrationContractKind,
    IntegrationSecurityRequirement,
    PostingEventBridge,
)
from accore.platform.posting import DocumentPosted, DocumentReposted, DocumentUnposted
from accore.platform.security import SecurityObjectIdentity, SecurityOperation


def event_identity(name: str = "DocumentPosted") -> IntegrationContractIdentity:
    return IntegrationContractIdentity(
        namespace="tests.posting",
        name=name,
        version=ContractVersion(1, 0),
        kind=IntegrationContractKind.EVENT,
    )


def envelope(
    identity: IntegrationContractIdentity | None = None,
    payload: object = None,
) -> EventEnvelope[object]:
    return EventEnvelope(
        event_identity=identity or event_identity(),
        event_id=Identifier.new(),
        occurred_at=datetime.now(UTC),
        payload=payload,
        source="tests",
    )


class RecordingSubscriber:
    def __init__(self) -> None:
        self.events: list[EventEnvelope[object]] = []

    def handle(self, event: EventEnvelope[object]) -> None:
        self.events.append(event)


class FailingSubscriber:
    def handle(self, event: EventEnvelope[object]) -> None:
        raise RuntimeError("subscriber failure")


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[EventEnvelope[object]] = []

    def publish(self, event: EventEnvelope[object]) -> None:
        self.events.append(event)


def test_event_contract_requires_event_kind() -> None:
    identity = IntegrationContractIdentity(
        "tests", "NotAnEvent", ContractVersion(1, 0), IntegrationContractKind.QUERY
    )

    with pytest.raises(ValueError, match="EVENT"):
        EventContract(identity)


def test_event_contract_accepts_security_requirement() -> None:
    requirement = IntegrationSecurityRequirement(
        target=SecurityObjectIdentity("integration_event", "DocumentPosted"),
        operation=SecurityOperation.READ,
    )

    contract = EventContract(event_identity(), requirement)

    assert contract.identity == event_identity()
    assert contract.security_requirement == requirement


def test_event_envelope_requires_event_identity_and_aware_time() -> None:
    with pytest.raises(ValueError, match="EVENT"):
        EventEnvelope(
            event_identity=IntegrationContractIdentity(
                "tests",
                "Command",
                ContractVersion(1, 0),
                IntegrationContractKind.COMMAND,
            ),
            event_id=Identifier.new(),
            occurred_at=datetime.now(UTC),
            payload={},
            source="tests",
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        EventEnvelope(
            event_identity=event_identity(),
            event_id=Identifier.new(),
            occurred_at=datetime(2026, 1, 1),  # noqa: DTZ001
            payload={},
            source="tests",
        )


def test_event_envelope_requires_source() -> None:
    with pytest.raises(ValueError, match="source"):
        EventEnvelope(
            event_identity=event_identity(),
            event_id=Identifier.new(),
            occurred_at=datetime.now(UTC),
            payload={},
            source="  ",
        )


def test_dispatcher_routes_only_matching_identity() -> None:
    dispatcher = InMemoryEventDispatcher()
    subscriber = RecordingSubscriber()
    dispatcher.subscribe(event_identity(), subscriber)

    matching = envelope(payload={"value": 1})
    non_matching = envelope(event_identity("DocumentUnposted"))
    dispatcher.publish(matching)
    dispatcher.publish(non_matching)

    assert subscriber.events == [matching]


def test_dispatcher_deduplicates_subscriptions_and_supports_unsubscribe() -> None:
    dispatcher = InMemoryEventDispatcher()
    subscriber = RecordingSubscriber()
    dispatcher.subscribe(event_identity(), subscriber)
    dispatcher.subscribe(event_identity(), subscriber)

    dispatcher.publish(envelope())
    assert len(subscriber.events) == 1
    assert dispatcher.unsubscribe(event_identity(), subscriber) is True
    assert dispatcher.unsubscribe(event_identity(), subscriber) is False
    dispatcher.publish(envelope())
    assert len(subscriber.events) == 1


def test_dispatcher_isolates_subscriber_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    dispatcher = InMemoryEventDispatcher()
    later_subscriber = RecordingSubscriber()
    dispatcher.subscribe(event_identity(), FailingSubscriber())
    dispatcher.subscribe(event_identity(), later_subscriber)

    event = envelope()
    with caplog.at_level("ERROR"):
        dispatcher.publish(event)

    assert later_subscriber.events == [event]
    assert "Integration event subscriber failed" in caplog.text


def test_dispatcher_rejects_non_event_subscription() -> None:
    dispatcher = InMemoryEventDispatcher()
    command_identity = IntegrationContractIdentity(
        "tests", "Command", ContractVersion(1, 0), IntegrationContractKind.COMMAND
    )

    with pytest.raises(ValueError, match="EVENT"):
        dispatcher.subscribe(command_identity, RecordingSubscriber())


def test_posting_bridge_translates_supported_posting_events() -> None:
    publisher = RecordingPublisher()
    bridge = PostingEventBridge(publisher)
    posting_events = [
        DocumentPosted(Identifier.new()),
        DocumentUnposted(Identifier.new()),
        DocumentReposted(Identifier.new()),
    ]

    for posting_event in posting_events:
        bridge.publish(posting_event)

    assert [event.event_identity.name for event in publisher.events] == [
        "DocumentPosted",
        "DocumentUnposted",
        "DocumentReposted",
    ]
    assert all(event.event_identity.namespace == "accore.posting" for event in publisher.events)
    assert all(
        event.event_identity.kind is IntegrationContractKind.EVENT for event in publisher.events
    )
    assert [event.payload for event in publisher.events] == posting_events
    assert all(event.source == "accore.posting" for event in publisher.events)
    assert all(event.event_id for event in publisher.events)
    assert all(event.occurred_at.tzinfo is not None for event in publisher.events)


def test_posting_bridge_ignores_unmapped_event_types() -> None:
    publisher = RecordingPublisher()
    bridge = PostingEventBridge(publisher)

    bridge.publish(object())

    assert publisher.events == []


def test_posting_bridge_accepts_custom_event_identity_and_source() -> None:
    publisher = RecordingPublisher()
    identity = event_identity("PostedV2")
    bridge = PostingEventBridge(
        publisher,
        {DocumentPosted: identity},
        source="standard.posting",
    )
    event = DocumentPosted(Identifier.new())

    bridge.publish(event)

    assert publisher.events[0].event_identity == identity
    assert publisher.events[0].source == "standard.posting"


def test_posting_bridge_rejects_non_event_mapping() -> None:
    publisher = RecordingPublisher()
    command_identity = IntegrationContractIdentity(
        "tests", "Command", ContractVersion(1, 0), IntegrationContractKind.COMMAND
    )

    with pytest.raises(ValueError, match="EVENT"):
        PostingEventBridge(publisher, {DocumentPosted: command_identity})


def test_posting_bridge_rejects_empty_source() -> None:
    with pytest.raises(ValueError, match="source"):
        PostingEventBridge(RecordingPublisher(), source=" ")
