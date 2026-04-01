"""Data update coordinator for Edesur."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EdesurApi, EdesurApiError, EdesurAuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=6)


class EdesurCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator to fetch Edesur consumption data."""

    def __init__(self, hass: HomeAssistant, api: EdesurApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                return await self.api.get_consumption(session)
        except EdesurAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except EdesurApiError as err:
            raise UpdateFailed(f"API error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
