"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : ai/ai_service.py

Description :
Phase 8 - the ONLY module in this app that talks to the Gemini API.
Takes a ready-made system/user prompt pair and returns the raw model
text. No prompt construction, no response parsing, no business logic -
that lives in prompt_builder.py and formatter.py so the API call
itself stays swappable/testable in isolation.
=============================================================================
"""

import httpx

from google import genai
from google.genai import errors, types

from ai.config import (
    AI_MAX_TOKENS,
    AI_MODEL,
    AI_REQUEST_TIMEOUT_SECONDS,
    AI_TEMPERATURE,
    GEMINI_API_KEY
)


def _response_schema(
        sections: list[str]
) -> types.Schema:
    """
    Forces Gemini's structured-output mode so the response is
    guaranteed valid JSON matching this exact shape, instead of
    relying only on the system prompt's instructions (which the model
    does not always follow to the letter - unlike Claude, Gemini
    would sometimes add a preamble or wrap the JSON in prose despite
    being told not to). Built from `sections` rather than a fixed
    module-level constant so this one API-call layer serves every
    JSON contract in the app (per-product insight, dataset-wide
    executive summary, ...) without duplicating the call/error-
    handling logic per contract.
    """

    return types.Schema(

        type=types.Type.OBJECT,

        properties={

            key: types.Schema(type=types.Type.STRING)

            for key in sections

        },

        required=sections

    )


class AIService:

    _client = None

    @classmethod
    def _get_client(cls) -> genai.Client:

        if not GEMINI_API_KEY:

            raise ValueError(

                "GEMINI_API_KEY is not set. Copy .env.example to "

                ".env and add your Gemini API key to enable AI "

                "insights."

            )

        if cls._client is None:

            cls._client = genai.Client(

                api_key=GEMINI_API_KEY,

                http_options=types.HttpOptions(

                    timeout=AI_REQUEST_TIMEOUT_SECONDS * 1000

                )

            )

        return cls._client

    @classmethod
    def generate(
            cls,
            system_prompt: str,
            user_prompt: str,
            sections: list[str]
    ) -> str:
        """
        Sends one prompt pair to the model and returns the raw text
        response, constrained to a JSON object with exactly these
        `sections` as required string keys. Raises ValueError with a
        clear, user-facing message on any failure (missing key, auth,
        rate limit, timeout, network) - callers surface this directly,
        consistent with how the rest of the app reports precondition
        failures.
        """

        client = cls._get_client()

        try:

            response = client.models.generate_content(

                model=AI_MODEL,

                contents=user_prompt,

                config=types.GenerateContentConfig(

                    system_instruction=system_prompt,

                    temperature=AI_TEMPERATURE,

                    max_output_tokens=AI_MAX_TOKENS,

                    response_mime_type="application/json",

                    response_schema=_response_schema(sections)

                )

            )

        except errors.ClientError as error:

            raise ValueError(
                AIService._client_error_message(error)
            ) from error

        except errors.ServerError as error:

            raise ValueError(

                f"AI insight failed: the Gemini API had a server-side "

                f"error ({error.code}). Try again in a moment."

            ) from error

        except httpx.TimeoutException as error:

            raise ValueError(

                "AI insight failed: the request timed out. Try again."

            ) from error

        except httpx.TransportError as error:

            raise ValueError(

                "AI insight failed: could not reach the Gemini API. "

                "Check your network connection."

            ) from error

        text = getattr(response, "text", None)

        if not text:

            raise ValueError(

                "AI insight failed: the model returned no text "

                "content."

            )

        return text

    @staticmethod
    def _client_error_message(
            error: "errors.ClientError"
    ) -> str:
        """Maps a Gemini 4xx error to a clear, actionable message."""

        detail = getattr(error, "message", None) or str(error)

        if error.code in (401, 403):

            return (

                f"AI insight failed: the Gemini API key was rejected "

                f"({error.code}). Check GEMINI_API_KEY in your .env "

                f"file. Detail: {detail}"

            )

        if error.code == 429:

            return (

                "AI insight failed: rate limit or free-tier quota "

                "reached. Try again in a moment."

            )

        return (

            f"AI insight failed: the Gemini API returned an error "

            f"({error.code}): {detail}"

        )
