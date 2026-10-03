from __future__ import annotations

from dataclasses import dataclass

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.security import (
    AuthorizationDecision,
    AuthorizationDeniedError,
    AuthorizationDenyReason,
    AuthorizationOutcome,
    AuthorizationRequest,
    DefaultAuthorizationService,
    Permission,
    Principal,
    PrincipalType,
    Role,
    SecurityClaim,
    SecurityContext,
    SecurityObjectIdentity,
    SecurityOperation,
    User,
)
from accore.platform.security.errors import SecurityConfigurationError, SecurityInfrastructureError
from standard.security import (
    InMemoryRoleRepository,
    InMemoryUserRepository,
    StandardSecurityAuthorizationState,
    StandardSecurityComposition,
)

TARGET = SecurityObjectIdentity("Processing", "inventory.rebuild")
OTHER_TARGET = SecurityObjectIdentity("Processing", "inventory.post")


@dataclass(frozen=True, slots=True)
class _Constraint:
    code: str
    result: bool

    def evaluate(self, request: AuthorizationRequest) -> bool:
        return self.result


@dataclass(frozen=True, slots=True)
class _ExplodingConstraint:
    code: str = "explode"

    def evaluate(self, request: AuthorizationRequest) -> bool:
        raise SecurityInfrastructureError("constraint unavailable")


class _ExplodingState:
    def user_for_principal(self, principal: Principal) -> User:
        raise SecurityInfrastructureError("user state unavailable")

    def role(self, identity: Identifier) -> Role:
        raise AssertionError("role must not be queried")


class _RoleState:
    def __init__(self, user: User, roles: dict[Identifier, Role]) -> None:
        self.user = user
        self.roles = roles

    def user_for_principal(self, principal: Principal) -> User:
        return self.user

    def role(self, identity: Identifier) -> Role:
        return self.roles[identity]


def _user(*role_ids: Identifier, active: bool = True) -> User:
    return User(
        identity=Identifier.new(),
        login="alice",
        display_name="Alice",
        email=None,
        active=active,
        role_ids=role_ids,
    )


def _principal(user: User, principal_type: PrincipalType = PrincipalType.USER) -> Principal:
    return Principal(identity=user.identity, identity_type=principal_type)


def _request(
    user: User | None,
    *,
    target: SecurityObjectIdentity = TARGET,
    operation: SecurityOperation = SecurityOperation.EXECUTE,
    principal_type: PrincipalType = PrincipalType.USER,
    claims: tuple[SecurityClaim, ...] = (),
    resource: object | None = None,
) -> AuthorizationRequest:
    principal = None if user is None else Principal(user.identity, principal_type, claims)
    return AuthorizationRequest(
        context=SecurityContext(principal=principal, session=None),
        target=target,
        operation=operation,
        resource=resource,  # type: ignore[arg-type]
    )


def _service(user: User, *roles: Role) -> DefaultAuthorizationService:
    return DefaultAuthorizationService(_RoleState(user, {role.identity: role for role in roles}))


def _role(user_role: Identifier, *permissions: Permission) -> Role:
    return Role(user_role, "operator", "Operator", permissions)


def _permission(
    target: SecurityObjectIdentity = TARGET,
    operation: SecurityOperation = SecurityOperation.EXECUTE,
    constraints: tuple = (),
) -> Permission:
    return Permission(Identifier.new(), target, operation, constraints)


def test_unauthenticated_is_denied_without_state_lookup() -> None:
    service = DefaultAuthorizationService(_ExplodingState())

    decision = service.authorize(_request(None))

    assert decision == AuthorizationDecision(
        AuthorizationOutcome.DENY,
        AuthorizationDenyReason.UNAUTHENTICATED,
    )


def test_inactive_principal_is_denied() -> None:
    user = _user(active=False)
    service = _service(user)

    decision = service.authorize(_request(user))

    assert decision.reason is AuthorizationDenyReason.INACTIVE_PRINCIPAL


