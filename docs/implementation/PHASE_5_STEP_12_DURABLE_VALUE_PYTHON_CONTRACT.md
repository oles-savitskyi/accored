# Python API Contract — `platform/value/durable.py`

## 1. Module purpose

`durable.py` defines the platform-level semantic contract for immutable durable values.

The module MUST NOT depend on:

* Runtime;
* Object;
* Persistence;
* Storage;
* Metadata;
* Configuration;
* transactions;
* serialization.

The module defines only:

* the `DurableValue` type contract;
* immutable composite durable values;
* validation of the durable-value domain.

---

# 2. Public types

The module exposes:

```python
DurableScalar
DurableValue
StructuredValue
CollectionValue
is_durable_value
validate_durable_value
```

No additional public value hierarchy is required by Step 12.

---

# 3. `DurableScalar`

`DurableScalar` is the closed union of supported scalar Python representations:

```python
type DurableScalar = (
    bool
    | int
    | Decimal
    | str
    | date
    | datetime
)
```

The following semantic mapping is normative:

```text
Boolean  → bool
Integer  → int
Decimal  → decimal.Decimal
String   → str
Date     → datetime.date
DateTime → datetime.datetime
```

Scalar values MUST use the exact supported Python types.

Subclasses of the supported scalar types MUST NOT automatically qualify as `DurableScalar`.

This prevents arbitrary Python subclasses from entering the durable-value domain.

The implementation MUST distinguish:

```text
bool      from int
datetime  from date
```

according to their exact concrete Python types.

Therefore:

```text
True
```

is Boolean and not Integer, while:

```text
1
```

is Integer.

Likewise:

```text
datetime(...)
```

is DateTime and not Date.

---

# 4. `DurableValue`

`DurableValue` is the closed union:

```python
type DurableValue = (
    bool
    | int
    | Decimal
    | str
    | date
    | datetime
    | StructuredValue
    | CollectionValue
)
```

`DurableValue` MUST NOT be represented by a universal wrapper containing:

```text
kind + object
```

and MUST NOT accept arbitrary Python objects.

The durable-value domain is closed at the Step 12 level.

A new durable-value kind requires an explicit architectural change.

---

# 5. Unsupported values

The following Python values MUST NOT qualify as `DurableValue` merely by being Python objects:

```text
float
None
dict
list
set
tuple
object
Enum instances
ObjectIdentity
ObjectInstance
ObjectContext
RuntimeObjectType
Metadata
Persistence objects
Storage objects
custom mutable objects
arbitrary custom classes
```

A `dict` may be converted into a `StructuredValue`.

A `list` or `tuple` may be converted into a `CollectionValue`.

Such conversion is explicit and creates an immutable semantic snapshot.

---

# 6. `StructuredValue`

`StructuredValue` represents an immutable semantic mapping:

```python
FieldIdentity → DurableValue
```

In the current Metadata model:

```python
FieldIdentity = str
```

where the string is the canonical Metadata field name.

`StructuredValue` therefore has the semantic shape:

```text
StructuredValue
    └── immutable mapping[str, DurableValue]
```

## 6.1 Construction

The primary construction API is:

```python
StructuredValue(
    values: Mapping[str, DurableValue] | Iterable[tuple[str, DurableValue]],
)
```

The constructor MUST create an immutable snapshot of the supplied values.

The caller MUST NOT retain any mutable structure through which the internal state of the resulting `StructuredValue` can be modified.

An empty structure is valid:

```python
StructuredValue({})
```

---

## 6.2 Key rules

Each key MUST:

* be a `str`;
* represent a canonical field identity;
* be unique.

Duplicate keys MUST result in an error.

Empty field names and invalid field-name syntax are not validated by `StructuredValue` unless such syntax is already part of the generic field-identity contract.

Metadata-level field-name validation remains outside this value object.

---

## 6.3 Value rules

Every value MUST satisfy:

```python
is_durable_value(value) is True
```

Nested `StructuredValue` and `CollectionValue` instances are therefore valid.

Arbitrary Python objects MUST be rejected.

For example:

```text
StructuredValue(
    {
        "name": "Alice",
        "age": 42,
    }
)
```

is valid.

But:

```text
StructuredValue(
    {
        "runtime": ObjectInstance(...),
    }
)
```

is invalid.

---

# 7. `StructuredValue` access API

The public API SHOULD expose mapping-like read-only access:

```python
__getitem__(key: str) -> DurableValue

get(
    key: str,
    default: DurableValue | None = None,
) -> DurableValue | None

__contains__(key: object) -> bool

__iter__() -> Iterator[str]

__len__() -> int

keys() -> ...
values() -> ...
items() -> ...
```

No mutating mapping methods are exposed.

The following operations MUST NOT exist:

```text
__setitem__
__delitem__
clear
pop
popitem
setdefault
update
```

or equivalent mutation APIs.

The object is read-only after construction.

---

# 8. `StructuredValue` equality

`StructuredValue` equality is semantic.

Mapping insertion order MUST NOT affect equality.

Therefore:

```text
{
    "a": 1,
    "b": 2
}
```

and:

```text
{
    "b": 2,
    "a": 1
}
```

