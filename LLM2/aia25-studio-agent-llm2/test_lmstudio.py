from openai import OpenAI
import httpx

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm_studio",
    http_client=httpx.Client(
        timeout=30.0,
        transport=httpx.HTTPTransport(retries=1)
    )
)

try:
    response = client.chat.completions.create(
        model="llava-llama-3-8b-v1_1-imat",
        messages=[
            {"role": "user", "content": "What is the capital of France?"}
        ]
    )
    print(response.choices[0].message.content)
except Exception as e:
    print("❌ Request failed:", e)