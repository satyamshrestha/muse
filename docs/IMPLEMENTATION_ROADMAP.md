# Implementation Roadmap

**Project:** MUSE
**Document:** Implementation Roadmap
**Status:** Initial Specification
**Version:** 0.1
**Related Documents:** `PRODUCT_SPEC.md`, `UX_ARCHITECTURE.md`, `PERSONALIZATION.md`, `TECHNICAL_ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `API_CONTRACT.md`

---

# 1. Purpose

This document defines the implementation sequence for MUSE.

The purpose is to answer:

* What should be built first?
* What depends on what?
* When should the mobile application begin?
* When should personalization be implemented?
* When should realtime functionality be added?
* When should media storage be added?
* When should push notifications be added?
* When is the application ready for real users?
* What should be tested before deployment?

The roadmap is intentionally sequential.

MUSE should be built as one complete product rather than as a collection of disconnected features.

---

# 2. Implementation Philosophy

The implementation follows these principles:

### Build foundations before features

Infrastructure, database, authentication, and API foundations should exist before feature development becomes extensive.

### Build vertical slices

Whenever practical, implement a feature across the entire stack:

```text
Database
   ↓
Backend service
   ↓
API
   ↓
Mobile client
   ↓
Testing
```

Instead of building the entire backend first and the entire mobile application afterward.

### Keep the architecture proportional

Do not introduce infrastructure simply because it appears in a typical production architecture.

MUSE starts as:

```text
React Native / Expo
        ↓
FastAPI
        ↓
PostgreSQL
        ↓
Object Storage
```

with WebSockets and push notifications added where they provide real value.

---

# 3. Overall Development Sequence

```text
Phase 0  → Repository & Development Environment
Phase 1  → Backend Foundation
Phase 2  → Database & Migrations
Phase 3  → Authentication
Phase 4  → Onboarding & Personalization
Phase 5  → Mobile Foundation
Phase 6  → Home
Phase 7  → Discover & Daily Drop
Phase 8  → Mood → World
Phase 9  → The Room
Phase 10 → Memories & Media
Phase 11 → Life
Phase 12 → Notifications
Phase 13 → Personalization Refinement
Phase 14 → Testing & Reliability
Phase 15 → Production Deployment
Phase 16 → iOS Release & Real-User Validation
```

The phases are sequential at the architectural level, but individual implementation tasks may overlap where appropriate.

---

# 4. Phase 0 — Repository & Development Environment

## Goal

Create the initial project structure and establish the development workflow.

## Tasks

Create the repository structure:

```text
muse/
├── backend/
├── mobile/
├── docs/
├── .gitignore
└── README.md
```

Set up:

* Git
* Python environment
* Node.js
* Expo
* TypeScript
* FastAPI
* PostgreSQL
* Environment configuration

Establish:

* Development commands
* Environment variable conventions
* Code formatting
* Linting
* Basic Git workflow

## Completion Criteria

* Repository initializes successfully.
* Backend runs locally.
* Expo application starts.
* Mobile application can connect to development backend.
* Environment configuration is documented.

---

# 5. Phase 1 — Backend Foundation

## Goal

Create the basic FastAPI application architecture.

## Tasks

Implement:

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
└── requirements.txt
```

Add:

* FastAPI application
* Configuration management
* Database session management
* Dependency injection
* Exception handling
* Logging
* Health endpoint
* API versioning

Initial endpoint:

```text
GET /api/v1/health
```

## Completion Criteria

The backend starts cleanly and provides a functioning health endpoint.

---

# 6. Phase 2 — Database & Migrations

## Goal

Implement the persistence layer defined in `DATABASE_SCHEMA.md`.

## Tasks

Set up:

* PostgreSQL
* SQLAlchemy
* Alembic

Implement initial models:

```text
User
FriendGroup
GroupMembership
InvitationCode
BaseConfiguration
UserInterest
UserPreference
FeaturePreference
NotificationPreference
```

Create the initial migration.

Add:

* Foreign keys
* Unique constraints
* Required indexes
* Enum definitions
* Timestamp handling

## Completion Criteria

A fresh database can be created entirely through migrations.

The application can:

```text
create database
→ run migrations
→ start backend
→ access database
```

without manual schema modification.

---

# 7. Phase 3 — Authentication

## Goal

Create secure account access.

