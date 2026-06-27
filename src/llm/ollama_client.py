import ollama

class OllamaClient:

    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        response = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.2,
                "num_predict": 1024,
            }
        )
        return response["message"]["content"]