represent equal `StructuredValue` instances.

The implementation MAY use a canonical immutable internal representation to guarantee this property.

The internal representation is not part of the public API.

---

# 9. `StructuredValue` hash

`StructuredValue` SHOULD be hashable.

Hashing MUST be consistent with semantic equality.

Therefore equal `StructuredValue` instances MUST have equal hashes regardless of construction order.

Nested values MUST therefore also have stable immutable representations.

---

# 10. `CollectionValue`

`CollectionValue` represents an immutable ordered sequence:

```python
sequence[DurableValue]
```

Its semantic shape is:

```text
CollectionValue
    └── immutable ordered sequence[DurableValue]
```

Order is part of the semantic value.

Therefore:

```text
[A, B, C]
```

is not equal to:

```text
[C, B, A]
```

---

# 11. `CollectionValue` construction

The primary construction API is:

```python
CollectionValue(
    values: Iterable[DurableValue],
)
```

The constructor MUST create an immutable snapshot.

An empty collection is valid:

```python
CollectionValue(())
```

Every element MUST satisfy:

```python
is_durable_value(value) is True
```

Arbitrary Python objects MUST be rejected.

---

# 12. `CollectionValue` access API

The public API SHOULD expose read-only sequence semantics:

```python
__getitem__(index: int | slice) -> DurableValue | CollectionValue

__iter__() -> Iterator[DurableValue]

__len__() -> int

__contains__(value: object) -> bool
```

No mutating sequence methods are exposed.

The following operations MUST NOT exist:

```text
append
extend
insert
remove
pop
clear
reverse
sort
```

or equivalent mutation APIs.

---

# 13. `CollectionValue` equality

`CollectionValue` equality is semantic and order-sensitive.

For example:

```text
CollectionValue([1, 2, 3])
==
CollectionValue([1, 2, 3])
```

but:

```text
CollectionValue([1, 2, 3])
!=
CollectionValue([3, 2, 1])
```

---

# 14. `CollectionValue` hash

`CollectionValue` SHOULD be hashable.

Hashing MUST preserve sequence ordering and MUST be consistent with semantic equality.

---

# 15. Recursive immutability

Immutability is recursive.

It is not sufficient for `StructuredValue` or `CollectionValue` itself to reject mutation.

All nested values MUST also satisfy the durable-value contract.

Therefore the following is valid:

```text
StructuredValue
    └── CollectionValue
          ├── Integer
          ├── String
          └── StructuredValue
                └── Boolean
```

provided every level is immutable.

No mutable Python object may remain reachable as part of the semantic value representation.

---

# 16. Snapshot semantics

Construction from mutable Python containers MUST establish snapshot semantics.

For example, conceptually:

```python
source = {"a": 1}

value = StructuredValue(source)

source["a"] = 2
```

After construction:

```text
value["a"] == 1
```

must remain true.

Likewise:

```python
source = [1, 2]

value = CollectionValue(source)

source.append(3)
```

must not alter `value`.

The durable value owns its semantic state after construction.

---

# 17. `is_durable_value`

The module provides:

```python
def is_durable_value(value: object) -> TypeGuard[DurableValue]:
    ...
```

The function MUST return `True` only when the supplied object satisfies the complete Step 12 durable-value contract.

It MUST recursively validate:

* scalar type;
* `StructuredValue` contents;
* `CollectionValue` contents.

It MUST reject:

* unsupported scalar types;
* mutable containers;
* arbitrary Python objects;
* `None`;
* `float`;
* runtime objects;
* persistence objects.

The function MUST NOT perform Metadata validation.

For example, it MUST NOT determine whether:

```text
"age" → 42
```

is valid for a particular Metadata field.

It only determines whether `42` is a valid durable value.

---

# 18. `validate_durable_value`

The module provides:

```python
def validate_durable_value(value: object) -> None:
    ...
```

The function MUST raise a dedicated value-contract exception when the supplied object is not a valid `DurableValue`.

A successful call returns `None`.

The exception type SHOULD be:

```python
DurableValueError
```

and this exception SHOULD be part of the public module API.

Therefore the complete public API becomes:

```python
DurableScalar
DurableValue

StructuredValue
CollectionValue

DurableValueError

is_durable_value
validate_durable_value
```

---

# 19. `DurableValueError`

`DurableValueError` represents violation of the platform durable-value contract.

It MUST be independent of:

* Runtime errors;
* Persistence errors;
* Storage errors;
* Metadata errors.

Recommended inheritance:

```python
class DurableValueError(ValueError):
    ...
```

The exception indicates invalid value representation, not invalid business meaning.

For example:

```text
float
```

may raise `DurableValueError`.

But:

```text
Decimal("10.50")
```

being disallowed for a particular Metadata field is not a `DurableValueError`; that is a Metadata/Validation concern.

---

# 20. Type semantics

The module MUST preserve scalar semantic kinds.

The following distinction is normative:

```text
bool       ≠ int
date       ≠ datetime
```

even though Python's inheritance relationships may make ordinary `isinstance` checks ambiguous.

The implementation MUST use exact scalar type semantics when validating the closed scalar domain.