def test_exact_permission_allows() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    service = _service(user, _role(role_id, _permission()))

    decision = service.authorize(_request(user))

    assert decision.outcome is AuthorizationOutcome.ALLOW
    assert decision.reason is None


def test_different_target_or_operation_is_missing_permission() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    service = _service(user, _role(role_id, _permission()))

    assert (
        service.authorize(_request(user, target=OTHER_TARGET)).reason
        is AuthorizationDenyReason.MISSING_PERMISSION
    )
    assert (
        service.authorize(_request(user, operation=SecurityOperation.READ)).reason
        is AuthorizationDenyReason.MISSING_PERMISSION
    )


def test_multiple_roles_form_additive_union() -> None:
    role_a = Identifier.new()
    role_b = Identifier.new()
    user = _user(role_a, role_b)
    service = _service(
        user,
        _role(role_a, _permission(target=OTHER_TARGET, operation=SecurityOperation.READ)),
        _role(role_b, _permission()),
    )

    assert service.authorize(_request(user)).outcome is AuthorizationOutcome.ALLOW


def test_duplicate_permissions_are_harmless() -> None:
    role_a = Identifier.new()
    role_b = Identifier.new()
    permission = _permission()
    user = _user(role_a, role_b)
    service = _service(user, _role(role_a, permission), _role(role_b, permission))

    assert service.authorize(_request(user)).outcome is AuthorizationOutcome.ALLOW


def test_repeated_evaluation_observes_current_authoritative_state() -> None:
    role_id = Identifier.new()
    permission = _permission()
    user = _user(role_id)
    state = _RoleState(user, {role_id: _role(role_id)})
    service = DefaultAuthorizationService(state)

    assert service.authorize(_request(user)).reason is AuthorizationDenyReason.MISSING_PERMISSION
    state.roles[role_id] = _role(role_id, permission)
    assert service.authorize(_request(user)).outcome is AuthorizationOutcome.ALLOW


def test_missing_role_fails_closed() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    state = StandardSecurityAuthorizationState(
        users=InMemoryUserRepository((user,)),
        roles=InMemoryRoleRepository(()),
    )
    service = DefaultAuthorizationService(state)

    with pytest.raises(SecurityConfigurationError, match="Unknown role identity"):
        service.authorize(_request(user))


def test_valid_granting_role_plus_missing_role_still_fails_before_allow() -> None:
    valid_role = Identifier.new()
    missing_role = Identifier.new()
    user = _user(valid_role, missing_role)
    state = StandardSecurityAuthorizationState(
        users=InMemoryUserRepository((user,)),
        roles=InMemoryRoleRepository((_role(valid_role, _permission()),)),
    )
    service = DefaultAuthorizationService(state)

    with pytest.raises(SecurityConfigurationError, match="Unknown role identity"):
        service.authorize(_request(user))


def test_no_constraints_grant() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    service = _service(user, _role(role_id, _permission(constraints=())))

    assert service.authorize(_request(user)).outcome is AuthorizationOutcome.ALLOW


def test_all_constraints_true_grant() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    permission = _permission(constraints=(_Constraint("a", True), _Constraint("b", True)))

    service_result = _service(user, _role(role_id, permission)).authorize(_request(user))
    assert service_result.outcome is AuthorizationOutcome.ALLOW


def test_one_false_constraint_denies() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    permission = _permission(constraints=(_Constraint("a", True), _Constraint("b", False)))

    decision = _service(user, _role(role_id, permission)).authorize(_request(user))

    assert decision.reason is AuthorizationDenyReason.CONSTRAINT_FAILED


def test_failed_matching_permission_and_granting_matching_permission_allows() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    role = _role(
        role_id,
        _permission(constraints=(_Constraint("deny", False),)),
        _permission(constraints=(_Constraint("allow", True),)),
    )

    assert _service(user, role).authorize(_request(user)).outcome is AuthorizationOutcome.ALLOW


