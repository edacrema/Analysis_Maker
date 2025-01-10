import os
from dotenv import load_dotenv
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
client = genai.Client(api_key=GOOGLE_API_KEY)
model_id = "gemini-2.0-flash-exp"

def is_overloaded_error(exception):
    """Check if the error is due to model overload"""
    return isinstance(exception, Exception) and "503 UNAVAILABLE" in str(exception)

@retry(
    retry=retry_if_exception_type((Exception,)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    reraise=True
)
def news_search(query):
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=query,
            config=GenerateContentConfig(
                response_modalities=["TEXT"],
            ))
        return response.text
    except Exception as e:
        if is_overloaded_error(e):
            print(f"Model overloaded, retrying... Error: {e}")
            raise  # This will trigger a retry
        else:
            print(f"Unexpected error: {e}")
            return f"Error occurred during search: {str(e)}"