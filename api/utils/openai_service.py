import openai

from api.utils.settings import settings


class OpenAIService:
    
    def __init__(self):
        self.client = openai.OpenAI(
            base_url='https://openrouter.ai/api/v1',
            api_key=settings.OPENROUTER_API_KEY
        )
    
    
    def prompt_ai(
        self,
        prompt: str, 
        system_role_desc: str = "You are a very helpful assistant.",
        model: str = 'openai/gpt-4o-mini',
        max_tokens: int = 15000
    ):
        """THis function is used to prompt openai and get an answer

        Args:
            prompt (str): Text prompt to be sent to open ai
            system_role_desc (int, optional): This is the role the AI should take its form as.

        Returns:
            str: The summarized version of the input text
        """

        try:
            response = self.client.chat.completions.create(
                model=model,
                # model="openai/gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_role_desc},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens  # Adjust based on the token limit
            )
            return response.choices[0].message.content
        except Exception as e:
            raise e
        

openai_service = OpenAIService()