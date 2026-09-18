# MUSE Model Conventions

## Purpose

This document defines the conventions used by the MUSE SQLAlchemy model layer.

The goal is to keep database models consistent, predictable, and easy to maintain as the application grows.

---

## Primary Keys

MUSE models use UUIDs as primary keys.

```python
id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4,
)
```

UUIDs provide globally unique identifiers without relying on sequential database IDs.

---

## Timestamps

All persisted timestamps should be timezone-aware and stored in UTC.

Use:

```python
from datetime import datetime, timezone

default=lambda: datetime.now(timezone.utc)
```

For automatically updated timestamps:

```python
onupdate=lambda: datetime.now(timezone.utc)
```

Avoid deprecated or timezone-naive patterns such as:

```python
datetime.utcnow()
```

---

## Foreign Keys

Relationships between persistent entities should use explicit foreign keys.

Example:

```python
ForeignKey(
    "users.id",
    ondelete="CASCADE",
)
```

Deletion behavior should be chosen according to the domain relationship rather than applied automatically to every relationship.

---

## Indexes

Columns frequently used for lookups, especially foreign-key columns, should be indexed where appropriate.

Example:

```python
user_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("users.id"),
    nullable=False,
    index=True,
)
```

Indexes should be added based on expected query patterns rather than indiscriminately indexing every column.

---

## Unique Constraints

Database-level uniqueness should be used when duplicate records would violate a domain rule.

For example:

```python
UniqueConstraint(
    "plan_id",
    "user_id",
    name="uq_plan_participant",
)
```

This ensures that the same user cannot be added to the same plan more than once.

---

## Nullable Fields

A column should be nullable only when the absence of a value is meaningful to the domain.

Required information should remain non-nullable so that database-level constraints help maintain data integrity.

---

## Model Responsibilities

Models are responsible for:

* Table definitions
* Columns
* Data types
* Foreign keys
* Constraints
* Indexes
* Persistence-related configuration

Models should not contain:

* API request handling
* Authentication workflows
* External service calls
* Recommendation generation
* Notification dispatching
* Complex business workflows

Business logic belongs in the appropriate service layer.

---

## Layered Architecture

The model layer is part of MUSE's layered backend architecture:

```text
API / Routers
      ↓
Services
      ↓
Repositories
      ↓
Models
      ↓
PostgreSQL
```

Each layer should have a clear responsibility and avoid unnecessarily leaking concerns into other layers.

---

## Schema Evolution

The current MUSE models represent a first-pass domain schema.

The schema may evolve as implementation progresses.

Changes should be based on actual product requirements, data integrity, query patterns, and observed application behavior.

The number of database tables is not itself a design goal.

---

## Migration Responsibility

Database schema changes will be managed through **Alembic migrations**.

Model changes should not be treated as automatically equivalent to database changes.

Before applying a migration, generated migration operations should be reviewed to ensure they accurately represent the intended schema change.