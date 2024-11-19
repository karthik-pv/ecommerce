import google.generativeai as genai

API_KEY = "AIzaSyCadPuPUQvtH-NsETbzmgooO9OT2NkAt1s"

genai.configure(api_key=API_KEY)


def get_favorite_guitar_details() -> str:
    """Returns the details of my favorite guitar"""
    return "les paul"


model = genai.GenerativeModel(
    model_name="gemini-pro", tools=[get_favorite_guitar_details]
)

chat = model.start_chat(enable_automatic_function_calling=True)
response = chat.send_message("which is my favorite guitar")
print(response)
