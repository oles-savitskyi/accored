from __future__ import annotations

from inspect import signature

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.persistence import (
    ObjectDeletion,
    ObjectPersistence,
    PersistentBusinessState,
    PersistentFieldState,
    PersistentObject,
    PersistentObjectState,
    PersistentReferenceState,
    PersistentSystemFieldState,
)


def test_persistent_object_representation_is_immutable() -> None:
    obj = PersistentObject(
        identity=Identifier.new(),
        object_type_identity=Identifier.new(),
        state=PersistentObjectState(
            fields=PersistentFieldState({"code": "A"}),
            references=PersistentReferenceState(),
            business_state=PersistentBusinessState(),
            system_fields=PersistentSystemFieldState(),
        ),
    )

    assert obj.state.fields["code"] == "A"

    with pytest.raises((AttributeError, TypeError)):
        obj.state = PersistentObjectState(  # type: ignore[misc]
            fields=PersistentFieldState(),
            references=PersistentReferenceState(),
            business_state=PersistentBusinessState(),
            system_fields=PersistentSystemFieldState(),
        )


def test_object_persistence_contract_shape() -> None:
    assert list(signature(ObjectPersistence.create).parameters) == ["self", "obj"]
    assert list(signature(ObjectPersistence.get).parameters) == ["self", "identity"]
    assert list(signature(ObjectPersistence.update).parameters) == ["self", "obj"]


def test_object_deletion_contract_shape() -> None:
    assert list(signature(ObjectDeletion.delete).parameters) == ["self", "identity"]


def make_state() -> PersistentObjectState:
    return PersistentObjectState(
        fields=PersistentFieldState({"name": "Acme"}),
        references=PersistentReferenceState({"parent": Identifier.new()}),
        business_state=PersistentBusinessState({Identifier.new(): Identifier.new()}),
        system_fields=PersistentSystemFieldState({"deleted": False}),
    )


def test_persistent_object_state_contains_all_durable_categories() -> None:
    fields = PersistentFieldState({"name": "Acme"})
    references = PersistentReferenceState({"parent": Identifier.new()})
    business_state = PersistentBusinessState({Identifier.new(): Identifier.new()})
    system_fields = PersistentSystemFieldState({"deleted": False})

    state = PersistentObjectState(
        fields=fields,
        references=references,
        business_state=business_state,
        system_fields=system_fields,
    )

    assert state.fields is fields
    assert state.references is references
    assert state.business_state is business_state
    assert state.system_fields is system_fields


def test_persistent_object_state_preserves_empty_containers() -> None:
    fields = PersistentFieldState.empty()
    references = PersistentReferenceState.empty()
    business_state = PersistentBusinessState.empty()
    system_fields = PersistentSystemFieldState.empty()

    state = PersistentObjectState(
        fields=fields,
        references=references,
        business_state=business_state,
        system_fields=system_fields,
    )

    assert state.fields is fields
    assert state.references is references
    assert state.business_state is business_state
    assert state.system_fields is system_fields


def test_persistent_object_state_equality_is_value_based() -> None:
    field_state = PersistentFieldState({"name": "Acme"})
    reference_state = PersistentReferenceState.empty()
    definition_identity = Identifier.new()
    state_identity = Identifier.new()
    business_state = PersistentBusinessState({definition_identity: state_identity})
    system_fields = PersistentSystemFieldState({"deleted": False})

    first = PersistentObjectState(
        fields=field_state,
        references=reference_state,
        business_state=business_state,
        system_fields=system_fields,
    )
    second = PersistentObjectState(
        fields=PersistentFieldState({"name": "Acme"}),
        references=PersistentReferenceState.empty(),
        business_state=PersistentBusinessState({definition_identity: state_identity}),
        system_fields=PersistentSystemFieldState({"deleted": False}),
    )

    assert first == second


def test_persistent_object_preserves_identity_type_and_state() -> None:
    identity = Identifier.new()
    object_type_identity = Identifier.new()
    state = make_state()

    obj = PersistentObject(
        identity=identity,
        object_type_identity=object_type_identity,
        state=state,
    )

    assert obj.identity is identity
    assert obj.object_type_identity is object_type_identity
    assert obj.state is state


def test_persistent_object_is_immutable() -> None:
    obj = PersistentObject(
        identity=Identifier.new(),
        object_type_identity=Identifier.new(),
        state=make_state(),
    )

    try:
        obj.state = make_state()  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("PersistentObject must be immutable.")


def test_persistent_object_repr_is_available() -> None:
    obj = PersistentObject(
        identity=Identifier.new(),
        object_type_identity=Identifier.new(),
        state=make_state(),
    )

    assert "PersistentObject" in repr(obj)


def test_persistent_object_state_preserves_all_durable_containers() -> None:
    fields = PersistentFieldState({"code": "A"})
    references = PersistentReferenceState({"parent": Identifier.new()})
    business_state = PersistentBusinessState({Identifier.new(): Identifier.new()})
    system_fields = PersistentSystemFieldState({"version": 1})

    state = PersistentObjectState(
        fields=fields,
        references=references,
        business_state=business_state,
        system_fields=system_fields,
    )

    assert state.fields is fields
    assert state.references is references
    assert state.business_state is business_state
    assert state.system_fields is system_fields


def test_persistent_object_state_is_immutable() -> None:
    state = PersistentObjectState(
        fields=PersistentFieldState({"code": "A"}),
        references=PersistentReferenceState(),
        business_state=PersistentBusinessState(),
        system_fields=PersistentSystemFieldState(),
    )

    with pytest.raises((AttributeError, TypeError)):
        state.fields = PersistentFieldState()  # type: ignore[misc]


def test_persistent_object_state_accepts_empty_containers() -> None:
    state = PersistentObjectState(
        fields=PersistentFieldState({}),
        references=PersistentReferenceState({}),
        business_state=PersistentBusinessState({}),
        system_fields=PersistentSystemFieldState({}),
    )

    assert len(state.fields) == 0
    assert len(state.references) == 0
    assert len(state.business_state) == 0
    assert len(state.system_fields) == 0
