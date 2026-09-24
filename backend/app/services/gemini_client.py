import httpx

from app.core.config import get_settings

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiError(Exception):
    """Base class for any Gemini call failure. Callers should catch the
    most specific subclass they care about, or this base class to catch
    anything."""


class GeminiTimeoutError(GeminiError):
    pass


class GeminiProviderError(GeminiError):
    """Gemini responded with a non-2xx status."""


class GeminiInvalidResponseError(GeminiError):
    """Gemini responded 2xx but with an unexpected/unparseable body shape."""


def generate_content(prompt: str) -> str:
    """Calls the Gemini REST API directly (no SDK dependency — see the
    design note in docs/sdd/15-ai-spec.md) and returns the generated text.

    Never call this directly from a route handler — go through the
    `get_gemini_generate_fn` FastAPI dependency (app/api/deps.py) so tests
    can override it without any network access or real API key."""
    settings = get_settings()
    url = f"{GEMINI_API_BASE}/models/{settings.gemini_model}:generateContent"

    try:
        response = httpx.post(
            url,
            params={"key": settings.gemini_api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=settings.gemini_timeout_seconds,
        )
    except httpx.TimeoutException as exc:
        raise GeminiTimeoutError("Gemini request timed out.") from exc
    except httpx.HTTPError as exc:
        raise GeminiProviderError(f"Gemini request failed: {exc}") from exc

    if response.status_code >= 400:
        raise GeminiProviderError(f"Gemini returned HTTP {response.status_code}.")

    try:
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise GeminiInvalidResponseError("Gemini returned an unexpected response shape.") from exc
