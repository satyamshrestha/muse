from app.db.redis import redis_client


def revoke_refresh_token(token: str, expires_in: int) -> None:
    redis_client.setex(
        f"revoked_refresh:{token}",
        expires_in,
        "1",
    )


def is_refresh_token_revoked(token: str) -> bool:
    return redis_client.exists(
        f"revoked_refresh:{token}"
    ) == 1