## Tasks

Implement:

* Invitation claim flow
* Registration
* Login
* JWT access tokens
* Refresh tokens
* Logout
* Current-user dependency
* Password hashing
* Authentication error handling

Endpoints:

```text
POST /auth/claim
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
```

Implement authorization utilities.

## Completion Criteria

A new user can:

```text
claim invitation
→ create account
→ log in
→ receive tokens
→ access protected endpoints
```

An unauthenticated user cannot access protected resources.

---

# 8. Phase 4 — Onboarding & Personalization

## Goal

Make MUSE understand the user before building the personalized experience.

## Tasks

Implement:

* Interest selection
* Feature preferences
* Personality/chaos preference
* Notification preferences
* Base configuration application
* Onboarding completion
* Personalization retrieval/update

Endpoints:

```text
GET   /onboarding
PUT   /onboarding/interests
PUT   /onboarding/preferences
POST  /onboarding/complete

GET   /personalization
PATCH /personalization
POST  /personalization/reset
```

Implement the initial deterministic personalization engine.

The first version should use:

```text
User interests
+
Feature preferences
+
Personality preference
+
Current context
```

No machine learning is required.

## Completion Criteria

Two users with different preferences should receive meaningfully different personalization output.

---

# 9. Phase 5 — Mobile Foundation

## Goal

Create the real iOS application shell.

## Tasks

Set up:

* React Native
* Expo
* TypeScript
* Navigation
* API client
* Authentication state
* Secure token storage
* Environment configuration
* Loading states
* Error states
* Basic design system

Initial navigation:

```text
Home
Discover
Room
Memories
Life
More
```

Implement:

```text
Splash
   ↓
Authentication
   ↓
Onboarding
   ↓
Main Application
```

## Completion Criteria

A real iOS device can:

```text
install app
→ authenticate
→ complete onboarding
→ reach main application
```

---

# 10. Phase 6 — Home

## Goal

Build the central MUSE experience.

Home should not simply be a menu.

It should answer:

> "What's waiting for me?"

## Tasks

Implement:

* Personalized greeting
* Daily Drop preview
* Mood prompt
* Recent memories
* Room activity
* Recommendations
* Quick actions
* Personalized feature ordering

Backend:

```text
GET /home
```

Mobile:

* Home layout
* Cards
* Navigation
* Loading states
* Empty states
* Pull-to-refresh where useful

## Completion Criteria

Opening the app feels like entering a personalized space rather than opening a utility dashboard.

---

# 11. Phase 7 — Discover & Daily Drop

## Goal

Build the primary discovery engine.

## Discover

Implement:

* Music
* Movies
* Books
* Psychology
* Travel
* Food
* Facts
* Questions
* Challenges
* Random discoveries

Initial content selection should be deterministic/tag-based.

Implement:

```text
GET  /discover
POST /discover/{id}/feedback
```

## Daily Drop

Implement:

```text
GET  /daily-drop
POST /daily-drop/{id}/open
POST /daily-drop/{id}/feedback
```

Daily Drop generation should use:

```text
User profile
+
Interests
+
Feature preferences
+
Recent interactions
+
Diversity rules
+
Current context
```

## Completion Criteria

A user can open the app and reliably encounter something personally relevant without manually searching for it.

---

# 12. Phase 8 — Mood → World

## Goal

Turn temporary mood into a personalized experience.

## Tasks

Implement:

```text
POST /mood
GET  /mood/world
```

A Mood → World response may contain:

```text
Song
Movie
Fact
Question
Activity
Recommendation
Random element
```

The composition should vary according to:

* Mood
* Energy
* Interests
* Personality
* Recent activity

## Completion Criteria

Changing the mood should meaningfully change the resulting experience.

---

# 13. Phase 9 — The Room

## Goal

Build the shared social space.

## Tasks

Implement:

* Group retrieval
* Message history
* Message creation
* Editing/deletion
* Reactions
* Activities
* Polls
* Questions
* Challenges

REST:

```text
GET  /groups/{id}/room/messages
POST /groups/{id}/room/messages
```

WebSocket:

```text
/ws/v1/groups/{id}/room
```

Implement realtime events for:

* New messages
* Message changes
* Reactions
* Activities

## Completion Criteria

Three users can have a reliable realtime conversation without refreshing the application.

