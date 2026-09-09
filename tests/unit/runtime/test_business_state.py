from __future__ import annotations

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.runtime.business_state import (
    BusinessStateSnapshot,
)


def make_identifier() -> Identifier:
    return Identifier.new()


def test_empty_snapshot_is_empty() -> None:
    snapshot = BusinessStateSnapshot.empty()

    assert len(snapshot) == 0
    assert list(snapshot) == []
    assert list(snapshot.keys()) == []
    assert list(snapshot.values()) == []
    assert list(snapshot.items()) == []


def test_snapshot_stores_single_business_state() -> None:
    definition_id = make_identifier()
    state_id = make_identifier()

    snapshot = BusinessStateSnapshot(
        {
            definition_id: state_id,
        }
    )

    assert snapshot[definition_id] == state_id
    assert snapshot.get(definition_id) == state_id
    assert definition_id in snapshot
    assert len(snapshot) == 1


def test_snapshot_stores_multiple_independent_dimensions() -> None:
    approval_definition = make_identifier()
    approval_state = make_identifier()

    posting_definition = make_identifier()
    posting_state = make_identifier()

    snapshot = BusinessStateSnapshot(
        {
            approval_definition: approval_state,
            posting_definition: posting_state,
        }
    )

    assert snapshot[approval_definition] == approval_state
    assert snapshot[posting_definition] == posting_state
    assert len(snapshot) == 2


def test_snapshot_is_semantically_equal_to_same_values() -> None:
    definition_id = make_identifier()
    state_id = make_identifier()

    first = BusinessStateSnapshot(
        {
            definition_id: state_id,
        }
    )
    second = BusinessStateSnapshot(
        {
            definition_id: state_id,
        }
    )

    assert first == second


def test_snapshot_equality_is_independent_of_mapping_order() -> None:
    first_definition = make_identifier()
    first_state = make_identifier()

    second_definition = make_identifier()
    second_state = make_identifier()

    first = BusinessStateSnapshot(
        {
            first_definition: first_state,
            second_definition: second_state,
        }
    )
    second = BusinessStateSnapshot(
        {
            second_definition: second_state,
            first_definition: first_state,
        }
    )

    assert first == second


def test_snapshot_is_not_equal_to_other_type() -> None:
    assert BusinessStateSnapshot.empty() != {}
    assert BusinessStateSnapshot.empty() != None


def test_source_mapping_is_defensively_copied() -> None:
    definition_id = make_identifier()
    state_id = make_identifier()
    replacement_state_id = make_identifier()

    source = {
        definition_id: state_id,
    }

    snapshot = BusinessStateSnapshot(source)

    source[definition_id] = replacement_state_id

    assert snapshot[definition_id] == state_id


def test_snapshot_has_no_mutation_api() -> None:
    snapshot = BusinessStateSnapshot.empty()

    assert not hasattr(snapshot, "set")
    assert not hasattr(snapshot, "update")
    assert not hasattr(snapshot, "pop")
    assert not hasattr(snapshot, "clear")
    assert not hasattr(snapshot, "__setitem__")


def test_missing_definition_is_not_substituted() -> None:
    definition_id = make_identifier()
    other_definition_id = make_identifier()
    state_id = make_identifier()

    snapshot = BusinessStateSnapshot(
        {
            definition_id: state_id,
        }
    )

    assert other_definition_id not in snapshot
    assert snapshot.get(other_definition_id) is None

    with pytest.raises(KeyError):
        _ = snapshot[other_definition_id]


def test_missing_definition_can_have_explicit_default() -> None:
    definition_id = make_identifier()
    default_state_id = make_identifier()

    snapshot = BusinessStateSnapshot.empty()

    assert snapshot.get(definition_id, default_state_id) == default_state_id


def test_none_state_value_is_rejected() -> None:
    definition_id = make_identifier()

    with pytest.raises(TypeError, match="state value identity"):
        BusinessStateSnapshot(
            {
                definition_id: None,  # type: ignore[dict-item]
            }
        )


def test_none_definition_identity_is_rejected() -> None:
    state_id = make_identifier()

    with pytest.raises(
        TypeError,
        match="business state definition identity",
    ):
        BusinessStateSnapshot(
            {
                None: state_id,  # type: ignore[dict-item]
            }
        )


@pytest.mark.parametrize(
    "invalid_definition",
    [
        "",
        "approval_status",
        1,
        object(),
    ],
)
def test_invalid_definition_identity_is_rejected(
    invalid_definition: object,
) -> None:
    state_id = make_identifier()

    with pytest.raises(
        TypeError,
        match="business state definition identity",
    ):
        BusinessStateSnapshot(
            {
                invalid_definition: state_id,  # type: ignore[dict-item]
            }
        )


@pytest.mark.parametrize(
    "invalid_state",
    [
        "",
        "approved",
        1,
        object(),
    ],
)
def test_invalid_state_value_identity_is_rejected(
    invalid_state: object,
) -> None:
    definition_id = make_identifier()

    with pytest.raises(
        TypeError,
        match="state value identity",
    ):
        BusinessStateSnapshot(
            {
                definition_id: invalid_state,  # type: ignore[dict-item]
            }
        )


def test_snapshot_contains_only_identity_values() -> None:
    definition_id = make_identifier()
    state_id = make_identifier()

    snapshot = BusinessStateSnapshot(
        {
            definition_id: state_id,
        }
    )

    assert all(isinstance(key, Identifier) for key in snapshot)
    assert all(isinstance(value, Identifier) for value in snapshot.values())


def test_snapshot_has_no_initial_state_semantics() -> None:
    definition_id = make_identifier()
    initial_state_id = make_identifier()

    snapshot = BusinessStateSnapshot.empty()

    assert definition_id not in snapshot
    assert snapshot.get(definition_id) is None
    assert initial_state_id not in snapshot.values()


def test_snapshot_repr_contains_values() -> None:
    definition_id = make_identifier()
    state_id = make_identifier()

    snapshot = BusinessStateSnapshot(
        {
            definition_id: state_id,
        }
    )

    representation = repr(snapshot)

    assert representation.startswith("BusinessStateSnapshot(")
    assert str(definition_id) in representation
    assert str(state_id) in representation
