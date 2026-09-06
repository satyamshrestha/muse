# Database Schema

**Project:** MUSE
**Document:** Database Schema
**Status:** Initial Specification
**Version:** 0.1
**Related Documents:** `PRODUCT_SPEC.md`, `UX_ARCHITECTURE.md`, `PERSONALIZATION.md`, `TECHNICAL_ARCHITECTURE.md`

---

# 1. Purpose

This document defines the initial PostgreSQL data model for MUSE.

The schema is designed around three principles:

1. **Users own their personal configuration and data.**
2. **Friend groups own shared experiences and content.**
3. **Personalization changes the experience without restricting feature access.**

The schema should support the initial private deployment while remaining generic enough for arbitrary friend groups.

This document defines the conceptual database model. Exact column types, indexes, constraints, and migration details will be finalized during implementation.

---

# 2. Entity Overview

The initial domain model contains the following major entities:

```text
User
 ├── UserPreference
 ├── UserInterest
 ├── FeaturePreference
 ├── NotificationPreference
 ├── BehavioralSignal
 ├── MoodEntry
 ├── RecommendationInteraction
 ├── Note
 ├── Reminder
 └── Personal Plan

FriendGroup
 ├── GroupMembership
 ├── RoomMessage
 ├── GroupActivity
 ├── Memory
 ├── SharedMedia
 ├── SharedPlan
 └── GroupRecommendation

InvitationCode
 └── BaseConfiguration

Content
 └── Recommendation / DailyDrop
```

---

# 3. User

The `User` entity represents an authenticated application account.

Core responsibilities:

* Authentication
* Account ownership
* Personal preferences
* Personal content
* Group membership
* Personalization signals

Conceptual fields:

```text
User
├── id
├── email
├── password_hash
├── display_name
├── avatar
├── created_at
├── updated_at
└── last_active_at
```

Requirements:

* Email must be unique.
* Passwords must never be stored in plaintext.
* User IDs should be stable internal identifiers.
* Account timestamps should be stored consistently.

---

# 4. FriendGroup

A `FriendGroup` represents a private social space.

The initial product may have one primary group, but the schema should not assume that a user can belong to only one group.

Conceptual fields:

```text
FriendGroup
├── id
├── name
├── created_by
├── created_at
└── updated_at
```

A group owns shared resources such as:

* Room conversations
* Memories
* Shared plans
* Group activities

---

# 5. GroupMembership

`GroupMembership` connects users to friend groups.

Conceptual fields:

```text
GroupMembership
├── id
├── user_id
├── group_id
├── role
├── joined_at
└── status
```

Possible roles:

```text
OWNER
MEMBER
```

The role system should remain minimal initially.

A user must not gain access to group data without a valid membership.

---

# 6. InvitationCode

`InvitationCode` represents a one-time private claim mechanism.

Conceptual fields:

```text
InvitationCode
├── id
├── code_hash
├── base_configuration_id
├── claimed_by
├── created_at
├── claimed_at
└── expires_at
```

Requirements:

* Codes are single-use.
* A claimed code cannot be reused.
* Codes should not expose unnecessary personal information.
* The raw code should not need to be stored permanently.
* A code may optionally have an expiration time.

The code maps to a predefined configuration rather than permanently identifying the resulting user.

---

# 7. BaseConfiguration

A `BaseConfiguration` represents an initial personalization profile.

It exists primarily for private seeded users.

Conceptual fields:

```text
BaseConfiguration
├── id
├── name
├── configuration_data
├── created_at
└── updated_at
```

The configuration may contain:

* Initial interests
* Initial feature priorities
* Personality preferences
* Notification preferences
* Other onboarding defaults

A base configuration is copied/applied to the user during onboarding.

It should not remain authoritative after the user begins modifying their preferences.

---

# 8. UserInterest

`UserInterest` represents an interest selected or inferred for a user.

Conceptual fields:

```text
UserInterest
├── id
├── user_id
├── interest
├── strength
├── source
├── created_at
└── updated_at
```

Potential sources:

```text
ONBOARDING
USER
BEHAVIOR
SYSTEM
```

Example:

```text
user_id: 123
interest: psychology
strength: 0.85
source: ONBOARDING
```

The exact scoring system can evolve later.

---

# 9. UserPreference

`UserPreference` stores broader user-level experience preferences.

Possible categories:

* Discovery
* Entertainment
* Learning
* Social interaction
* Memories
* Planning
* Organization
* Randomness

Conceptual structure:

