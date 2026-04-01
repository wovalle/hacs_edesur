"""Edesur API client."""

from __future__ import annotations

import logging
from datetime import datetime
from urllib.parse import urlencode

import aiohttp

from .const import DATA_URL, HASH_URL, TOKEN_URL

_LOGGER = logging.getLogger(__name__)


class EdesurApiError(Exception):
    """Edesur API error."""


class EdesurAuthError(EdesurApiError):
    """Authentication error."""


class EdesurApi:
    """Client for the Edesur API."""

    def __init__(self, username: str, password: str, nic: str) -> None:
        self._username = username
        self._password = password
        self._nic = nic

    async def authenticate(self, session: aiohttp.ClientSession) -> str:
        """Authenticate and return bearer token."""
        data = urlencode({
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        })
        async with session.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            if resp.status != 200:
                raise EdesurAuthError(f"Authentication failed: {resp.status}")
            result = await resp.json()
            if "access_token" not in result:
                raise EdesurAuthError("No access token in response")
            return result["access_token"]

    async def get_consumption(self, session: aiohttp.ClientSession) -> dict:
        """Fetch consumption data. Returns parsed data dict."""
        token = await self.authenticate(session)

        today = datetime.now().strftime("%d/%m/%Y")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Origin": "https://ov.edesur.com.do",
        }
        async with session.get(
            f"{HASH_URL}?FechaReporte={today}&NIC={self._nic}",
            headers=headers,
        ) as resp:
            if resp.status != 200:
                raise EdesurApiError(f"Failed to get hash: {resp.status}")
            hash_resp = await resp.json()
            hash_val = hash_resp.get("message", "")

        if not hash_val:
            raise EdesurApiError("Empty hash returned")

        async with session.get(
            f"{DATA_URL}?hash={hash_val}",
            headers={
                "Accept": "application/json",
                "Origin": "https://ov.edesur.com.do",
            },
        ) as resp:
            if resp.status != 200:
                raise EdesurApiError(f"Failed to get consumption: {resp.status}")
            data = await resp.json()

        obj = data.get("object")
        if not obj:
            raise EdesurApiError("No data in response")

        return self._parse(obj)

    def _parse(self, obj: dict) -> dict:
        """Parse API response into sensor-friendly dict."""
        daily = obj.get("historicoConsumoDiario", [])
        monthly = obj.get("historicoConsumoMensual", [])
        habits = obj.get("habitosConsumo", {})

        today_str = datetime.now().strftime("%Y-%m-%d")
        today_kwh = 0.0
        yesterday_kwh = 0.0
        month_total = sum(d.get("consumo", 0) for d in daily)

        for i, d in enumerate(daily):
            if d.get("fecha", "")[:10] == today_str:
                today_kwh = d.get("consumo", 0)
                if i > 0:
                    yesterday_kwh = daily[i - 1].get("consumo", 0)
                break

        last_day = daily[-1] if daily else {}

        # Last entry in monthly is the current (in-progress) billing cycle,
        # second-to-last is the last completed bill.
        current_bill = monthly[-1] if monthly else {}
        last_bill = monthly[-2] if len(monthly) >= 2 else {}

        daily_history = [
            {"date": d["fecha"][:10], "kwh": d.get("consumo", 0)}
            for d in daily
            if d.get("fecha")
        ]

        return {
            "today_kwh": today_kwh,
            "yesterday_kwh": yesterday_kwh,
            "last_day_kwh": last_day.get("consumo", 0),
            "last_day_date": last_day.get("fecha", "")[:10] if last_day.get("fecha") else "",
            "month_total_kwh": month_total,
            "daily_avg_kwh": habits.get("promedioGeneral", 0),
            "weekday_avg_kwh": habits.get("promedioDiasSemana", 0),
            "weekend_avg_kwh": habits.get("promedioFinSemana", 0),
            "current_bill_kwh": current_bill.get("consumo", 0),
            "current_bill_amount": current_bill.get("importe", 0),
            "last_bill_kwh": last_bill.get("consumo", 0),
            "last_bill_amount": last_bill.get("importe", 0),
            "daily_history": daily_history,
        }
