from __future__ import annotations

from enum import StrEnum


class SecurityOperation(StrEnum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    POST = "post"
    UNPOST = "unpost"
    APPROVE = "approve"
    CLOSE = "close"
    CONFIGURE = "configure"
    ADMINISTER = "administer"
    MANAGE_USERS = "manage_users"
    IMPORT = "import"
    EXPORT = "export"
    INVOKE = "invoke"
