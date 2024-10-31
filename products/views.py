from django.shortcuts import render, get_object_or_404
from .models import Product
from .utils import vector_search
from .vector_db import ChromaDBSingleton
from django.http import JsonResponse
from .ai_model import GeminiClient

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
        topic = ai.identify_topic(query=message)
        relevant_passage = vector_search(topic)
        chat_reply = ai.get_sales_chat_reply(message, relevant_passage)
        processed_response = f"Received your message: {chat_reply}"

        return JsonResponse({"status": "success", "response": processed_response})

    return render(
        request,
        "products/product_chat.html",
        {"messages": []},
    )
