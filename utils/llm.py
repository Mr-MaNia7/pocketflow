import os
from openai import OpenAI
from anthropic import Anthropic
import logging
from google import genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def call_llm(prompt, model="gpt-3.5-turbo", provider="openai"):
    """
    Call the specified LLM provider with the given prompt.

    Args:
        prompt (str): The prompt to send to the LLM
        model (str): The model to use (e.g., "gpt-4", "claude-2")
        provider (str): The provider to use ("openai" or "anthropic")

    Returns:
        str: The LLM's response
    """
    logger.info(f"Calling {provider} with model {model}")
    logger.debug(f"Prompt: {prompt}")

    try:
        if provider == "openai":
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content

        elif provider == "anthropic":
            client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
            )
            result = response.content
        elif provider == "google":
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            response = client.models.generate_content(
                model="gemini-2.0-flash", contents=prompt
            )
            result = response.text

        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.debug(f"Response: {result}")
        return result

    except Exception as e:
        logger.error(f"Error calling LLM: {str(e)}")
        raise


if __name__ == "__main__":
    # Test the LLM wrapper
    test_prompt = "What is the capital of France?"
    print(
        call_llm(test_prompt, model="claude-3-5-sonnet-20240620", provider="anthropic")
    )
