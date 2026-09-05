# Initial Technical Architecture

**Project:** MUSE
**Document:** Initial Technical Architecture
**Status:** Initial Specification
**Version:** 0.1
**Platform:** iOS-first
**Related Documents:** `PRODUCT_SPEC.md`, `UX_ARCHITECTURE.md`, `PERSONALIZATION.md`

---

# 1. Purpose

This document defines the initial technical architecture for MUSE.

The architecture is designed around three requirements:

1. The application must be a real, installable mobile product.
2. The backend must be remotely deployed and usable without localhost dependencies.
3. The system should be technically strong without unnecessary infrastructure complexity.

The architecture should support the current private deployment while remaining capable of supporting a broader friend-group product in the future.

---

# 2. Architecture Principles

## 2.1 Mobile-First Product

The primary client is a mobile application.

The initial platform is iOS.

The application should be built using:

* React Native
* Expo
* TypeScript

Android compatibility should remain possible without making Android the initial development priority.

---

## 2.2 Simple Backend

The backend should begin as a modular monolithic application.

The initial backend will use:

* Python
* FastAPI
* PostgreSQL

The backend should have clear internal boundaries without being split into microservices.

---

## 2.3 Production From the Beginning

The application should use a real deployed backend.

The mobile application should communicate with the backend over HTTPS.

The production application must never depend on:

```text
localhost
127.0.0.1
developer machine
local network
```

Local development may use localhost.

Production may not.

---

## 2.4 Avoid Premature Infrastructure

The initial system does not require:

* Kubernetes
* Microservices
* Celery
* Redis
* Service meshes
* Complex event buses
* Distributed tracing infrastructure
* Dedicated recommendation clusters

Infrastructure should be added when actual product requirements justify it.

---

# 3. High-Level Architecture

The initial architecture is:

```text
┌─────────────────────────┐
│     iOS Application     │
│ React Native + Expo     │
│       TypeScript        │
└────────────┬────────────┘
             │ HTTPS
             │ WebSocket
             ▼
┌─────────────────────────┐
│       FastAPI API       │
│     Python Backend      │
└───────┬───────┬─────────┘
        │       │
        │       ├──────────────► Object Storage
        │       │                 Photos / Media
        │       │
        │       └──────────────► External APIs
        │                         Content / Services
        │
        ▼
┌─────────────────────────┐
│       PostgreSQL        │
│   Persistent App Data   │
└─────────────────────────┘

              ┌─────────────────────┐
              │ Push Notifications  │
              │  Expo Notifications │
              └─────────────────────┘
```

The backend remains the primary source of truth.

---

# 4. Mobile Application

## Technology

The mobile client will use:

* React Native
* Expo
* TypeScript

Expo is preferred because it provides a practical development and deployment workflow for an iOS-first React Native application.

---

# 5. Mobile Architecture

The mobile application should be organized by product/domain responsibility rather than placing everything into a single component structure.

Conceptually:

```text
mobile/
├── app/
│   ├── auth/
│   ├── onboarding/
│   ├── home/
│   ├── discover/
│   ├── room/
│   ├── memories/
│   ├── life/
│   └── more/
│
├── components/
├── features/
├── hooks/
├── services/
├── store/
├── types/
├── utils/
└── assets/
```

The exact Expo Router structure may differ during implementation.

The important requirement is clear separation between:

* Screens
* Reusable UI
* Feature logic
* API communication
* Local state
* Shared utilities

---

# 6. Navigation

The application should use a primary navigation structure corresponding to:

```text
Home
Discover
Room
Memories
Life
More
```

Authentication and onboarding exist outside the primary application navigation.

Conceptually:

```text
Unauthenticated
      ↓
Authentication
      ↓
Onboarding
      ↓
Main Application
```

---

# 7. Backend

## Technology

The backend will use:

* Python
* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL

The backend should expose a REST API for normal application operations.

WebSockets will be used where real-time interaction provides meaningful value.

---

# 8. Backend Architecture

The backend should follow a modular structure.

Conceptually:

