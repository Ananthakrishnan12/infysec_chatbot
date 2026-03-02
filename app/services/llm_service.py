from groq import Groq
from app.core.config import GROQ_API_KEY
from app.utils.prompts import SYSTEM_PROMPT

client = Groq(api_key=GROQ_API_KEY)

async def generate_response(user_query, context=""):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": context},
            {"role": "user", "content": user_query}
        ],
        temperature=0.3,
    )

    return completion.choices[0].message.content
