from __future__ import annotations

from app.main import app
from app.routers import admin as admin_router


class StubRemnawave:
    async def ping(self):
        return {"uptime": "ok"}

    async def get_users_by_telegram_id(self, telegram_id: int):
        return [
            {
                "uuid": "11111111-1111-1111-1111-111111111111",
                "shortUuid": "11111111",
                "username": f"tg{telegram_id}",
                "telegramId": telegram_id,
                "status": "ACTIVE",
                "trafficLimitBytes": 100 * 1024**3,
                "usedTrafficBytes": 10 * 1024**3,
                "expireAt": "2099-01-01T00:00:00Z",
                "hwidDeviceLimit": 3,
                "subscriptionUrl": "https://sub.example/11111111",
            }
        ]

    async def get_hwid_count(self, uuid: str):
        return 2


async def test_admin_remnawave_status(client):
    app.dependency_overrides[admin_router._client] = lambda: StubRemnawave()

    resp = await client.get("/api/admin/remnawave/status")

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["stats"] == {"uptime": "ok"}


async def test_admin_remnawave_lookup_by_telegram_id(client):
    app.dependency_overrides[admin_router._client] = lambda: StubRemnawave()

    resp = await client.get("/api/admin/remnawave/users/by-telegram-id/12345")

    assert resp.status_code == 200
    body = resp.json()
    assert body["telegram_id"] == 12345
    assert body["count"] == 1
    assert body["subscriptions"][0]["uuid"] == "11111111-1111-1111-1111-111111111111"
    assert body["subscriptions"][0]["devices_used"] == 2