```text
backend/
├── app/
│   ├── api/
│   ├── auth/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── personalization/
│   ├── notifications/
│   └── main.py
│
├── migrations/
├── tests/
├── uploads/
└── ...
```

The exact structure can evolve as implementation begins.

---

# 9. API Layer

FastAPI will expose versioned API endpoints.

Conceptually:

```text
/api/v1/auth
/api/v1/users
/api/v1/onboarding
/api/v1/home
/api/v1/discover
/api/v1/daily-drop
/api/v1/mood
/api/v1/room
/api/v1/memories
/api/v1/life
/api/v1/personalization
/api/v1/notifications
```

The API should be organized around product domains rather than individual database tables.

---

# 10. Database

PostgreSQL is the primary persistent datastore.

The database will store structured application data such as:

* Users
* Friend groups
* Memberships
* Preferences
* Interests
* Feature configuration
* Recommendations
* Recommendation feedback
* Daily Drops
* Mood selections
* Room messages
* Room activities
* Memories
* Media metadata
* Plans
* Reminders
* Notes
* Notifications
* Invitation/claim codes

The exact schema will be designed separately before implementation.

---

# 11. Database Ownership Model

The application should distinguish between:

### User-owned data

Examples:

* Preferences
* Notes
* Personal reminders
* Personal configuration
* Recommendation history

### Group-owned data

Examples:

* Room messages
* Shared memories
* Group activities
* Shared plans
* Group recommendations

This distinction should be represented explicitly in the data model.

---

# 12. Authentication

Initial authentication should remain simple.

The application will support:

* Account creation
* Login
* Logout
* Secure session/token handling
* Password-based authentication
* Invitation/claim codes for private seeded users

JWT-based authentication is appropriate for the initial architecture.

The implementation should avoid unnecessary authentication complexity.

---

# 13. Invitation / Claim Codes

Invitation codes are a private deployment mechanism.

A code represents a one-time claim for a predefined configuration.

Conceptually:

```text
Claim Code
    ↓
Validate
    ↓
Find predefined configuration
    ↓
Create account
    ↓
Attach configuration
    ↓
Mark code consumed
```

The code should not become the user's permanent identifier.

Security requirements:

* Codes must be unique.
* Codes must be stored securely.
* Codes must be single-use.
* Consumed codes cannot be reused.
* Invalid codes must fail safely.
* Codes should not expose unnecessary user information.

---

# 14. Personalization Engine

Personalization will initially live inside the backend as a dedicated module.

It does not need to be a separate service.

Conceptually:

```text
personalization/
├── scoring
├── ranking
├── profiles
├── recommendations
├── mood
└── signals
```

The initial engine will use deterministic rules and scoring.

---

# 15. Recommendation Flow

A recommendation request may follow:

```text
User Request
      ↓
Load User Configuration
      ↓
Load Relevant Context
      ↓
Retrieve Candidate Content
      ↓
Apply Preference Matching
      ↓
Apply History / Freshness
      ↓
Apply Diversity
      ↓
Apply Controlled Randomness
      ↓
Rank Results
      ↓
Return Recommendation
```

The recommendation engine should remain easy to inspect and modify.

---

# 16. External Content

MUSE will eventually depend on external sources for certain content.

Potential categories include:

* Music
* Movies
* Books
* Food
* Travel
* General information

External APIs should be accessed through backend services rather than directly from the mobile client whenever practical.

This provides:

* Centralized credentials
* Consistent data transformation
* Better security
* Easier provider replacement
* Centralized caching if needed later

---

# 17. Object Storage

Photos and other user media should not be stored directly inside PostgreSQL.

An S3-compatible object storage service will be used.

Conceptually:

```text
Mobile
   ↓
Backend
   ↓
Object Storage
   ↓
Media URL / reference
   ↓
PostgreSQL metadata
```

PostgreSQL stores metadata such as:

* Object key
* Owner
* Group
* Media type
* Upload timestamp
* Associated memory

The actual binary media remains in object storage.

---

# 18. Media Uploads

Media upload should eventually support:

* Photos
* Potentially other media types
* Upload progress
* Validation
* Size limits
* Secure access
* Deletion

The initial implementation should prioritize photos.

