# Mobile App UX Architecture

**Project:** MUSE
**Document:** Mobile App UX Architecture
**Status:** Initial Specification
**Version:** 0.1
**Platform:** iOS-first
**Related Document:** `PRODUCT_SPEC.md`

---

# 1. Purpose

This document defines the initial user experience architecture of MUSE.

It describes:

* The application's navigation model
* Major screens
* Screen responsibilities
* Core user flows
* Relationships between features
* Personalization within the interface
* Loading, empty, and error states
* The overall information architecture

This document intentionally focuses on **UX and product structure**, not implementation details.

---

# 2. UX Philosophy

MUSE should feel like a small digital world rather than a collection of disconnected utilities.

The user should be able to enter the application and immediately understand:

1. What is happening.
2. What is waiting for them.
3. What they can explore.
4. What their people are doing.
5. What useful things need attention.

The interface should remain simple even though the application contains many capabilities.

The product should prioritize:

* Personalization
* Discovery
* Context
* Familiarity
* Low friction
* Visual simplicity
* Small moments of surprise

The application should avoid feeling like a dashboard packed with widgets.

---

# 3. Primary Navigation

The initial application will use a small number of primary navigation destinations.

```text
Home
Discover
Room
Memories
Life
More
```

The exact visual navigation treatment may be refined during implementation, but the conceptual information architecture should remain stable.

## Home

The personalized starting point.

## Discover

Explore content and experiences.

## Room

The shared friend-group space.

## Memories

Shared history and resurfaced moments.

## Life

Planning and practical tools.

## More

The complete feature library, account settings, and less frequently used functionality.

---

# 4. Home

Home is the most important screen in the application.

It should answer:

> **"Why should I stay here for a minute?"**

rather than:

> **"Which feature do I want to open?"**

The contents of Home are personalized.

Potential sections include:

```text
Greeting / current context
        ↓
Daily Drop
        ↓
Something for you
        ↓
Room activity
        ↓
Memory
        ↓
Life / things to handle
        ↓
Something unexpected
```

The exact sections shown and their order may vary according to the user's configuration.

---

## 4.1 Personalized Prominence

Home does not disable features.

Instead, it changes what appears first and what receives visual emphasis.

For example:

### User A

Home might prioritize:

* Daily Drop
* Psychology discovery
* Music
* Movies
* Quiz
* Group activity

### User B

Home might prioritize:

* Daily Drop
* Planner
* Reminders
* Notes
* Music
* Mystery discovery

Both users still have access to every feature.

---

## 4.2 Home Should Not Become a Feed

Home should not become an infinite scrolling feed.

Content should be intentionally selected.

The user should feel that the application prepared a small set of things specifically for them.

---

# 5. Onboarding

Onboarding is a core product experience rather than a simple account setup flow.

The user should gradually construct their initial MUSE experience.

```text
Welcome
   ↓
Create account
   ↓
Invitation / claim code (when applicable)
   ↓
Interests
   ↓
What do you want more of?
   ↓
Personality / vibe
   ↓
Feature preferences
   ↓
Notification preferences
   ↓
Personalized experience generated
   ↓
Home
```

For users without a private invitation code, the claim-code step is skipped.

---

# 6. Invitation / Claim Code Flow

Private seeded users can enter a one-time invitation code during account creation.

Example:

```text
Enter invitation code
        ↓
Backend validates code
        ↓
Predefined base configuration identified
        ↓
Account created
        ↓
Base configuration attached
        ↓
Code consumed
        ↓
User continues onboarding
```

The user should never need to remember the code after account creation.

The code is not a login credential.

---

# 7. Interests Selection

The onboarding experience should allow users to select interests.

Potential categories:

* Music
* Movies
* Series
* Books
* Fashion
* Beauty
* Psychology
* Travel
* Food
* Documentaries
* Learning
* Games
* Pop culture
* Lifestyle
* Other relevant categories

The interface should favor visual selection over long forms.

The user should be able to select multiple interests quickly.

---

# 8. Experience Preferences

Users should be able to indicate what they want the application to provide.

Possible choices:

* Discover new things
* Hang out with friends
* Save memories
* Plan things
* Stay organized
* Learn interesting things
* Find entertainment
* Play games
* Get random surprises

These preferences influence Home and recommendations.

They do not restrict access to features.

---

# 9. Personality Configuration

MUSE should learn the user's preferred interaction style.

Possible dimensions include:

```text
Calm ───────── Chaotic
Practical ───────── Playful
Organized ───────── Spontaneous
Minimal ───────── Expressive
```

These settings influence:

