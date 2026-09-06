# API Contract

**Project:** MUSE
**Document:** API Contract
**Status:** Initial Specification
**Version:** 0.1
**Related Documents:** `PRODUCT_SPEC.md`, `UX_ARCHITECTURE.md`, `PERSONALIZATION.md`, `TECHNICAL_ARCHITECTURE.md`, `DATABASE_SCHEMA.md`

---

# 1. Purpose

This document defines the initial API contract between the MUSE mobile application and backend.

The API should provide:

* Authentication
* Account onboarding
* Personalization
* Home data
* Discovery
* Daily Drops
* Mood experiences
* Friend-group interaction
* Memories
* Life tools
* Notifications
* Profile/settings

The API is designed around the principle that the mobile client should primarily consume **experience-oriented data**, while the backend owns business logic, authorization, personalization, and persistence.

---

# 2. API Principles

## 2.1 Backend Owns Business Logic

The mobile application should not independently implement important business rules.

The backend owns:

* Authorization
* Personalization
* Recommendation selection
* Daily Drop generation
* Invitation-code validation
* Group membership
* Data ownership
* Notification decisions

The mobile app is responsible primarily for presentation and user interaction.

---

# 3. Base URL

The API will use a versioned base path:

```text
/api/v1
```

Production:

```text
https://<production-domain>/api/v1
```

Development may use a local backend URL.

The mobile application must obtain its API base URL through environment/configuration rather than hardcoding it throughout the codebase.

---

# 4. Authentication

Authentication uses JWT access tokens.

The typical flow is:

```text
Login
  ↓
Access token
  ↓
Authenticated API requests
  ↓
Access token expires
  ↓
Refresh token
  ↓
New access token
```

Authenticated requests use:

```http
Authorization: Bearer <access_token>
```

---

# 5. Standard Response Principles

Successful responses should use JSON.

Example:

```json
{
  "data": {},
  "meta": {}
}
```

The exact wrapper should remain consistent across the API.

For simple endpoints, returning the resource directly is acceptable if consistency is maintained.

The API should not expose internal database implementation details unnecessarily.

---

# 6. Error Contract

Errors should follow one predictable structure.

Example:

```json
{
  "error": {
    "code": "INVALID_INVITATION_CODE",
    "message": "The invitation code is invalid or has already been used."
  }
}
```

Possible error codes:

```text
VALIDATION_ERROR
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
CONFLICT
RATE_LIMITED
INVALID_INVITATION_CODE
INVITATION_CODE_EXPIRED
EMAIL_ALREADY_EXISTS
INVALID_CREDENTIALS
RESOURCE_DELETED
INTERNAL_ERROR
```

The mobile application should rely primarily on `code`, not string-matching arbitrary messages.

---

# 7. Authentication Endpoints

## POST `/auth/claim`

Claims an invitation code and begins account creation.

Request:

```json
{
  "code": "AARYA12"
}
```

Response:

```json
{
  "data": {
    "claim_id": "uuid",
    "configuration": {
      "display_name": null,
      "interests": [],
      "feature_preferences": {}
    }
  }
}
```

The claim process should not expose private information about the predefined configuration.

---

## POST `/auth/register`

Creates an account.

Request:

```json
{
  "claim_id": "uuid",
  "email": "user@example.com",
  "password": "password",
  "display_name": "Aarya"
}
```

Response:

```json
{
  "data": {
    "user": {},
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer"
  }
}
```

For normal public onboarding, `claim_id` may be omitted.

---

## POST `/auth/login`

Request:

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Response:

```json
{
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer"
  }
}
```

---

## POST `/auth/refresh`

Request:

```json
{
  "refresh_token": "..."
}
```

Response:

```json
{
  "data": {
    "access_token": "...",
    "token_type": "bearer"
  }
}
```

---

## POST `/auth/logout`

Invalidates the relevant session/refresh token where server-side session invalidation is implemented.

Response:

```json
{
  "data": {
    "success": true
  }
}
```

---

## GET `/auth/me`

Returns the currently authenticated user.

Response:

```json
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "Aarya",
    "avatar": null
  }
}
```

---

# 8. Onboarding

## GET `/onboarding`

Returns the user's current onboarding state.

