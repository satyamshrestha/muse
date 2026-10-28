from fastapi import APIRouter

from app.services.routers import (
    auth_router,
    device_router,
    group_router,
    notification_router,
    notification_preference_router,
    personalization_router,
    reminder_router,
    user_interest_router,
    mood_entry_router,
    personal_note_router,
    feature_preference_router,
    group_activity_router,
    group_activity_response_router,
    shared_note_router,
    memory_router,
    memory_media_router,
    plan_router,
    plan_participant_router,
)

api = APIRouter(prefix="/api/v1")

api.include_router(auth_router.router)
api.include_router(personalization_router.router)
api.include_router(group_router.router)
api.include_router(device_router.router)
api.include_router(notification_router.router)
api.include_router(notification_preference_router.router)
api.include_router(reminder_router.router)
api.include_router(user_interest_router.router)
api.include_router(mood_entry_router.router)
api.include_router(personal_note_router.router)
api.include_router(feature_preference_router.router)
api.include_router(group_activity_router.router)
api.include_router(group_activity_response_router.router)
api.include_router(shared_note_router.router)
api.include_router(memory_router.router)
api.include_router(memory_media_router.router)
api.include_router(plan_router.router)
api.include_router(plan_participant_router.router)