"""Contracts for one-time guided setup completion state."""

import asyncio

from custom_components.ezaiot.onboarding import OnboardingState


def test_completion_requires_active_supported_setup(hass) -> None:
    """A prompt is shown only after install, restart, and exact match."""
    state = OnboardingState(hass)
    asyncio.run(state.async_initialize())
    assert asyncio.run(state.async_should_show_completion(False, False, 1)) is False
    assert asyncio.run(state.async_should_show_completion(True, True, 1)) is False
    assert asyncio.run(state.async_should_show_completion(True, False, 0)) is False
    assert asyncio.run(state.async_should_show_completion(True, False, 1)) is True


def test_completion_is_shown_once(hass) -> None:
    """Dismissal survives a fresh state instance."""
    state = OnboardingState(hass)
    asyncio.run(state.async_initialize())
    asyncio.run(state.async_mark_completion_shown())
    reloaded = OnboardingState(hass)
    asyncio.run(reloaded.async_initialize())
    assert asyncio.run(reloaded.async_should_show_completion(True, False, 1)) is False