* Recommendation selection
* Home presentation
* Copy
* Notification tone
* Surprise frequency
* Suggested activities

These should be treated as preferences rather than permanent personality labels.

Users can change them later.

---

# 10. Notification Configuration

Onboarding may allow users to configure notification preferences.

Possible controls:

* Useful updates
* Friend activity
* Daily Drop
* Reminders
* Recommendations
* Playful notifications
* Quiet hours

Users should have control over notification frequency.

The application should never depend on notifications being enabled for the core experience to function.

---

# 11. Discover

Discover is the primary exploration surface.

The user should be able to start with a simple intent:

> "Give me something."

Then refine it if desired.

Potential entry points:

```text
Music
Movies
Series
Books
Food
Travel
Psychology
Facts
Questions
Games
Activities
Random
```

Discover should support both:

### Directed Discovery

> "Give me a psychological topic."

### Open Discovery

> "Surprise me."

---

# 12. Discovery Result

A discovery result should not simply be a piece of content.

It should provide context and possible actions.

For example:

```text
Recommendation
     ↓
Why this was recommended
     ↓
Save / Like / Skip
     ↓
Share with Room
     ↓
Explore something related
```

User interactions become signals for future personalization.

---

# 13. Daily Drop

Daily Drop has its own dedicated experience but should also appear on Home.

The user opens it and receives one primary personalized experience.

Possible Daily Drops:

* Song
* Movie
* Book
* Fact
* Psychology topic
* Question
* Quiz
* Challenge
* Memory
* Travel idea
* Food recommendation
* Group activity

The experience should feel intentionally selected rather than like a random feed item.

---

# 14. Mood → World

Mood → World begins with a lightweight mood selection.

Example:

```text
How are you feeling?

😌 Calm
😴 Tired
🧠 Curious
😂 Chaotic
❤️ Social
😐 Bored
🔥 Energetic
```

The application then creates a short personalized experience.

Example:

```text
Mood: Bored

Song
    ↓
Interesting fact
    ↓
Movie recommendation
    ↓
Question
    ↓
Optional group activity
    ↓
Unexpected item
```

The generated experience should reflect both:

* Current mood
* Existing user preferences

Mood is temporary context, not a permanent profile attribute.

---

# 15. The Room

The Room is the shared social space.

It should provide more than conventional chat.

Potential structure:

```text
Room
├── Conversation
├── Questions
├── Polls
├── Recommendations
├── Activities
├── Shared media
└── Random
```

Users should be able to move naturally between conversation and activities.

For example:

```text
Movie recommendation
        ↓
Share to Room
        ↓
Friend reacts
        ↓
Poll: "Should we watch it?"
        ↓
Plan created in Life
```

This connection between features is important.

The application should feel like one coherent system.

---

# 16. Room Conversation

The Room may include lightweight messaging.

However, the product should not attempt to become a complete messaging platform.

The emphasis should remain on:

* Shared experiences
* Context
* Reactions
* Recommendations
* Activities
* Group decisions

Existing messaging applications remain appropriate for normal everyday communication.

---

# 17. Memories

Memories provide a dedicated shared archive.

Primary experience:

> **"Remember this?"**

Potential structure:

```text
Memories
├── Recent
├── Timeline
├── Albums
├── Favorites
└── Resurfaced
```

A memory may contain:

* Photos
* Text
* Date
* Location, when intentionally provided
* Participants
* Reactions
* Comments

Location should not be required.

---

# 18. Memory Resurfacing

The application can periodically surface older memories.

Examples:

> "One year ago today."

> "Remember this?"

> "This deserves another look."

Resurfacing should remain occasional.

The system should avoid turning memories into an engagement farming mechanism.

---

# 19. Life

Life contains practical utilities.

Potential sections:

```text
Life
├── Planner
├── Reminders
├── Notes
├── To-do
└── Shared Plans
```

All users can access these features.

Personalization determines whether they are prominent.

---

# 20. Planner

The planner provides lightweight planning rather than attempting to compete with dedicated productivity applications.

Potential capabilities:

* Events
* Dates
* Shared plans
* Simple scheduling
* Group activities

The focus is on things relevant to the friend group.

---

# 21. Reminders

Reminders should support personal and shared reminders.

Examples:

* "Buy tickets."
* "Call Mom."
* "Submit assignment."
* "Bring camera."
* "Movie night tomorrow."

Reminders can optionally be connected to plans or Room activities.

---

# 22. Notes

Notes provide lightweight personal or shared text storage.

Possible types:

* Personal note
* Shared note
* Idea
* List
* Random thought
* Planning note

