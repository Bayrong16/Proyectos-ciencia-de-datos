from app.config import client


def translate_text(input_str: str) -> str:
    """
    Traduce un texto del inglés al español usando OpenRouter.
    """

    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b:free",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert translator. "
                    "Translate the user's text from English to Spanish. "
                    "Return only the translated text."
                ),
            },
            {
                "role": "user",
                "content": input_str,
            },
        ],
    )

    return completion.choices[0].message.content