Video and large media processing can be introduced later.

---

# 19. Real-Time Communication

WebSockets will be used where real-time updates materially improve the experience.

The primary initial use case is The Room.

Potential real-time events include:

* New message
* Reaction
* Poll update
* Group activity
* Shared interaction

Conceptually:

```text
Client A
   │
   │ WebSocket
   ▼
FastAPI
   │
   ├──► Client B
   └──► Client C
```

The system should not use WebSockets for functionality that works naturally through normal HTTP requests.

---

# 20. Push Notifications

Push notifications will use Expo Notifications.

The backend will manage notification decisions.

Conceptually:

```text
User activity / scheduled event
            ↓
Notification decision
            ↓
Backend
            ↓
Expo notification service
            ↓
iOS device
```

The backend should determine:

* Whether a notification should be sent.
* Which category it belongs to.
* Appropriate timing.
* Appropriate tone.
* Whether the user has disabled that category.

---

# 21. Notification Scheduling

The initial system should avoid introducing a dedicated task-processing infrastructure unless required.

Possible approaches include:

* Application-level scheduled jobs
* Hosting-platform scheduled tasks
* Database-backed scheduled records
* External scheduling facilities

The exact mechanism will depend on deployment requirements.

A dedicated queue system should only be introduced if notification volume or workload makes it necessary.

---

# 22. Caching

Caching is not a required part of the initial architecture.

PostgreSQL and appropriate application-level logic should be sufficient initially.

Caching may be introduced later for:

* Expensive external API responses
* Frequently requested discovery content
* Recommendation candidates
* High-frequency read operations

Redis should not be introduced merely because it is familiar from other projects.

---

# 23. Background Work

The initial application should avoid a dedicated distributed task queue.

If background work is required, start with the simplest suitable mechanism.

Potential background work includes:

* Notification scheduling
* Content refresh
* Recommendation preparation
* Media processing

A task queue may be introduced later if actual workloads justify it.

---

# 24. API Security

The backend should enforce:

* Authentication
* Authorization
* Input validation
* Ownership checks
* Group membership checks
* Rate limiting where appropriate
* Secure password storage
* Secure token handling
* HTTPS in production

A user must never be able to access another user's private data merely by changing an identifier in a request.

Authorization must be enforced server-side.

---

# 25. Group Isolation

Friend-group data must be isolated.

A user should only be able to access data belonging to:

* Their own account
* Friend groups they belong to
* Resources explicitly shared with them

This applies to:

* Room messages
* Memories
* Shared plans
* Group activities
* Media
* Recommendations

---

# 26. Environment Configuration

Environment-specific configuration must not be hard-coded.

Examples:

```text
DATABASE_URL
SECRET_KEY
OBJECT_STORAGE_ENDPOINT
OBJECT_STORAGE_BUCKET
OBJECT_STORAGE_ACCESS_KEY
OBJECT_STORAGE_SECRET_KEY
EXTERNAL_API_KEYS
EXPO_NOTIFICATION_CONFIGURATION
```

Secrets must not be committed to the repository.

Development and production environments should use separate credentials and configuration.

---

# 27. Deployment

The backend must be deployed to a cloud-hosted environment.

Production architecture should provide:

* HTTPS
* Persistent PostgreSQL
* Object storage
* Backend hosting
* Environment variables
* Database migrations
* Logs
* Basic monitoring
* Automated or repeatable deployment

The mobile application communicates only with the production API when running as a production build.

---

# 28. Reverse Proxy

A reverse proxy may sit in front of the FastAPI application.

Conceptually:

```text
Internet
    ↓
HTTPS
    ↓
Reverse Proxy
    ↓
FastAPI
    ↓
PostgreSQL / Object Storage / External APIs
```

The exact reverse proxy and hosting arrangement can be chosen during deployment.

Nginx is an acceptable option but is not mandatory if the chosen hosting platform provides equivalent functionality.

---

# 29. Database Migrations

Alembic will manage database schema migrations.

The project should never rely on manually modifying production database schemas.

Schema changes should follow:

```text
Model change
    ↓
Migration
    ↓
Review
    ↓
Migration execution
    ↓
Updated production schema
```

