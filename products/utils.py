from django.http import JsonResponse
from .vector_db import ChromaDBSingleton


def vector_search(query):
    try:
        db = ChromaDBSingleton()
        print(f"Received query: {query}")

        formatted_results = []
        if query:
            results = db.search_similar(query, 3)
            print(f"Search results: {results}")

            if results:
                # Get the inner lists
                ids = results["ids"][0] if results["ids"] else []
                documents = results["documents"][0] if results["documents"] else []
                metadatas = results["metadatas"][0] if results["metadatas"] else []

                # Zip them together for easy iteration
                for id_, doc, metadata in zip(ids, documents, metadatas):
                    formatted_results.append(
                        {
                            "id": id_,
                            "name": metadata["name"],
                            "price": metadata["price"],
                            "image_url": metadata["image_url"],
                            "description": doc,
                        }
                    )

        print(f"Formatted results: {formatted_results}")
        return formatted_results
    except Exception as e:
        print(f"Error in vector search: {str(e)}")
        return None