Response:

```json
{
  "data": {
    "completed": false,
    "step": "interests"
  }
}
```

---

## PUT `/onboarding/interests`

Request:

```json
{
  "interests": [
    "movies",
    "music",
    "psychology",
    "travel"
  ]
}
```

Response:

```json
{
  "data": {
    "interests": [
      "movies",
      "music",
      "psychology",
      "travel"
    ]
  }
}
```

---

## PUT `/onboarding/preferences`

Request:

```json
{
  "features": {
    "discover": 5,
    "memories": 4,
    "life": 3,
    "room": 5
  },
  "chaos_level": 8,
  "notification_style": "playful"
}
```

Response:

```json
{
  "data": {
    "saved": true
  }
}
```

---

## POST `/onboarding/complete`

Marks onboarding as complete.

Response:

```json
{
  "data": {
    "completed": true
  }
}
```

---

# 9. Personalization

## GET `/personalization`

Returns the user's current personalization configuration.

Response:

```json
{
  "data": {
    "interests": [],
    "feature_preferences": {},
    "personality": {},
    "notification_preferences": {}
  }
}
```

---

## PATCH `/personalization`

Updates user-controlled preferences.

Request:

```json
{
  "interests": ["music", "books"],
  "chaos_level": 4
}
```

Response:

```json
{
  "data": {
    "updated": true
  }
}
```

The user owns this configuration.

Behavioral learning must not silently remove explicit user preferences.

---

## POST `/personalization/reset`

Resets learned personalization signals without necessarily deleting explicit user preferences.

Response:

```json
{
  "data": {
    "reset": true
  }
}
```

---

# 10. Home

## GET `/home`

Returns the primary personalized home experience.

Response:

```json
{
  "data": {
    "greeting": {},
    "daily_drop": {},
    "mood_prompt": {},
    "waiting": [],
    "recent_memories": [],
    "room_activity": [],
    "recommended": [],
    "quick_actions": []
  }
}
```

The backend determines what should be surfaced.

The mobile app should not need to understand the recommendation algorithm.

---

# 11. Daily Drop

## GET `/daily-drop`

Returns the user's Daily Drop for the current day.

Response:

```json
{
  "data": {
    "id": "uuid",
    "type": "song",
    "content": {},
    "reason": "Something that matches your current vibe.",
    "opened": false
  }
}
```

If no Drop exists, the backend may generate one.

---

## POST `/daily-drop/{id}/open`

Marks the Daily Drop as opened.

Response:

```json
{
  "data": {
    "opened": true
  }
}
```

---

## POST `/daily-drop/{id}/feedback`

Request:

```json
{
  "action": "like"
}
```

Possible actions:

```text
LIKE
SAVE
SKIP
NOT_INTERESTED
MORE_LIKE_THIS
```

Response:

```json
{
  "data": {
    "recorded": true
  }
}
```

---

# 12. Discover

## GET `/discover`

Returns personalized discovery content.

Query parameters may include:

```text
type
mood
limit
cursor
```

Example:

```text
GET /discover?type=music&limit=10
```

Response:

```json
{
  "data": {
    "items": [
      {
        "id": "uuid",
        "type": "music",
        "title": "...",
        "description": "...",
        "metadata": {}
      }
    ],
    "next_cursor": null
  }
}
```

Discover should not behave like an infinite social feed.

The backend should provide deliberate selections.

---

## POST `/discover/{id}/feedback`

Records user feedback.

Request:

```json
{
  "action": "save"
}
```

---

# 13. Mood

## POST `/mood`

Records the user's current mood.

Request:

```json
{
  "mood": "tired",
  "energy": 2
}
```

Response:

```json
{
  "data": {
    "mood_session_id": "uuid"
  }
}
```

---

## GET `/mood/world`

Generates the current personalized Mood → World experience.

Response:

```json
{
  "data": {
    "mood": "tired",
    "energy": 2,
    "items": [
      {
        "type": "song",
        "content": {}
      },
      {
        "type": "movie",
        "content": {}
      },
      {
        "type": "question",
        "content": {}
      },
      {
        "type": "random",
        "content": {}
      }
    ]
  }
}
```

---

# 14. Friend Groups