```text
UserPreference
├── id
├── user_id
├── key
├── value
└── updated_at
```

The implementation may later normalize frequently queried preferences into dedicated columns/tables.

The initial design should avoid excessive schema complexity.

---

# 10. FeaturePreference

`FeaturePreference` determines how prominently a feature should appear.

Conceptual fields:

```text
FeaturePreference
├── id
├── user_id
├── feature_key
├── priority
├── enabled_for_home
└── updated_at
```

Important:

`enabled_for_home` does **not** mean the feature is disabled globally.

It only controls whether that feature should be surfaced prominently.

All features remain accessible through the application.

---

# 11. NotificationPreference

`NotificationPreference` controls notification behavior.

Conceptual fields:

```text
NotificationPreference
├── id
├── user_id
├── category
├── enabled
├── frequency
└── updated_at
```

Potential categories:

```text
DAILY_DROP
ROOM
MEMORIES
REMINDERS
RECOMMENDATIONS
PLAYFUL
SYSTEM
```

Users should be able to control notification categories independently.

---

# 12. BehavioralSignal

`BehavioralSignal` records meaningful interactions that may influence personalization.

Conceptual fields:

```text
BehavioralSignal
├── id
├── user_id
├── signal_type
├── entity_type
├── entity_id
├── value
└── created_at
```

Examples:

```text
OPENED
LIKED
SKIPPED
SAVED
SHARED
DISMISSED
USED
```

The system should avoid storing every possible UI interaction.

Only useful personalization signals should be persisted.

---

# 13. Recommendation

A `Recommendation` represents a personalized recommendation delivered to a user.

Conceptual fields:

```text
Recommendation
├── id
├── user_id
├── content_type
├── content_reference
├── source
├── score
├── reason
├── created_at
└── expires_at
```

The recommendation may reference external content rather than storing the complete external resource.

---

# 14. RecommendationInteraction

`RecommendationInteraction` stores explicit feedback on recommendations.

Conceptual fields:

```text
RecommendationInteraction
├── id
├── recommendation_id
├── user_id
├── action
└── created_at
```

Possible actions:

```text
LIKE
SAVE
SKIP
NOT_INTERESTED
MORE_LIKE_THIS
SHARE
```

Explicit feedback should have stronger influence than passive behavior.

---

# 15. DailyDrop

A `DailyDrop` represents the user's daily personalized experience.

Conceptual fields:

```text
DailyDrop
├── id
├── user_id
├── content_type
├── content_reference
├── personalization_context
├── delivered_at
├── opened_at
└── created_at
```

A Daily Drop should be associated with the user it was generated for.

The system should prevent accidental repeated delivery of the same item.

---

# 16. MoodEntry

A `MoodEntry` represents a user's selected current mood.

Conceptual fields:

```text
MoodEntry
├── id
├── user_id
├── mood
├── energy
└── created_at
```

Mood is temporary context.

It should not automatically overwrite the user's long-term personality or interest configuration.

---

# 17. RoomMessage

`RoomMessage` represents a message inside a friend group's shared Room.

Conceptual fields:

```text
RoomMessage
├── id
├── group_id
├── sender_id
├── content
├── reply_to_id
├── created_at
├── edited_at
└── deleted_at
```

Messages belong to a group.

Authorization must verify group membership before reading or modifying them.

---

# 18. MessageReaction

Reactions can be represented separately.

```text
MessageReaction
├── id
├── message_id
├── user_id
├── reaction
└── created_at
```

A user should normally have at most one instance of the same reaction per message.

The exact reaction set can remain small initially.

---

# 19. GroupActivity

`GroupActivity` represents an interactive activity inside the Room.

Potential types:

```text
POLL
QUESTION
QUIZ
CHALLENGE
GAME
RECOMMENDATION
```

Conceptual fields:

```text
GroupActivity
├── id
├── group_id
├── created_by
├── activity_type
├── payload
├── expires_at
└── created_at
```

Activity-specific data may initially be stored as structured JSON where appropriate.

---

# 20. GroupActivityResponse

Responses to activities are stored separately.

```text
GroupActivityResponse
├── id
├── activity_id
├── user_id
├── response
└── created_at
```

This allows polls, questions, quizzes, and other activities to share a common interaction model.

---

# 21. Memory

A `Memory` represents a shared moment.

Conceptual fields:

```text
Memory
├── id
├── group_id
├── created_by
├── title
├── description
├── occurred_at
├── created_at
└── updated_at
```

