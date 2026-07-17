from pydantic import BaseModel


class TranslationRequest(BaseModel):
    input_str: str


class TranslationResponse(BaseModel):
    translated_text: str


# Este bloque solo se ejecuta cuando corres models.py directamente
if __name__ == "__main__":
    request = TranslationRequest(input_str="Hello World")

    print(request)
    print(request.input_str)