## GET `/groups`

Returns groups the current user belongs to.

Response:

```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Our Room",
      "member_count": 3
    }
  ]
}
```

---

## GET `/groups/{group_id}`

Returns group information.

Response:

```json
{
  "data": {
    "id": "uuid",
    "name": "Our Room",
    "members": []
  }
}
```

Membership must be verified before returning group data.

---

# 15. Room

## GET `/groups/{group_id}/room/messages`

Returns messages.

Query parameters:

```text
limit
cursor
```

Response:

```json
{
  "data": {
    "messages": [],
    "next_cursor": null
  }
}
```

Pagination should use cursor-based pagination rather than large offset queries.

---

## POST `/groups/{group_id}/room/messages`

Request:

```json
{
  "content": "What are we watching tonight?"
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "content": "What are we watching tonight?",
    "sender": {},
    "created_at": "..."
  }
}
```

---

# 16. Room Realtime API

WebSocket:

```text
/ws/v1/groups/{group_id}/room
```

The WebSocket connection requires authentication.

Events may include:

```text
message.created
message.updated
message.deleted
reaction.created
activity.created
activity.updated
```

Example event:

```json
{
  "type": "message.created",
  "data": {
    "id": "uuid",
    "content": "Look at this 😂"
  }
}
```

REST remains the source of truth.

WebSockets provide realtime delivery.

---

# 17. Room Activities

## GET `/groups/{group_id}/activities`

Returns active and recent activities.

---

## POST `/groups/{group_id}/activities`

Request:

```json
{
  "type": "poll",
  "title": "What should we watch?",
  "payload": {
    "options": [
      "Movie A",
      "Movie B",
      "Movie C"
    ]
  }
}
```

---

## POST `/activities/{activity_id}/responses`

Request:

```json
{
  "response": "Movie B"
}
```

---

# 18. Memories

## GET `/groups/{group_id}/memories`

Query parameters:

```text
limit
cursor
date
```

Response:

```json
{
  "data": {
    "items": [],
    "next_cursor": null
  }
}
```

---

## POST `/groups/{group_id}/memories`

Request:

```json
{
  "title": "That random trip",
  "description": "..."
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "title": "That random trip"
  }
}
```

---

## POST `/memories/{memory_id}/media`

Uploads or registers media associated with a memory.

The actual upload mechanism may use a signed object-storage URL.

---

## GET `/memories/{memory_id}`

Returns a complete memory.

---

## DELETE `/memories/{memory_id}`

Deletes or soft-deletes the memory according to the deletion policy.

---

# 19. Media Upload

Large media files should not necessarily pass directly through the FastAPI server.

Preferred flow:

```text
Mobile
  ↓
Request upload URL
  ↓
FastAPI
  ↓
Signed object-storage URL
  ↓
Mobile uploads directly
  ↓
FastAPI confirms/registers media
```

Endpoint:

```text
POST /media/upload-url
```

Request:

```json
{
  "filename": "photo.jpg",
  "content_type": "image/jpeg"
}
```

Response:

```json
{
  "data": {
    "upload_url": "...",
    "media_id": "uuid"
  }
}
```

This keeps the backend from becoming an unnecessary file-transfer bottleneck.

---

# 20. Life

Life contains:

* Plans
* Reminders
* Notes

These remain separate resources even though they share the same application section.

---

# 21. Notes

## GET `/notes`

Returns the authenticated user's notes.

---

## POST `/notes`

Request:

```json
{
  "title": "Things to remember",
  "content": "..."
}
```

---

## PATCH `/notes/{note_id}`

Updates a note.

---

## DELETE `/notes/{note_id}`

Deletes a note.

---

# 22. Reminders

## GET `/reminders`

Returns reminders.

Query parameters may include:

```text
status
from
to
```

---

## POST `/reminders`

Request:

```json
{
  "title": "Call Aarya",
  "remind_at": "2026-09-10T18:00:00Z"
}
```

---

## PATCH `/reminders/{reminder_id}`

Updates a reminder.

---

## POST `/reminders/{reminder_id}/complete`

Marks a reminder complete.

---

## DELETE `/reminders/{reminder_id}`

Deletes a reminder.

---

# 23. Plans