A memory belongs to a friend group.

It may contain one or more media items.

---

# 22. Media

`Media` represents a file stored in object storage.

Conceptual fields:

```text
Media
├── id
├── owner_id
├── group_id
├── object_key
├── media_type
├── file_size
├── metadata
├── created_at
└── deleted_at
```

The database stores metadata.

The actual file is stored in S3-compatible object storage.

---

# 23. MemoryMedia

`MemoryMedia` connects memories to media.

```text
MemoryMedia
├── memory_id
├── media_id
└── position
```

This allows a memory to contain multiple photos.

---

# 24. PersonalNote

`PersonalNote` represents a user's private note.

Conceptual fields:

```text
PersonalNote
├── id
├── user_id
├── title
├── content
├── created_at
├── updated_at
└── deleted_at
```

A personal note is accessible only to its owner.

---

# 25. SharedNote

Shared notes may eventually be supported.

Conceptually:

```text
SharedNote
├── id
├── group_id
├── created_by
├── title
├── content
├── created_at
└── updated_at
```

This can support:

* Shared lists
* Planning notes
* Ideas
* Group information

The distinction between personal and shared notes should remain explicit.

---

# 26. Reminder

`Reminder` represents a reminder for a user or group.

Conceptual fields:

```text
Reminder
├── id
├── owner_id
├── group_id
├── title
├── description
├── remind_at
├── completed_at
├── created_at
└── updated_at
```

A reminder may be:

* Personal
* Group-shared

The ownership model must be explicit.

---

# 27. Plan

`Plan` represents an event or shared plan.

Conceptual fields:

```text
Plan
├── id
├── owner_id
├── group_id
├── title
├── description
├── starts_at
├── ends_at
├── location
├── status
├── created_at
└── updated_at
```

Plans can originate from:

* Life
* Room activities
* Recommendations
* Manual creation

---

# 28. PlanParticipant

A plan may include multiple users.

```text
PlanParticipant
├── plan_id
├── user_id
├── status
└── responded_at
```

Possible statuses:

```text
PENDING
ACCEPTED
DECLINED
```

---

# 29. Notification

`Notification` represents a notification generated for a user.

Conceptual fields:

```text
Notification
├── id
├── user_id
├── category
├── title
├── body
├── data
├── sent_at
├── read_at
└── created_at
```

The notification record allows the system to track notification history without depending entirely on the push provider.

---

# 30. Device

A `Device` represents a registered mobile device capable of receiving push notifications.

Conceptual fields:

```text
Device
├── id
├── user_id
├── push_token
├── platform
├── app_version
├── last_seen_at
└── created_at
```

A user may have multiple devices.

---

# 31. Group Recommendation

Group-level recommendations may eventually need their own persistence.

Conceptual fields:

```text
GroupRecommendation
├── id
├── group_id
├── content_type
├── content_reference
├── created_by
├── created_at
└── expires_at
```

Examples:

* Movie recommendations
* Music
* Activities
* Restaurants
* Travel ideas

This is separate from an individual's recommendation history.

---

# 32. Relationships

The major relationships are:

```text
User
 ├── 1:M UserInterest
 ├── 1:M UserPreference
 ├── 1:M FeaturePreference
 ├── 1:M BehavioralSignal
 ├── 1:M Recommendation
 ├── 1:M DailyDrop
 ├── 1:M MoodEntry
 ├── 1:M PersonalNote
 ├── 1:M Reminder
 └── 1:M Device

User
 └── M:M FriendGroup
        via GroupMembership

FriendGroup
 ├── 1:M RoomMessage
 ├── 1:M GroupActivity
 ├── 1:M Memory
 ├── 1:M SharedNote
 ├── 1:M SharedPlan
 └── 1:M GroupRecommendation

Memory
 └── M:M Media
        via MemoryMedia

Plan
 └── M:M User
        via PlanParticipant

RoomMessage
 └── 1:M MessageReaction
```

---

# 33. Ownership Rules

Every piece of persistent data must have a clear ownership model.

## User-owned

Examples:

* Preferences
* Interests
* Personal notes
* Personal reminders
* Mood history
* Recommendation history
* Devices

## Group-owned

Examples:

* Room messages
* Shared memories
* Shared notes
* Group activities
* Group plans
* Group recommendations

## System-owned

Examples:

* Base configurations
* Invitation codes
* Recommendation source data
* Notification records

Ownership must be enforced at the backend authorization layer.

---

# 34. Privacy Rules