The Room should feel like a lightweight shared space, not a replacement for WhatsApp.

---

# 14. Phase 10 — Memories & Media

## Goal

Build the friendship memory layer.

## Tasks

Implement:

* Memory creation
* Memory browsing
* Memory details
* Photo uploads
* Multiple media per memory
* Memory deletion
* Media metadata

Set up S3-compatible object storage.

Implement signed upload URLs.

Flow:

```text
Mobile
 ↓
API requests upload URL
 ↓
Object storage
 ↓
Upload
 ↓
API confirms media
 ↓
Memory references media
```

## Completion Criteria

Users can create a memory, attach photos, and later rediscover it from the application.

---

# 15. Phase 11 — Life

## Goal

Integrate useful everyday tools.

Implement:

### Notes

```text
GET
POST
PATCH
DELETE
```

### Reminders

```text
GET
POST
PATCH
COMPLETE
DELETE
```

### Plans

```text
GET
POST
GET BY ID
PATCH
RESPOND
```

The Life section should remain useful without becoming a full productivity platform.

## Completion Criteria

A user can realistically use MUSE for small everyday planning tasks.

---

# 16. Phase 12 — Notifications

## Goal

Make MUSE capable of naturally returning to the user's life.

## Tasks

Set up:

* Expo Notifications
* Device registration
* Notification preferences
* Notification records
* Reminder notifications
* Daily Drop notifications
* Memory resurfacing
* Room activity notifications

Notification philosophy:

```text
Useful
+
Occasionally playful
+
Context-aware
-
Guilt
-
Spam
-
Streak pressure
```

Notifications should not become the product.

They should create occasional moments of:

> "Wait, why did MUSE send me this 😂"

## Completion Criteria

Notifications are reliable, controllable, and infrequent enough to remain welcome.

---

# 17. Phase 13 — Personalization Refinement

## Goal

Improve personalization based on actual usage.

Only after the basic product works should behavioral learning become more sophisticated.

## Tasks

Track meaningful signals:

```text
Opened
Liked
Saved
Skipped
Dismissed
Shared
Used
```

Improve:

* Recommendation ranking
* Repetition avoidance
* Interest weighting
* Feature prominence
* Daily Drop selection
* Mood recommendations
* Notification timing
* Exploration vs familiarity

Implement explicit controls such as:

```text
More like this
Not interested
Reset learned preferences
```

## Completion Criteria

The application becomes noticeably better at matching the user without requiring manual configuration for everything.

---

# 18. Phase 14 — Testing & Reliability

## Goal

Make MUSE trustworthy enough for real daily use.

Testing should exist at multiple levels.

## Backend Unit Tests

Test:

* Services
* Personalization logic
* Authentication
* Validation
* Authorization
* Recommendation scoring

## API Integration Tests

Test:

* Authentication flows
* Database interactions
* Group authorization
* CRUD operations
* Error responses

## Mobile Tests

Test critical:

* Authentication
* Onboarding
* Navigation
* Home loading
* Room behavior
* Memory creation
* Life tools

## End-to-End Scenarios

At minimum:

### New User

```text
Invitation
→ Registration
→ Login
→ Onboarding
→ Home
```

### Daily Experience

```text
Open app
→ Daily Drop
→ Discover
→ Feedback
```

### Social

```text
User A sends message
→ User B receives realtime update
→ User B reacts
→ User A sees reaction
```

### Memory

```text
Create memory
→ Upload photo
→ Save
→ Reopen later
```

### Planning

```text
Create plan
→ Invite group
→ Member responds
```

## Reliability

Add:

* Structured logging
* Health checks
* Error tracking
* Basic metrics
* Database backup strategy
* API monitoring

## Completion Criteria

Critical user flows work consistently across clean installs and real devices.

---

# 19. Phase 15 — Production Deployment

## Goal

Move MUSE from development infrastructure to a real hosted environment.

## Tasks

Deploy:

```text
Mobile
   ↓
HTTPS
   ↓
FastAPI
   ↓
PostgreSQL
   ↓
Object Storage
```

Configure:

* Production database
* HTTPS
* Domain
* Environment variables
* Secrets
* Database migrations
* Logging
* Monitoring
* Backups

The backend must not depend on the developer's local machine.

## Completion Criteria