## GET `/plans`

Returns personal and relevant shared plans.

---

## POST `/plans`

Request:

```json
{
  "title": "Movie night",
  "description": "Watch something together",
  "starts_at": "...",
  "ends_at": "...",
  "group_id": "uuid"
}
```

---

## GET `/plans/{plan_id}`

Returns plan details.

---

## PATCH `/plans/{plan_id}`

Updates the plan.

---

## POST `/plans/{plan_id}/respond`

Request:

```json
{
  "status": "accepted"
}
```

---

# 24. Notifications

## GET `/notifications`

Returns notification history.

Query parameters:

```text
unread
limit
cursor
```

---

## POST `/notifications/{notification_id}/read`

Marks a notification as read.

---

## GET `/notifications/preferences`

Returns notification preferences.

---

## PATCH `/notifications/preferences`

Updates notification preferences.

Request:

```json
{
  "daily_drop": true,
  "room": true,
  "memories": true,
  "reminders": true,
  "playful": false
}
```

---

# 25. Device Registration

## POST `/devices`

Registers a device for push notifications.

Request:

```json
{
  "push_token": "...",
  "platform": "ios",
  "app_version": "1.0.0"
}
```

---

## DELETE `/devices/{device_id}`

Removes a device registration.

---

# 26. Profile

## GET `/profile`

Returns the user's profile.

---

## PATCH `/profile`

Updates profile information.

Request:

```json
{
  "display_name": "Satyam"
}
```

---

## DELETE `/profile`

Initiates account deletion.

Account deletion should follow the data-deletion policy defined by the backend.

---

# 27. Authorization

Every authenticated endpoint must determine:

1. Who is making the request?
2. Does the user own the resource?
3. If it is group-owned, is the user a member?
4. Does the user's role permit the operation?

Example:

```text
GET /groups/123/room/messages

        ↓

Authenticate user

        ↓

Find group

        ↓

Verify GroupMembership

        ↓

Return messages
```

The API must never trust a `user_id` supplied by the client to determine ownership.

The authenticated identity comes from the JWT.

---

# 28. Pagination

Collection endpoints should support pagination.

Preferred format:

```text
limit
cursor
```

Example:

```text
GET /groups/{id}/room/messages?limit=30&cursor=abc123
```

Response:

```json
{
  "data": {
    "items": [],
    "next_cursor": "xyz456"
  }
}
```

This is especially important for:

* Messages
* Memories
* Notifications
* Recommendations
* Discover results

---

# 29. API Versioning

The initial API uses:

```text
/api/v1
```

Breaking API changes should result in a new version rather than silently changing the contract.

Non-breaking additions can remain within the same version.

---

# 30. Idempotency

Operations that may be retried by the client should be designed carefully.

Examples:

* Creating memories
* Creating plans
* Registering devices
* Recording Daily Drop interactions

Where duplicate requests could cause meaningful problems, idempotency keys should be considered.

---

# 31. Rate Limiting

Rate limiting should protect endpoints that are expensive or abuse-sensitive.

Initial candidates:

* Login
* Registration
* Invitation claiming
* Recommendation generation
* AI/external-provider calls
* Media upload URL generation

Normal read operations should not be aggressively limited for a small private deployment.

---

# 32. External Content

MUSE may consume external sources for:

* Music
* Movies
* Books
* Places
* Facts
* Other discovery content

The mobile app should not directly depend on external APIs when doing so would expose credentials or duplicate backend business logic.

Preferred flow:

```text
Mobile
  ↓
MUSE API
  ↓
Content provider
  ↓
MUSE normalization
  ↓
Mobile
```

The backend returns a normalized content structure.

---

# 33. API Data Ownership

The API should distinguish between:

### User-generated data

Examples:

* Messages
* Memories
* Notes
* Plans
* Preferences

### System-generated data

Examples:

* Recommendations
* Daily Drops
* Notifications
* Personalization signals

### External data

Examples:

* Movie metadata
* Music metadata
* Book metadata

This distinction becomes important for deletion, caching, and privacy.

---

# 34. API Security Requirements

The API must:

