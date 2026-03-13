from openai import OpenAI

client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1',
    api_key='ms-86779415-739f-4ae7-bf39-3c0b89167aba', # ModelScope Token
)

response = client.chat.completions.create(
    model='ZhipuAI/GLM-4.7-Flash', # ModelScope Model-Id
    messages=[
        {
            'role': 'system',
            'content': 'You are a helpful assistant.'
        },
        {
            'role': 'user',
            'content': '你好'
        }
    ],
    stream=False
)

print(response.choices[0].message.content)