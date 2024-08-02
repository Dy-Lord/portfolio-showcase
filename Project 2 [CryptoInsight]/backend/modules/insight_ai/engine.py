import json
from openai import OpenAI


class OpenAIEngine:
    def __init__(self, api_key: str, config: dict):
        self.api_key = api_key
        required_keys = ['model', 'context', 'temperature', 'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty']
        assert all([el in config.keys() for el in required_keys]), 'Missed config key'
        self.config = config
        self.engine = OpenAI(api_key=self.api_key)

    def query(self, data: str):
        response = self.engine.chat.completions.create(
            model=self.config['model'],
            messages=[
                {
                    "role": "system",
                    "content": self.config['context']
                },
                {
                    "role": "user",
                    "content": data
                }
            ],
            temperature=self.config['temperature'],
            max_tokens=self.config['max_tokens'],
            top_p=self.config['top_p'],
            frequency_penalty=self.config['frequency_penalty'],
            presence_penalty=self.config['presence_penalty'],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

