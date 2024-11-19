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
    _chat = None
    cart = []

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
            self.model = genai.GenerativeModel(
                model_name="gemini-pro", tools=[self.add_to_cart, self.check_cart]
            )
            self._initialized = True
        except Exception as e:
            logger.error(f"Error initializing Gemini models: {str(e)}")
            raise

    @property
    def chat(self):
        if self._chat is None:
            self._chat = self.model.start_chat(enable_automatic_function_calling=True)
        return self._chat

    def add_to_cart(self, product_id: int, quantity: int) -> str:
        """Add item to cart using product_id and the quantity."""
        self.cart.append({"product_id": product_id, "quantity": quantity})
        print(f"Cart updated: {self.cart}")
        return "product has been added to cart"

    def check_cart(self) -> str:
        """Check the items in the current cart"""
        print("cart checked" + str(self.cart))
        return str(self.cart)

    def identify_topic(self, query: str) -> str:
        try:
            prompt = (
                "From the given conversation and final question identify the topic of discussion. "
                "The topic will mostly always be a product. "
                "Give me the range of products the user is looking for. "
                "For example, if search query is 'i want to buy shoes', "
                "you need to return 'shoes'. "
                "In maximum 3 words, just tell me the topic. "
                "If the final sentence doesnt have any indication of the topic......look at the previous context and find the topic from that"
                "if there is no prominent topic....just return ''"
                f"Sentence: '{query}'"
            )

            response = self.chat.send_message(prompt)

            if hasattr(response, "text"):
                return response.text.strip()
            return response._result.candidates[0].content.parts[0].text.strip()

        except Exception as e:
            logger.error(f"Error identifying topic: {str(e)}")
            return None

    def get_sales_chat_reply(self, query: str, relevant_passage: str) -> str:
        cart_hot_words = ["cart", "wishlist", "bag"]
        print(query)
        if any(word in query.lower() for word in cart_hot_words):
            prompt = (
                "You need to perform one of the operations on the cart......either adding......removing.......or checking the products in the cart"
                "when you see that you have to add something to the cart make sure to call the add_to_cart function"
                "when you see that you have to get details from the cart make sure to call the check_cart function"
                "you have been provided with the necesary tools for each of the operations"
                "look at the query string and extract the relevant product ids and quantity from the provided Passage...and execute the function using that data"
                "make sure the operations happens on valid data"
                "be very careful while extracting the data from the query"
                "confirm with the user if you aren't sure about which operation to carry out or you arent sure about the data to be added/removed"
                "look at the chat history giving more importance to the latest messages while making decisions as well"
                "it is essential that an operation on cart is carried out when this prompt is called. "
                "request confirmation but always perform an operation."
                f"\n\nQUERY : '{query}' \n\n"
                f"PASSAGE : '{relevant_passage}'\n\n"
            )
        else:
            prompt = (
                "You are a helpful and informative bot that answers questions using text from the reference passage included below. "
                "Be sure to respond in a complete sentence, being comprehensive. "
                "However, you are talking to a non-technical audience, so be sure to break down complicated concepts and "
                "strike a friendly and conversational tone. "
                "If the passage is irrelevant to the answer, you may ignore it. "
                "The response must be short....around 75-100 words "
                "Make sure the answer contains the product details provided in the relevant passage.....it is absolutely essential. "
                "When you are not talking about the product in particular keep your responses short."
                "Make sure to always give details about the product being discussed without fail. This is essential."
                "Answer the question as if you are a human salesman......end every response with a question to help the user further.....example volunteer extra information.....volunteer to compare the products and provide the best\n\n"
                f"\n\nQUERY : '{query}' \n\n"
                f"PASSAGE: '{relevant_passage}'\n\n"
            )

        response = self.chat.send_message(prompt)
        reply = response._result.candidates[0].content.parts[0].text.strip()
        print(self.cart)
        print(reply)
        return reply