def test_false_constraint_is_not_infrastructure_failure() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    role = _role(role_id, _permission(constraints=(_Constraint("deny", False),)))

    decision = _service(user, role).authorize(_request(user))

    assert decision.outcome is AuthorizationOutcome.DENY
    assert decision.reason is AuthorizationDenyReason.CONSTRAINT_FAILED


def test_resource_does_not_affect_base_permission_matching() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    role = _role(role_id, _permission())

    resource_a = object()
    resource_b = object()
    service = _service(user, role)

    assert (
        service.authorize(_request(user, resource=resource_a)).outcome is AuthorizationOutcome.ALLOW
    )
    assert (
        service.authorize(_request(user, resource=resource_b)).outcome is AuthorizationOutcome.ALLOW
    )


def test_claims_are_inert_without_explicit_constraint() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    role = _role(role_id, _permission())

    request = _request(
        user,
        claims=(SecurityClaim("department", "other"),),
    )

    assert _service(user, role).authorize(request).outcome is AuthorizationOutcome.ALLOW


def test_claims_can_be_used_by_explicit_constraint() -> None:
    @dataclass(frozen=True, slots=True)
    class ClaimConstraint:
        code: str = "department"

        def evaluate(self, request: AuthorizationRequest) -> bool:
            principal = request.context.principal
            assert principal is not None
            return any(
                claim.name == "department" and claim.value == "inventory"
                for claim in principal.claims
            )

    role_id = Identifier.new()
    user = _user(role_id)
    role = _role(role_id, _permission(constraints=(ClaimConstraint(),)))

    request = _request(user, claims=(SecurityClaim("department", "inventory"),))

    assert _service(user, role).authorize(request).outcome is AuthorizationOutcome.ALLOW


def test_unsupported_principal_type_fails_closed() -> None:
    user = _user()
    service = _service(user)

    with pytest.raises(SecurityConfigurationError, match="Unsupported principal type"):
        service.authorize(_request(user, principal_type=PrincipalType.SERVICE))


def test_user_state_infrastructure_failure_propagates() -> None:
    with pytest.raises(SecurityInfrastructureError, match="unavailable"):
        DefaultAuthorizationService(_ExplodingState()).authorize(_request(_user()))


def test_constraint_infrastructure_failure_propagates() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    role = _role(role_id, _permission(constraints=(_ExplodingConstraint(),)))

    with pytest.raises(SecurityInfrastructureError, match="constraint unavailable"):
        _service(user, role).authorize(_request(user))


def test_require_returns_none_when_allowed() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    service = _service(user, _role(role_id, _permission()))

    assert service.require(_request(user)) is None


def test_require_raises_and_retains_decision_when_denied() -> None:
    user = _user()
    service = _service(user)

    with pytest.raises(AuthorizationDeniedError) as exc_info:
        service.require(_request(user))

    assert exc_info.value.decision.outcome is AuthorizationOutcome.DENY
    assert exc_info.value.decision.reason is AuthorizationDenyReason.MISSING_PERMISSION


def test_decision_invariants_are_enforced() -> None:
    with pytest.raises(ValueError):
        AuthorizationDecision(
            AuthorizationOutcome.ALLOW,
            AuthorizationDenyReason.MISSING_PERMISSION,
        )
    with pytest.raises(ValueError):
        AuthorizationDecision(AuthorizationOutcome.DENY, None)


def test_standard_role_repository_rejects_duplicate_identity() -> None:
    role_id = Identifier.new()
    role = _role(role_id)

    with pytest.raises(SecurityConfigurationError, match="Duplicate role identity"):
        InMemoryRoleRepository((role, role))


def test_standard_authorization_state_adapts_user_and_roles() -> None:
    role_id = Identifier.new()
    user = _user(role_id)
    role = _role(role_id, _permission())
    users = InMemoryUserRepository((user,))
    roles = InMemoryRoleRepository((role,))
    state = StandardSecurityAuthorizationState(users=users, roles=roles)
    composition = StandardSecurityComposition(DefaultAuthorizationService(state))

    assert composition.authorization.authorize(_request(user)).outcome is AuthorizationOutcome.ALLOW
