from app.auth.token_store import (
    revoke_refresh_token,
    is_refresh_token_revoked,
)


def test_refresh_token_revocation():
    token = "test-refresh-token"

    assert not is_refresh_token_revoked(token)

    revoke_refresh_token(
        token,
        expires_in=60,
    )

    assert is_refresh_token_revoked(token)