The feature should remain intentionally simple.

---

# 23. More

More is the complete feature library.

It exists specifically to preserve the principle:

> **Everything is available; personalization determines prominence.**

Potential contents:

* Planner
* Reminders
* Notes
* Games
* Quizzes
* Mystery
* Settings
* Personalization
* Notification settings
* Account
* Other future features

A user should be able to find functionality that does not appear on their personalized Home.

---

# 24. Profile & Personalization Settings

Users should have access to their own configuration.

Potential sections:

```text
Profile
├── Account
├── Interests
├── Experience preferences
├── Personality
├── Notifications
└── Privacy
```

Users can modify their preferences after onboarding.

The application should never assume that the initial onboarding configuration remains accurate forever.

---

# 25. Cross-Feature Connections

Features should not operate as isolated modules.

Important relationships include:

```text
Discover
   ↓
Save
   ↓
Share to Room
   ↓
Group discussion
   ↓
Create Plan
   ↓
Life
   ↓
Memory
```

Another example:

```text
Mood
   ↓
Mood → World
   ↓
Recommendation
   ↓
User reaction
   ↓
Personalization signal
   ↓
Future recommendation
```

And:

```text
Room activity
   ↓
Event / plan
   ↓
Life
   ↓
Completed activity
   ↓
Memory
```

The long-term UX goal is a connected personal world rather than a collection of separate tools.

---

# 26. Loading States

Loading states should be lightweight and visually consistent.

They should communicate that something is happening without making the application feel slow.

Examples:

* Skeleton cards
* Subtle animations
* Contextual loading messages
* Progressive content loading

For personalized experiences, a small personality-driven loading message may occasionally be appropriate.

---

# 27. Empty States

Empty states should be useful and sometimes playful.

Examples:

### Empty Memories

> "Nothing here yet. That's either peaceful or suspicious."

### Empty Notes

> "Your thoughts are currently refusing to be documented."

### Empty Plans

> "No plans yet. Dangerous."

The personality should remain subtle and context-appropriate.

---

# 28. Error States

Errors should be:

* Clear
* Recoverable
* Human-readable
* Non-blaming

Avoid exposing raw technical errors.

For example, instead of:

> `HTTP 500 INTERNAL SERVER ERROR`

the user should see something like:

> "Something went sideways. Try again."

with an appropriate retry action.

Technical details may still be logged internally.

---

# 29. Offline / Poor Connectivity

The application should handle temporary connectivity problems gracefully.

Where possible:

* Previously loaded content should remain available.
* Drafts should not be unnecessarily lost.
* Failed actions should provide retry options.
* The user should understand when an action requires connectivity.

Offline support should be practical rather than attempting to turn MUSE into a fully offline application.

---

# 30. Accessibility

The UI should support standard iOS accessibility expectations.

Initial requirements include:

* Dynamic text sizing where practical
* Sufficient contrast
* Accessible touch targets
* Screen-reader-compatible labels
* Clear interaction states
* Avoiding information conveyed only through color

Accessibility should be considered during implementation rather than added as a final cleanup task.

---

# 31. UX Success Criteria

The initial UX should succeed if a new user can:

1. Create an account.
2. Complete onboarding without confusion.
3. Understand what the application is for.
4. Immediately see personalized content.
5. Discover something interesting.
6. Find the shared Room.
7. Access Memories.
8. Find Life tools even when they are not prominent on Home.
9. Modify their preferences.
10. Understand how the application becomes more personalized over time.

Most importantly:

> **The user should understand why they might want to open MUSE again tomorrow.**

---

# 32. UX Non-Goals

The UX should not become:

* A social-media feed
* A complicated productivity suite
* A full messaging replacement
* An overwhelming dashboard
* A gamified productivity system
* A settings-heavy personalization nightmare

The application should remain approachable despite its breadth.

---

# 33. Definition of Done

This UX architecture is considered complete enough for technical architecture when:

* Primary navigation is defined.
* Major screens are defined.
* Onboarding flow is defined.
* Personalization is reflected in UX.
* The complete feature universe remains accessible.
* Home's purpose is clear.
* Discover is defined.
* Daily Drop is defined.
* Mood → World is defined.
* The Room is defined.
* Memories are defined.
* Life is defined.
* More is defined.
* Cross-feature relationships are documented.
* Loading, empty, and error states have principles.
* Accessibility expectations are documented.
* The UX has clear boundaries against becoming a feed, messaging replacement, or productivity suite.

This document defines **what the user experiences and how the product is organized**.

Technical implementation belongs in `TECHNICAL_ARCHITECTURE.md`.