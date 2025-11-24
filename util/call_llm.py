from openai import OpenAI, AsyncOpenAI
import os
import requests
import asyncio
from typing import Dict, Any, Type
from pydantic import BaseModel
import json

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def call_llm_async(
        system_prompt: str,
        user_content: str,
        ):    
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-api-key"))
    r = await client.chat.completions.create(
        model="gpt-4o",
       messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return r.choices[0].message.content

async def call_llm_json_async(
    system_prompt: str,
    user_content: str,
    response_model: Type[BaseModel],
) -> Dict[str, Any]:
    """Ask the model to return JSON and parse it.

    The prompt should request ONLY JSON. We also try a simple recovery
    if the model wraps JSON in extra text.
    """

    # 1. Generate the JSON schema from the Pydantic model class
    json_schema = response_model.model_json_schema()

    # 2. Call the API using the manual 'json_schema' construction
    response = await _client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__, # Use the class name
                "strict": True,                  # Enforce strict schema adherence
                "schema": json_schema,
            }
        }
    )
    # 3. Extract content
    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to recover by trimming around outer braces
        try:
            first = content.index("{")
            last = content.rindex("}")
            return json.loads(content[first : last + 1])
        except Exception as e:
            raise ValueError(f"LLM did not return valid JSON: {content}") from e