---

# 30. Testing Strategy

Testing should exist at multiple levels.

## Unit Tests

Test isolated logic such as:

* Recommendation scoring
* Personalization
* Validation
* Utility functions
* Permission checks

## API Tests

Test:

* Authentication
* Endpoints
* Authorization
* Database interactions
* Error handling

## Mobile Tests

Test important UI and interaction behavior where practical.

## End-to-End Tests

Critical user journeys should eventually be tested.

Examples:

```text
Signup
   ↓
Onboarding
   ↓
Home
```

and:

```text
Login
   ↓
Room
   ↓
Send message
   ↓
Receive update
```

and:

```text
Upload memory
   ↓
Store media
   ↓
View memory
```

Testing should focus on important user behavior rather than maximizing meaningless coverage percentages.

---

# 31. Observability

The initial production system should provide basic observability.

At minimum:

* Application logs
* Error tracking
* Request logging
* Basic health checks
* Deployment visibility

The project does not initially require a complex observability stack.

The system should be able to answer:

> "Is the application working?"

and:

> "What went wrong when it wasn't?"

More advanced monitoring can be added as the product grows.

---

# 32. Health Checks

The backend should expose a health endpoint.

Conceptually:

```text
GET /health
```

It should allow deployment infrastructure to determine whether the application is running.

A more detailed readiness check may later verify dependencies such as PostgreSQL.

---

# 33. Logging

Backend logs should contain useful operational context.

Potential fields:

* Timestamp
* Request ID
* Route
* HTTP method
* Status code
* Execution time
* User identifier where appropriate
* Error information

Sensitive information must not be logged unnecessarily.

Passwords, tokens, private media data, and secrets must never be logged.

---

# 34. Error Handling

The backend should expose consistent API errors.

Errors should:

* Use appropriate HTTP status codes.
* Provide safe user-facing messages.
* Avoid exposing internal implementation details.
* Be logged internally when appropriate.

The mobile application should translate API failures into useful UX states.

---

# 35. API Versioning

The initial API should use a versioned prefix:

```text
/api/v1
```

This provides a clean path for future breaking changes.

The project should avoid introducing multiple API versions until they are actually needed.

---

# 36. Data Ownership & Deletion

Users should eventually be able to manage their data.

The architecture should account for:

* Account deletion
* Personal data deletion
* Memory deletion
* Media deletion
* Preference reset

Group-owned data requires explicit ownership rules.

Deleting a user should not accidentally delete shared content belonging to an entire group unless that behavior is explicitly defined.

---

# 37. Performance Principles

Initial performance priorities are:

1. Fast application startup.
2. Responsive navigation.
3. Fast Home loading.
4. Efficient API requests.
5. Efficient media loading.
6. Smooth Room interactions.
7. Avoid unnecessary network requests.

The project should optimize based on actual measurements rather than premature optimization.

---

# 38. Scalability Philosophy

The initial application is designed for a small user base.

The architecture should nevertheless avoid decisions that make future growth unnecessarily difficult.

The desired progression is:

```text
Simple architecture
      ↓
Measure actual usage
      ↓
Identify bottleneck
      ↓
Solve specific bottleneck
      ↓
Repeat
```

Not:

```text
Predict hypothetical scale
      ↓
Build massive infrastructure
      ↓
Maintain infrastructure nobody needs
```

---

# 39. Development Environment

Local development should support:

```text
Mobile App
    ↓
Local FastAPI
    ↓
Local PostgreSQL
```

Environment variables should allow the mobile application to switch between development and production API endpoints.

The production build must never accidentally point at localhost.

---

# 40. Repository Structure

The initial repository should eventually resemble:

```text
muse/
├── mobile/
├── backend/
├── docs/
│   ├── PRODUCT_SPEC.md
│   ├── UX_ARCHITECTURE.md
│   ├── PERSONALIZATION.md
│   └── TECHNICAL_ARCHITECTURE.md
│
├── .gitignore
├── README.md
└── ...
```

The exact repository structure may evolve during implementation.

---

# 41. CI/CD