* Use HTTPS in production.
* Hash passwords securely.
* Validate all incoming data.
* Authenticate protected requests.
* Authorize resource access.
* Avoid exposing internal errors.
* Avoid logging passwords/tokens.
* Validate uploaded media metadata.
* Protect invitation-code endpoints against brute force.
* Rate-limit sensitive endpoints.
* Keep secrets in environment/configuration management.

---

# 35. Mobile Client Expectations

The mobile application should have:

* A single API client layer.
* Typed request/response models.
* Centralized authentication handling.
* Automatic access-token refresh.
* Standard error handling.
* Network timeout handling.
* Offline-aware UI where appropriate.

Feature screens should not independently construct raw HTTP requests.

---

# 36. Initial Endpoint Map

```text
AUTH
POST   /auth/claim
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
POST   /auth/logout
GET    /auth/me

ONBOARDING
GET    /onboarding
PUT    /onboarding/interests
PUT    /onboarding/preferences
POST   /onboarding/complete

PERSONALIZATION
GET    /personalization
PATCH  /personalization
POST   /personalization/reset

HOME
GET    /home

DAILY DROP
GET    /daily-drop
POST   /daily-drop/{id}/open
POST   /daily-drop/{id}/feedback

DISCOVER
GET    /discover
POST   /discover/{id}/feedback

MOOD
POST   /mood
GET    /mood/world

GROUPS
GET    /groups
GET    /groups/{id}

ROOM
GET    /groups/{id}/room/messages
POST   /groups/{id}/room/messages
WS     /ws/v1/groups/{id}/room

ACTIVITIES
GET    /groups/{id}/activities
POST   /groups/{id}/activities
POST   /activities/{id}/responses

MEMORIES
GET    /groups/{id}/memories
POST   /groups/{id}/memories
GET    /memories/{id}
POST   /memories/{id}/media
DELETE /memories/{id}

MEDIA
POST   /media/upload-url

NOTES
GET    /notes
POST   /notes
PATCH  /notes/{id}
DELETE /notes/{id}

REMINDERS
GET    /reminders
POST   /reminders
PATCH  /reminders/{id}
POST   /reminders/{id}/complete
DELETE /reminders/{id}

PLANS
GET    /plans
POST   /plans
GET    /plans/{id}
PATCH  /plans/{id}
POST   /plans/{id}/respond

NOTIFICATIONS
GET    /notifications
POST   /notifications/{id}/read
GET    /notifications/preferences
PATCH  /notifications/preferences

DEVICES
POST   /devices
DELETE /devices/{id}

PROFILE
GET    /profile
PATCH  /profile
DELETE /profile
```

---

# 37. V1 API Priority

Not every endpoint needs to be implemented immediately.

### Milestone 1 — Authentication

```text
/auth/*
```

### Milestone 2 — Onboarding & Personalization

```text
/onboarding/*
/personalization/*
```

### Milestone 3 — Core Home

```text
/home
/daily-drop/*
/discover/*
/mood/*
```

### Milestone 4 — Social

```text
/groups/*
/room/*
/activities/*
```

### Milestone 5 — Memories

```text
/memories/*
/media/*
```

### Milestone 6 — Life

```text
/notes/*
/reminders/*
/plans/*
```

### Milestone 7 — Notifications & Devices

```text
/notifications/*
/devices/*
```

---

# 38. Non-Goals

The initial API will not include:

* Public social profiles
* Followers/following
* Public feeds
* Advertising APIs
* Payments
* Complex admin dashboards
* Microservice-to-microservice APIs
* GraphQL
* Public developer APIs

REST + WebSockets are sufficient for the initial product.

---

# 39. Definition of Done

The API contract is considered ready for implementation when:

* Authentication flows are defined.
* Invitation claiming is defined.
* Onboarding is defined.
* Personalization is defined.
* Home data is defined.
* Daily Drop is defined.
* Discover is defined.
* Mood → World is defined.
* Groups and Room are defined.
* Realtime communication is defined.
* Memories and media are defined.
* Life tools are defined.
* Notifications are defined.
* Authorization boundaries are explicit.
* Error structure is standardized.
* Pagination strategy is defined.
* API versioning is defined.
* Security requirements are documented.
* Implementation priority is established.

The contract may evolve during implementation, but changes should be deliberate and reflected in this document.