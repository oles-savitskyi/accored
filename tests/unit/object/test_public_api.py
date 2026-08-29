from __future__ import annotations

import accore.platform.object as object_api
from accore.platform.object import (
    ObjectContext,
    ObjectCreationError,
    ObjectCreator,
    ObjectInstance,
    ObjectLifecycle,
    ObjectLifecycleError,
    ObjectState,
)


def test_object_public_api_exports_expected_symbols() -> None:
    expected = {
        "ObjectContext",
        "ObjectCreationError",
        "ObjectCreator",
        "ObjectInstance",
        "ObjectLifecycle",
        "ObjectLifecycleError",
        "ObjectState",
    }

    assert set(object_api.__all__) == expected


def test_object_public_api_exports_expected_objects() -> None:
    assert object_api.ObjectContext is ObjectContext
    assert object_api.ObjectCreationError is ObjectCreationError
    assert object_api.ObjectCreator is ObjectCreator
    assert object_api.ObjectInstance is ObjectInstance
    assert object_api.ObjectLifecycle is ObjectLifecycle
    assert object_api.ObjectLifecycleError is ObjectLifecycleError
    assert object_api.ObjectState is ObjectState