The project should eventually use automated CI.

Initial CI should verify:

* Backend tests
* Backend linting
* Type checking
* Mobile linting
* Mobile type checking
* Build-related checks where practical

Deployment automation can be introduced once the production environment is established.

The first priority is reliable verification, not an elaborate pipeline.

---

# 42. Secrets & Sensitive Configuration

The repository must never contain:

* Passwords
* API keys
* JWT secrets
* Object storage credentials
* Database production credentials
* Private notification credentials

Development secrets should use local environment configuration.

Production secrets should be stored using the hosting provider's secure configuration system.

---

# 43. External Dependency Philosophy

External services should be introduced only when they solve a meaningful product requirement.

Potential dependencies include:

* Content APIs
* Object storage
* Push notification infrastructure
* App distribution services

Each dependency should have a clear purpose.

The architecture should avoid becoming dependent on unnecessary third-party services.

---

# 44. AI / LLM Integration

AI is optional.

The initial product should not depend on an LLM for its fundamental functionality.

AI may eventually be useful for:

* Personalized explanations
* Generated questions
* Mood experiences
* Mystery generation
* Recommendation narratives
* Natural-language discovery
* Personalized Daily Drops

If introduced, AI should exist behind a clean backend abstraction.

The rest of the application should not depend directly on a specific AI provider.

---

# 45. Security Baseline

Before production release, the application must have:

* HTTPS
* Secure password hashing
* Secure authentication tokens
* Server-side authorization
* Input validation
* Database access controls
* Secure media access
* Rate limiting where appropriate
* Secret management
* Safe error handling
* Dependency updates

Security should be treated as part of the product rather than a later feature.

---

# 46. Initial Architecture Decision Summary

| Area               | Initial Decision                    |
| ------------------ | ----------------------------------- |
| Mobile             | React Native + Expo                 |
| Language           | TypeScript                          |
| Backend            | FastAPI + Python                    |
| Database           | PostgreSQL                          |
| ORM                | SQLAlchemy                          |
| Migrations         | Alembic                             |
| Authentication     | JWT + email/password                |
| Private onboarding | One-time claim codes                |
| Media              | S3-compatible object storage        |
| Real-time          | FastAPI WebSockets                  |
| Push               | Expo Notifications                  |
| Personalization    | Backend Python module               |
| Recommendations    | Deterministic/tag-based initially   |
| AI                 | Optional / later                    |
| Cache              | Not initially required              |
| Queue              | Not initially required              |
| Architecture       | Modular monolith                    |
| Deployment         | Cloud-hosted                        |
| Transport          | HTTPS                               |
| API                | REST + WebSockets where appropriate |
| Platform           | iOS-first                           |
| Android            | Later                               |
| CI/CD              | Yes                                 |
| Kubernetes         | No                                  |
| Microservices      | No                                  |

---

# 47. Architecture Decision Principles

When future technical decisions are made, they should be evaluated against these questions:

### 1. Does the product actually need it?

If not, do not add it.

### 2. Does it make the application meaningfully better?

Infrastructure should serve the product.

### 3. Does it increase operational complexity?

If yes, the benefit must justify the cost.

### 4. Can the simpler solution work for the current scale?

If yes, prefer it.

### 5. Can we replace it later?

Avoid unnecessary architectural lock-in.

---

# 48. Definition of Done

This technical architecture is considered complete enough to begin implementation planning when:

* Mobile stack is defined.
* Backend stack is defined.
* Database technology is defined.
* Authentication approach is defined.
* Invitation/claim-code flow is defined technically.
* Object storage strategy is defined.
* Real-time communication strategy is defined.
* Push notification architecture is defined.
* Personalization architecture is defined.
* API organization is defined.
* Deployment principles are defined.
* Security baseline is defined.
* Testing strategy is defined.
* Observability baseline is defined.
* Repository structure is defined.
* AI/ML boundaries are defined.
* Infrastructure non-goals are explicit.

This document intentionally defines the **initial architecture**, not every implementation detail.

Detailed database schemas, API contracts, component architecture, deployment configuration, and implementation decisions should be created immediately before the relevant development work.