The contract does not require a stored runtime `ValueKind` field.

If later layers require value-kind inspection, such inspection MUST derive the kind from the validated value rather than introducing redundant state into every durable value.

---

# 21. Decimal semantics

`Decimal` is the only base decimal numeric representation.

`float` is prohibited.

The module MUST NOT silently convert:

```python
float → Decimal
```

because such conversion would hide an invalid source representation.

Likewise, the module MUST NOT silently convert arbitrary numeric types into `int` or `Decimal`.

Conversion, if required, belongs to an explicit boundary such as object creation, import, mapping, or validation.

The `Decimal` value itself remains an immutable semantic value.

---

# 22. Date and DateTime semantics

The Python representations are:

```text
date     → Date
datetime → DateTime
```

`datetime` MUST be recognized as DateTime rather than Date.

Step 12 does not impose additional timezone policy.

Timezone requirements, normalization, calendar rules, or domain-specific temporal constraints belong to the appropriate higher-level semantic or Metadata layer.

---

# 23. Serialization independence

`StructuredValue` and `CollectionValue` MUST NOT expose serialization-specific APIs.

The module MUST NOT define:

```text
to_json
from_json
to_bytes
from_bytes
database serialization
pickle format
storage format
```

A later serialization layer may define a representation of `DurableValue`, but that representation is outside this contract.

---

# 24. Metadata independence

`durable.py` MUST NOT import Metadata classes.

`StructuredValue` may use the current canonical field identity representation:

```python
str
```

but it MUST NOT contain:

```text
AttributeMetadata
Metadata
AttributeDefinition
ValidationDefinition
SystemFieldMetadata
```

or any other definition object.

The distinction is:

```text
DurableValue
    = actual semantic value

Metadata
    = definition of what that value means
```

---

# 25. Runtime independence

`durable.py` MUST NOT import Runtime classes.

In particular, it MUST NOT depend on:

```text
ObjectInstance
ObjectContext
ObjectState
RuntimeObjectType
RuntimeDurableState
RuntimeConfigurationContext
```

A durable value may be stored by `RuntimeDurableState`, but it has no knowledge of that runtime model.

---

# 26. Persistence independence

`durable.py` MUST NOT import:

```text
PersistentObject
PersistentObjectState
PersistentField
PersistenceProvider
StorageProvider
StorageKey
```

The same durable semantic value can therefore be represented by both:

```text
RuntimeDurableState
```

and:

```text
PersistentObjectState
```

without either representation owning the value contract.

---

# 27. Reference separation

`ObjectIdentity` is not a `DurableValue`.

References are represented separately:

```text
RuntimeDurableState
│
├── fields
│     FieldIdentity → NULL | DurableValue
│
├── references
│     ReferenceIdentity → ReferenceValue
│
├── business_state
│     ...
│
└── durable_system_fields
      SystemFieldIdentity → NULL | DurableValue
```

A future reference implementation MUST NOT require `DurableValue` to understand runtime object identity.

---

# 28. Business-state separation

Business-state values are not a separate base `DurableValue` kind.

A business-state snapshot uses its own semantic identity:

```text
BusinessStateDefinitionIdentity
    →
StateValueIdentity
```

The current Step 12 design does not require `StateValueIdentity` to be represented as a `DurableValue`.

Business-state semantics therefore remain separate from ordinary field values.

---

# 29. NULL and MISSING separation

The module does not define `MISSING`.

`MISSING` is represented by absence from a state container.

The module does not include `None` in `DurableValue`.

Therefore:

```text
MISSING
    ≠
NULL
    ≠
DurableValue
```

`NULL` is a state-container semantic and is not represented by `DurableValue`.

---

# 30. No implicit coercion

The constructors MUST NOT silently coerce values into the durable-value domain.

Examples:

```text
float → Decimal       prohibited
list → CollectionValue       implicit conversion prohibited
dict → StructuredValue        implicit conversion prohibited
object → String                implicit conversion prohibited
Enum → String/Integer          implicit conversion prohibited
```

Explicit construction is required.

This prevents accidental loss of semantic information.

---

# 31. Public API stability

The following are the intended stable public abstractions for Step 12:

```text
DurableScalar
DurableValue
StructuredValue
CollectionValue
DurableValueError
is_durable_value()
validate_durable_value()
```

Internal canonical representation, helper functions, normalization routines, and implementation details MUST NOT be considered part of the public contract unless explicitly exported later.

---

# 32. Architectural invariant

The complete contract can be summarized as:

```text
DurableValue
│
├── immutable scalar
│     ├── bool
│     ├── int
│     ├── Decimal
│     ├── str
│     ├── date
│     └── datetime
│
└── immutable composite
      ├── StructuredValue
      │     └── str → DurableValue
      │
      └── CollectionValue
            └── ordered DurableValue sequence
```

The fundamental rule is:

> A `DurableValue` represents an immutable semantic value, not an arbitrary Python object.

The contract is intentionally small.

New semantic value kinds, domain-specific value objects, explicit field identities, serialization representations, or Metadata-aware value types require separate architectural decisions and MUST NOT be introduced implicitly during Step 12 implementation.
