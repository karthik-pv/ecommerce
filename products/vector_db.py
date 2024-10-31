import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
import logging
from .models import Product

logger = logging.getLogger(__name__)


class ChromaDBSingleton:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChromaDBSingleton, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            try:
                # Set up logging
                logger.setLevel(logging.DEBUG)

                # Create persist directory if it doesn't exist
                persist_directory = os.path.join("vector_db")
                os.makedirs(persist_directory, exist_ok=True)

                logger.debug(
                    f"Initializing ChromaDB with directory: {persist_directory}"
                )

                self.client = chromadb.PersistentClient(path=persist_directory)
                self.encoder = SentenceTransformer(
                    "sentence-transformers/all-MiniLM-L6-v2"
                )

                # Get or create collection
                self.collection = self.client.get_or_create_collection(
                    name="products", metadata={"hnsw:space": "cosine"}
                )

                # Get all products
                products = Product.objects.all()
                logger.debug(f"Found {products.count()} products in database")

                if products.exists():
                    self.add_products_to_vectordb(products)
                else:
                    logger.warning("No products found in database")

                self._initialized = True
                logger.info("ChromaDB initialization completed")

            except Exception as e:
                logger.error(f"Error during ChromaDB initialization: {str(e)}")
                raise

    def add_or_update_product(self, product):

        embedding = self.encoder.encode(product.description).tolist()

        document_text = f"{product.name}: {product.description}"

        try:
            self.collection.upsert(
                ids=[str(product.id)],
                embeddings=[embedding],
                documents=[document_text],
                metadatas=[
                    {
                        "name": product.name,
                        "price": str(product.price),
                        "image_url": product.image_url,
                    }
                ],
            )
        except Exception as e:
            print(f"Error adding/updating product to vector DB: {e}")

    def add_products_to_vectordb(self, products):
        """
        Add multiple products to vector database with improved error handling
        """
        try:
            # Get existing product IDs in vector DB
            existing_ids = set(self.collection.get()["ids"])
            logger.debug(f"Found {len(existing_ids)} existing products in vector DB")

            # Prepare lists for batch upload
            ids = []
            embeddings = []
            documents = []
            metadatas = []

            # Process each product
            for product in products:
                try:
                    # Skip if product already exists
                    if str(product.id) in existing_ids:
                        logger.debug(
                            f"Product {product.id} already exists in vector DB"
                        )
                        continue

                    # Create embedding
                    embedding = self.encoder.encode(product.description).tolist()
                    document_text = f"{product.name}: {product.description}"

                    # Add to lists
                    ids.append(str(product.id))
                    embeddings.append(embedding)
                    documents.append(document_text)
                    metadatas.append(
                        {
                            "name": product.name,
                            "price": str(product.price),
                            "image_url": product.image_url or "",
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing product {product.id}: {str(e)}")

            if ids:  # Only proceed if there are new products to add
                # Upload to vector DB
                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                )
                logger.info(f"Successfully added {len(ids)} new products to vector DB")
            else:
                logger.info("No new products to add to vector DB")

        except Exception as e:
            logger.error(f"Error in batch upload to vector DB: {str(e)}")
            raise

    def search_similar(self, query_text, n_results=5):
        """Search for similar products"""
        query_embedding = self.encoder.encode(query_text).tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=n_results
        )

        return results

    def delete_product(self, product_id):
        """Delete a product from the vector database"""
        try:
            self.collection.delete(ids=[str(product_id)])
        except Exception as e:
            print(f"Error deleting product from vector DB: {e}")
