"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : ai/ai_service.py

Description :
Phase 8 - the ONLY module in this app that talks to the Anthropic API.
Takes a ready-made system/user prompt pair and returns the raw model
text. No prompt construction, no response parsing, no business logic -
that lives in prompt_builder.py and formatter.py so the API call
itself stays swappable/testable in isolation.
=============================================================================
"""

import anthropic

from ai.config import (
    AI_MAX_TOKENS,
    AI_MODEL,
    AI_REQUEST_TIMEOUT_SECONDS,
    AI_TEMPERATURE,
    ANTHROPIC_API_KEY
)


class AIService:

    _client = None

    @classmethod
    def _get_client(cls) -> anthropic.Anthropic:

        if not ANTHROPIC_API_KEY:

            raise ValueError(

                "ANTHROPIC_API_KEY is not set. Copy .env.example to "

                ".env and add your Anthropic API key to enable AI "

                "insights."

            )

        if cls._client is None:

            cls._client = anthropic.Anthropic(

                api_key=ANTHROPIC_API_KEY,

                timeout=AI_REQUEST_TIMEOUT_SECONDS

            )

        return cls._client

    @classmethod
    def generate(
            cls,
            system_prompt: str,
            user_prompt: str
    ) -> str:
        """
        Sends one prompt pair to the model and returns the raw text
        response. Raises ValueError with a clear, user-facing message
        on any failure (missing key, auth, rate limit, timeout,
        network) - callers surface this directly, consistent with how
        the rest of the app reports precondition failures.
        """

        client = cls._get_client()

        try:

            response = client.messages.create(

                model=AI_MODEL,

                max_tokens=AI_MAX_TOKENS,

                temperature=AI_TEMPERATURE,

                system=system_prompt,

                messages=[
                    {"role": "user", "content": user_prompt}
                ]

            )

        except anthropic.AuthenticationError as error:

            raise ValueError(

                "AI insight failed: the Anthropic API key was "

                "rejected. Check ANTHROPIC_API_KEY in your .env file."

            ) from error

        except anthropic.RateLimitError as error:

            raise ValueError(

                "AI insight failed: rate limit reached. Try again in "

                "a moment."

            ) from error

        except anthropic.APITimeoutError as error:

            raise ValueError(

                "AI insight failed: the request timed out. Try again."

            ) from error

        except anthropic.APIConnectionError as error:

            raise ValueError(

                "AI insight failed: could not reach the Anthropic "

                "API. Check your network connection."

            ) from error

        except anthropic.APIStatusError as error:

            raise ValueError(

                f"AI insight failed: the Anthropic API returned an "

                f"error ({error.status_code})."

            ) from error

        text_blocks = [

            block.text

            for block in response.content

            if getattr(block, "type", None) == "text"

        ]

        if not text_blocks:

            raise ValueError(

                "AI insight failed: the model returned no text "

                "content."

            )

        return "".join(text_blocks)