The mobile application communicates with a publicly reachable production backend over HTTPS.

The entire system survives restarting the developer's computer.

---

# 20. Phase 16 — iOS Release & Real-User Validation

## Goal

Install MUSE on actual devices and use it as a real application.

Initial users:

* User
* Aarya
* Eliska

## Tasks

Create:

* Production Expo configuration
* App icon
* Splash screen
* App metadata
* Production environment
* Release build

Distribute through an appropriate iOS testing/release mechanism.

Then use the application normally.

Do not immediately assume the product is finished.

Observe:

* What gets opened?
* What gets ignored?
* Which notifications are annoying?
* Which features become habitual?
* What feels slow?
* What feels pointless?
* What makes someone open the app voluntarily?

## Completion Criteria

The three initial users can install and use MUSE independently without development infrastructure.

---

# 21. Development Commit Strategy

Commits should represent meaningful engineering milestones.

Avoid commits such as:

```text
fix stuff
update files
more changes
random backend
```

Prefer:

```text
feat: initialize backend application
feat: add database models
feat: implement authentication
feat: implement onboarding
feat: add personalization engine
feat: add home experience
feat: implement daily drop
feat: add discover experience
feat: add mood world
feat: implement realtime room
feat: add memory media uploads
feat: implement life tools
feat: add push notifications
test: cover critical user flows
chore: prepare production deployment
```

The exact number of commits is not important.

The history should communicate meaningful development progression.

---

# 22. Feature Completion Standard

A feature is not considered complete simply because the endpoint works.

Each feature should generally include:

```text
Database
+
Backend logic
+
API
+
Mobile UI
+
Loading state
+
Empty state
+
Error handling
+
Authorization
+
Testing
```

For relevant features also include:

```text
Offline behavior
+
Notifications
+
Realtime behavior
+
Analytics/metrics
```

Only when applicable.

---

# 23. MVP Definition

MUSE's first real MVP consists of:

```text
Authentication
Onboarding
Personalization
Home
Daily Drop
Discover
Mood → World
The Room
Memories
Basic Life tools
Notifications
```

The MVP must be:

* Installable
* Hosted
* Authenticated
* Persistent
* Private
* Usable on real devices
* Reliable enough for everyday use

---

# 24. What Does NOT Block MVP

The following are explicitly not required before the first real release:

* Machine-learning recommendation models
* AI everywhere
* Kubernetes
* Microservices
* Redis
* Celery
* Complex analytics infrastructure
* Public social features
* Android release
* Public App Store launch
* Enterprise-grade scaling

These can be introduced only when the product actually needs them.

---

# 25. Post-MVP Evolution

After real usage, development should be driven by observed behavior rather than speculation.

Potential future work:

```text
Better personalization
Advanced recommendation models
AI-generated experiences
Smarter notification timing
Richer games
Friendship timeline
Advanced memory resurfacing
More content providers
Android
Public release
```

Features should be added because they improve the product, not because they make the technology stack look more impressive.

---

# 26. Product Feedback Loop

After deployment:

```text
Build
 ↓
Use
 ↓
Observe
 ↓
Identify friction
 ↓
Improve
 ↓
Deploy
 ↓
Use again
```

The three initial users are not simply testers.

They are the first real users of the product.

Their actual behavior should influence future product decisions.

---

# 27. Definition of Done

MUSE's initial implementation is considered complete when:

* The backend is production-hosted.
* PostgreSQL is persistent and backed up.
* Authentication works.
* Invitation onboarding works.
* Users can configure personalization.
* Home provides a personalized experience.
* Daily Drop works.
* Discover works.
* Mood → World works.
* The Room supports realtime interaction.
* Memories support media.
* Life tools are usable.
* Push notifications work.
* Authorization protects private/group data.
* Critical flows are tested.
* Errors are handled gracefully.
* Logging and basic monitoring exist.
* The application works on real iOS devices.
* The three initial users can use the application without developer intervention.

At this point, MUSE stops being a development project and becomes a **real product in use**.

---

# 28. Final Development Principle

The goal is not:

> Build every possible feature.

The goal is:

> Build a small, beautiful, personalized digital world that three people genuinely want to keep using.

Engineering decisions should serve that goal.

Product decisions should serve that goal.

Architecture should serve that goal.

Anything that does not improve the actual product should be questioned before it is built.