# MUSE — Database Models

<p align="center">
  <strong>Persistent domain model layer for MUSE</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/SQLAlchemy-2.x-red?logo=sqlalchemy&logoColor=white" alt="SQLAlchemy">
  <img src="https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql&logoColor=white" alt="PostgreSQL">
</p>

---

## Overview

The `models` package defines the persistent domain entities used throughout the MUSE backend.

These models represent the data that MUSE needs to store across sessions, including:

* User accounts
* Friend groups and memberships
* Personalization and preferences
* Recommendations
* Communication
* Activities and planning
* Memories and media
* Notes and reminders
* Notifications
* Mood entries

The models form the foundation of the backend's persistence layer and are consumed by higher-level application layers such as repositories, services, and API routers.

---

## Architecture

MUSE follows a layered backend architecture:

```text
API / Routers
      │
      ▼
  Services
      │
      ▼
 Repositories
      │
      ▼
   Models
      │
      ▼
 PostgreSQL
```

The model layer should focus on **data representation and database concerns**.

Business logic should remain in the service layer rather than being embedded directly into SQLAlchemy models.

---

## Model Domains

### Identity & Groups

Models responsible for users, groups, membership, and group access.

| Model             | Responsibility                               |
| ----------------- | -------------------------------------------- |
| `User`            | User account and identity data               |
| `FriendGroup`     | Friend group representation                  |
| `GroupMembership` | Relationship between users and groups        |
| `InvitationCode`  | Controlled group joining through invitations |

---

### Personalization

Models responsible for configuring and learning user preferences.

| Model                    | Responsibility                                    |
| ------------------------ | ------------------------------------------------- |
| `BaseConfiguration`      | Initial/default configuration for a group         |
| `UserInterest`           | Explicit interests selected or provided by a user |
| `UserPreference`         | User-level personalization preferences            |
| `FeaturePreference`      | Preferences for individual MUSE features          |
| `NotificationPreference` | User notification preferences                     |
| `BehavioralSignal`       | Implicit signals used to understand user behavior |

MUSE's personalization system is designed around the idea that onboarding provides an initial preference profile while users remain free to modify and expand their preferences later.

---

### Recommendations

Models supporting MUSE's recommendation and personalization engine.

| Model                       | Responsibility                                         |
| --------------------------- | ------------------------------------------------------ |
| `Recommendation`            | Personalized recommendation                            |
| `RecommendationInteraction` | User interaction with a recommendation                 |
| `GroupRecommendation`       | Recommendation surfaced specifically to a friend group |
| `DailyDrop`                 | Personalized daily content or recommendation           |

---

### Communication

Models responsible for real-time and persistent communication-related data.

| Model             | Responsibility                                     |
| ----------------- | -------------------------------------------------- |
| `RoomMessage`     | Messages exchanged inside a group                  |
| `MessageReaction` | Reactions attached to messages                     |
| `Notification`    | Persistent notification history                    |
| `Device`          | User device registration for notification delivery |

Notifications are persisted so users can revisit notification history after clearing or reading individual notifications.

---

### Activities & Planning

Models supporting shared activities and plans.

| Model                   | Responsibility                                 |
| ----------------------- | ---------------------------------------------- |
| `GroupActivity`         | Activity created for a friend group            |
| `GroupActivityResponse` | Individual user's response to a group activity |
| `Plan`                  | Shared plan involving a group                  |
| `PlanParticipant`       | Users participating in a plan                  |
| `Reminder`              | User reminders                                 |

---

### Memories & Notes

Models supporting shared memories, uploaded media, and notes.

| Model          | Responsibility                          |
| -------------- | --------------------------------------- |
| `Memory`       | Saved group memory                      |
| `Media`        | Uploaded media metadata                 |
| `MemoryMedia`  | Relationship between memories and media |
| `PersonalNote` | Private user note                       |
| `SharedNote`   | Note shared with a friend group         |

Media metadata is stored in the database while the actual media files can be handled by external object storage.

---

### Wellbeing

Models supporting lightweight personal wellbeing features.

| Model       | Responsibility  |
| ----------- | --------------- |
| `MoodEntry` | User mood entry |

---

## Complete Model Inventory

The current first-pass model layer contains **29 models**:

```text
Identity & Groups
├── User
├── FriendGroup
├── GroupMembership
└── InvitationCode

Personalization
├── BaseConfiguration
├── UserInterest
├── UserPreference
├── FeaturePreference
├── NotificationPreference
└── BehavioralSignal

Recommendations
├── Recommendation
├── RecommendationInteraction
├── GroupRecommendation
└── DailyDrop

Communication
├── RoomMessage
├── MessageReaction
├── Notification
└── Device

Activities & Planning
├── GroupActivity
├── GroupActivityResponse
├── Plan
├── PlanParticipant
└── Reminder

Memories & Notes
├── Memory
├── Media
├── MemoryMedia
├── PersonalNote
└── SharedNote

Wellbeing
└── MoodEntry
```

---

## Model Conventions

### Primary Keys

Models use UUID-based primary keys where appropriate.

```python
id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4,
)
```

### Timestamps

Persistent timestamps use timezone-aware UTC datetimes.

```python
default=lambda: datetime.now(timezone.utc)
```

For update timestamps:

```python
onupdate=lambda: datetime.now(timezone.utc)
```

Naive UTC timestamp patterns such as `datetime.utcnow()` should not be used.

---

## Relationships

Foreign-key relationships should explicitly define their intended deletion behavior.

For example:

```python
ForeignKey(
    "users.id",
    ondelete="CASCADE",
)
```

Relationship design should preserve data integrity while ensuring that deleting a parent entity does not leave unintended orphaned records.

---

## Constraints & Indexes

Models should use database-level constraints where they represent actual domain rules.

Examples include:

* Unique constraints
* Foreign keys
* Non-null constraints
* Indexed foreign keys
* Unique relationship pairs

For example, a user should not be added to the same plan more than once:

```python
UniqueConstraint(
    "plan_id",
    "user_id",
    name="uq_plan_participant",
)
```

Database constraints should be preferred over relying solely on application-level validation when the rule is fundamentally a data-integrity requirement.

---

## Separation of Responsibilities

The model layer should **not** become the location for application workflows.

### Models should handle

* Database table definitions
* Columns
* Data types
* Foreign keys
* Constraints
* Indexes
* Persistence-related configuration

### Models should not handle

* Authentication workflows
* Recommendation generation
* Notification dispatching
* Business workflows
* API request handling
* External service calls
* Complex application logic

Those responsibilities belong to higher layers of the backend.

---

## Current Status

The model layer currently represents the **first-pass MUSE domain schema**.

The completion of these models does **not** mean the schema is permanently finalized.

The schema will be reviewed as implementation progresses to identify:

* Unnecessary entities
* Missing relationships
* Incorrect relationships
* Redundant fields
* Missing constraints
* Missing indexes
* Domain rules that belong at the database level
* Features that require additional persistence

The goal is not to maximize the number of tables.

The goal is to maintain a **coherent, maintainable, production-oriented domain model** that accurately represents the MUSE application.

---

## Next Step

After the first-pass model layer is complete, the backend moves toward database migration and persistence infrastructure:

```text
29 First-Pass Models
        │
        ▼
   Schema Review
        │
        ▼
   Alembic Migration
        │
        ▼
     PostgreSQL
        │
        ▼
   Repositories
        │
        ▼
     Services
        │
        ▼
       APIs
```

The schema should evolve based on actual MUSE functionality rather than being expanded simply to increase the number of database tables.