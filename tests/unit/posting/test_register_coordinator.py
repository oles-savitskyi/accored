from accore.platform.foundation import Identifier
from accore.platform.posting import RegisterPostingResultCoordinator
from accore.platform.registers import Movement


class Persistence:
    def __init__(self, movements: tuple[Movement, ...] = ()) -> None:
        self.movements = movements
        self.lookups = []

    def append(self, movements):
        self.movements = tuple(movements)

    def find_by_source_document(self, register_identity, source_document_identity):
        self.lookups.append((register_identity, source_document_identity))
        return tuple(
            movement
            for movement in self.movements
            if movement.register_identity == register_identity
            and movement.source_document_identity == source_document_identity
        )

    def remove(self, movement_identities):
        self.movements = tuple(
            movement for movement in self.movements if movement.identity not in movement_identities
        )

    def enumerate(self, register_identity):
        return tuple(m for m in self.movements if m.register_identity == register_identity)


class Mutation:
    def __init__(self):
        self.established = []
        self.removed = []

    def establish(self, movements):
        self.established.append(tuple(movements))

    def remove(self, movements):
        self.removed.append(tuple(movements))


def test_remove_uses_authoritative_source_document_lookup():
    document = type("Document", (), {"identity": Identifier.new()})()
    register = Identifier.new()
    movement = type(
        "Movement",
        (),
        {
            "identity": Identifier.new(),
            "register_identity": register,
            "source_document_identity": document.identity,
        },
    )()
    persistence = Persistence((movement,))
    mutation = Mutation()
    coordinator = RegisterPostingResultCoordinator(mutation, persistence, (register,))

    coordinator.remove(document)

    assert persistence.lookups == [(register, document.identity)]
    assert mutation.removed == [(movement,)]


def test_establish_delegates_complete_movement_set() -> None:
    document = type("Document", (), {"identity": Identifier.new()})()
    mutation = Mutation()
    persistence = Persistence()
    coordinator = RegisterPostingResultCoordinator(mutation, persistence, (Identifier.new(),))
    movement_set = type("MovementSet", (), {"movements": ("movement",)})()

    coordinator.establish(document, movement_set)

    assert mutation.established == [("movement",)]
