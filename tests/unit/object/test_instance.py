from accore.platform.foundation.identity import Identifier
from accore.platform.object import ObjectInstance


def test_object_instance_preserves_identity() -> None:
    identity = Identifier.new()

    instance = ObjectInstance(identity=identity)

    assert instance.identity == identity


def test_object_instances_with_different_identities_are_not_equal() -> None:
    first = ObjectInstance(identity=Identifier.new())
    second = ObjectInstance(identity=Identifier.new())

    assert first != second


def test_object_instances_with_same_identity_are_equal() -> None:
    identity = Identifier.new()

    first = ObjectInstance(identity=identity)
    second = ObjectInstance(identity=identity)

    assert first == second


def test_object_instance_equality_is_based_on_identity() -> None:
    identity = Identifier.new()

    first = ObjectInstance(identity=identity)
    second = ObjectInstance(identity=Identifier.from_str(str(identity)))

    assert first == second


def test_object_instance_is_not_equal_to_other_types() -> None:
    instance = ObjectInstance(identity=Identifier.new())

    assert instance != object()