The database model must support strict access boundaries.

### Personal data

Only the owning user should be able to access it unless explicitly shared.

### Group data

Only group members should be able to access it.

### Administrative data

Internal configuration and claim-code data must not be exposed through normal user APIs.

---

# 35. Soft Deletion

Some entities may use soft deletion.

Potential candidates:

* Messages
* Memories
* Media
* Notes
* Reminders

Soft deletion may be useful where restoration, auditing, or relationship preservation matters.

It should not be applied blindly to every table.

---

# 36. Timestamps

Persistent entities should generally include:

```text
created_at
updated_at
```

where meaningful.

Event-like entities may only require:

```text
created_at
```

Timestamps should be stored consistently in UTC.

The client can convert them into the user's local timezone for display.

---

# 37. IDs

Entities should use stable non-sequential identifiers where appropriate.

UUIDs are the preferred initial choice for externally referenced entities.

IDs should not expose information about:

* User count
* Creation order
* Internal database structure

---

# 38. JSON Usage

JSON/JSONB may be used where data is naturally flexible.

Good candidates include:

* Base configuration
* Activity payloads
* Notification metadata
* External content metadata
* Recommendation context

However, important queryable relationships and core entities should remain properly structured relational data.

The database should not become a collection of giant JSON blobs.

---

# 39. Indexing Principles

Indexes should be created around real query patterns.

Likely indexes include:

```text
User.email

GroupMembership.user_id
GroupMembership.group_id

RoomMessage.group_id + created_at

Memory.group_id + occurred_at

Recommendation.user_id + created_at

DailyDrop.user_id + created_at

Reminder.owner_id + remind_at

Notification.user_id + created_at
```

Additional indexes should be introduced based on actual query requirements.

---

# 40. Constraints

The database should enforce important invariants wherever practical.

Examples:

* Unique user email
* Unique group membership per user/group
* Unique invitation code identity
* Valid foreign-key relationships
* Non-null ownership fields
* Valid enum values
* Unique plan participation per user/plan
* Unique reaction per user/message/reaction where appropriate

Business rules that require application context should remain in the service layer.

---

# 41. Transaction Boundaries

Operations that modify multiple related entities should use database transactions.

Important examples:

### Claim Code

```text
Validate code
+
Create user
+
Attach configuration
+
Consume code
```

These operations should succeed or fail together.

### Memory Creation

```text
Create memory
+
Associate media
```

### Group Plan Creation

```text
Create plan
+
Create participants
```

The application should avoid partially completed state.

---

# 42. Initial Schema Scope

The first implementation should prioritize the entities required for the core experience.

### Phase 1

* User
* FriendGroup
* GroupMembership
* InvitationCode
* BaseConfiguration
* UserInterest
* UserPreference
* FeaturePreference

### Phase 2

* Recommendation
* RecommendationInteraction
* DailyDrop
* MoodEntry

### Phase 3

* RoomMessage
* MessageReaction
* GroupActivity
* GroupActivityResponse

### Phase 4

* Memory
* Media
* MemoryMedia

### Phase 5

* Notes
* Reminders
* Plans
* PlanParticipants

### Phase 6

* Notifications
* Devices
* Additional personalization data

This ordering may change during implementation.

---

# 43. Schema Non-Goals

The initial schema should not attempt to model:

* Public followers
* Public posts
* Creator accounts
* Advertising
* Payments
* Complex recommendation ML infrastructure
* Multi-tenant enterprise organizations
* Analytics warehouses

These can be considered separately if the product direction changes.

---

# 44. Future Expansion

The schema should remain capable of supporting:

* Multiple friend groups per user
* Richer group personalization
* More recommendation types
* AI-generated content
* More media types
* Android devices
* Advanced activity types

However, future possibilities should not result in speculative tables being created prematurely.

---

# 45. Definition of Done

This database specification is considered complete enough for API design when:

* Core entities are identified.
* User ownership is defined.
* Group ownership is defined.
* Invitation-code flow is represented.
* Personalization data is represented.
* Recommendation data is represented.
* Room data is represented.
* Memory/media relationships are represented.
* Life tools are represented.
* Notification/device data is represented.
* Major relationships are defined.
* Privacy boundaries are explicit.
* Transaction boundaries are identified.
* Initial indexing principles are documented.
* V1 schema scope is separated from future expansion.

This document defines the **conceptual persistence model**.

Exact SQLAlchemy models, migrations, constraints, and indexes will be implemented after the API contracts are finalized.