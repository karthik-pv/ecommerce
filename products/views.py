from django.shortcuts import render, get_object_or_404
from .models import Product
from .utils import vector_search
from .vector_db import ChromaDBSingleton
from django.http import JsonResponse
from .updated_ai_model import GeminiClient

ai = GeminiClient()


def product_list(request):
    products = Product.objects.all()
    return render(request, "products/product_list.html", {"products": products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "products/product_detail.html", {"product": product})


def product_search(request):
    query = request.GET.get("query", "")
    results = vector_search(query)
    return render(
        request,
        "products/product_search.html",
        {"results": results, "query": query},
    )


def product_chat(request):
    if request.method == "POST":
        message = request.POST.get("message", "")
        history = request.POST.get("history", "")
        print(history)
        if history:
            message_with_history = f"Previous Questions for context - {history}\n\nCurrent Question: {message}"
        else:
            message_with_history = message
        print(message_with_history)
        topic = ai.identify_topic(query=message_with_history)
        relevant_passage = vector_search(topic)
        print(relevant_passage)
        image = relevant_passage[0]["image_url"]
        id = relevant_passage[0]["id"]
        chat_reply = ai.get_sales_chat_reply(message, relevant_passage)
        processed_response = f"Received your message: {chat_reply}"
        print(ai.cart)

        return JsonResponse(
            {
                "status": "success",
                "response": processed_response,
                "image": image,
                "idlink": id,
            }
        )

    return render(
        request,
        "products/product_chat.html",
        {"messages": []},
    )
