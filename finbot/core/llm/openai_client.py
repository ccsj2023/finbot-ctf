"""OpenAI Client with configurable model

TODO: for reasoning capabilities, we need to use Responses API

"""

import json
import logging

from openai import AsyncOpenAI

from finbot.config import settings
from finbot.core.data.models import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI Client with configurable model"""

    def __init__(self):
        self.default_model = settings.LLM_DEFAULT_MODEL
        self.default_temperature = settings.LLM_DEFAULT_TEMPERATURE
        self._client = self._get_client()

    def _get_client(self):
        """Get the OpenAI client"""
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def chat(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Chat with OpenAI
        """
        try:
            model = request.model or self.default_model
            temperature = request.temperature or self.default_temperature
            max_tokens = settings.LLM_MAX_TOKENS
            input_list = request.messages or []
            tool_calls = []

            create_params = {
                "model": model,
                "input": input_list,
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "timeout": settings.LLM_TIMEOUT,
            }

            if request.output_json_schema:
                create_params["text"] = {
                    "format": {
                        "type": "json_schema",
                        "name": request.output_json_schema["name"],
                        "schema": request.output_json_schema["schema"],
                        "strict": True,
                    }
                }

            if request.tools:
                create_params["tools"] = request.tools

            if request.previous_response_id:
                create_params["previous_response_id"] = request.previous_response_id

            response = await self._client.responses.create(**create_params)

            metadata = {
                "response_id": response.id,
            }

            # Extract tool calls and messages for future calls
            # (TODO): take care of refusals
            for item in response.output:
                if item.type == "message":
                    texts = []
                    for content in item.content:
                        if content.type == "output_text":
                            texts.append(content.text)
                    input_list.append(
                        {
                            "role": item.role,
                            "content": "".join(texts),
                        }
                    )
                elif item.type == "function_call":
                    tool_call = {
                        "name": item.name,
                        "call_id": item.call_id,
                        "arguments": json.loads(item.arguments),
                    }
                    tool_calls.append(tool_call)
                    # Add the function call to the conversation history
                    input_list.append(
                        {
                            "type": "function_call",
                            "name": item.name,
                            "call_id": item.call_id,
                            "arguments": item.arguments,
                        }
                    )

            return LLMResponse(
                content=response.output_text,
                provider="openai",
                success=True,
                metadata=metadata,
                messages=input_list,
                tool_calls=tool_calls,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("OpenAI chat failed: %s", e)
            raise Exception(f"OpenAI chat failed: {e}") from e  # pylint: disable=broad-exception-raised
