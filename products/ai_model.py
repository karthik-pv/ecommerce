import os
import threading
import google.generativeai as genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class GeminiClient:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GeminiClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        api_key = ""

        if not api_key:
            raise ValueError(
                "Gemini API key not found in settings or environment variables"
            )
        genai.configure(api_key=api_key)

        try:
            self.model = genai.GenerativeModel("gemini-pro")
            self._initialized = True
        except Exception as e:
            logger.error(f"Error initializing Gemini models: {str(e)}")
            raise

    def identify_topic(self, query: str) -> str:
        """
        Identifies the product topic from a given query.
        Args:
            query (str): The input query/sentence to analyze
        Returns:
            str: The identified product topic or None if extraction fails
        """
        try:
            prompt = (
                "From the given sentence identify the topic of discussion. "
                "The topic will mostly always be a product. "
                "Give me the range of products the user is looking for. "
                "For example, if search query is 'how good is samsung m32', "
                "you need to return 'samsung m32'. "
                "In maximum 3 words, just tell me the topic. "
                f"Sentence: '{query}'"
            )

            response = self.model.generate_content(prompt)

            if hasattr(response, "text"):
                return response.text.strip()

            # Fallback for different response structure
            return response._result.candidates[0].content.parts[0].text.strip()

        except Exception as e:
            logger.error(f"Error identifying topic: {str(e)}")
            return None

    def get_sales_chat_reply(self, query: str, relevant_passage: str) -> str:
        prompt = (
            "You are a helpful and informative bot that answers questions using text from the reference passage included below. "
            "Be sure to respond in a complete sentence, being comprehensive, dont include all relevant background information just the bare minimum. "
            "However, you are talking to a non-technical audience, so be sure to break down complicated concepts and "
            "strike a friendly and conversational tone. "
            "If the passage is irrelevant to the answer, you may ignore it. "
            "If the data is not sufficient just return the response text as 'Data Insufficient'....nothing else "
            "The response must be short....around 75-100 words "
            "When you are not talking about the product in particular keep your responses short "
            "Answer the question as if you are a human salesman......end every response with a question to help the user further.....example volunteer extra information.....volunteer to compare the products and provide the best\n\n"
            f"QUESTION: '{query}'\n"
            f"PASSAGE: '{relevant_passage}'\n\n"
            "ANSWER:"
        )

        response = self.model.generate_content(prompt)
        return response._result.candidates[0].content.parts[0].text.strip()
