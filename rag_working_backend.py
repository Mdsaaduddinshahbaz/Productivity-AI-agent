from flask import Flask,request,jsonify
from flask_cors import CORS
# from socks import sock
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
import re
import os

app=Flask(__name__)
CORS(app)
# sock(app)
# ----------------------
# 1. Initialize model
# ----------------------
model = SentenceTransformer("multi-qa-mpnet-base-dot-v1")  # lightweight embedding model

# ----------------------
# 2. Define long text
# ----------------------
text="""On 3 December 1984, over 500,000 people in the vicinity of the Union Carbide India Limited pesticide plant in Bhopal, Madhya Pradesh, India were exposed to the highly toxic gas methyl isocyanate, in what is considered the world's worst industrial disaster.
 A government affidavit in 2006 stated that the leak caused approximately 558,125 injuries, including 38,478 temporary partial injuries and 3,900 severely and permanently disabling injuries. 
 Estimates vary on the death toll, with the official number of immediate deaths being 2,259. Others estimate that 8,000 died within two weeks of the incident occurring, and another 8,000 or more died from gas-related diseases. 
 In 2008, the Government of Madhya Pradesh paid compensation to the family members of victims killed in the gas release, and to the injured victims"""
api_Key=os.getenv("qdrant_api","localhost")
client=QdrantClient(api_Key)

from qdrant_client.http import models as rest

collection_name = "rag_collection"
@app.route("/store_text",methods=["POST"])
def store_text_qdrant(batch_size: int =100):
    print("query recived on backend")
    data = request.get_json()
    text = data.get("text")
    # print("recived_text",text)  
    cleaned_text = re.sub(r"\[\d+\]", "", text)
    cleaned_text=cleaned_text.lower()
    original_text=text.lower()
    # ----------------------
    # 3. Split into chunks (simple sentence split for demo)
    # ----------------------
    chunks = [c.strip() for c in re.split(r'\.\s+|/sss', cleaned_text) if c.strip()]
    original_chunked_text=[c.strip() for c in re.split(r'\.\s+|/sss', original_text) if c.strip()]
    print(original_chunked_text)
    # ----------------------
    # 4. Create embeddings
    # ----------------------
    embeddings = model.encode(chunks, convert_to_numpy=True)
    print(len(embeddings))
    # ----------------------
    # 5. Store in qdrant
    # ----------------------
    

    try:
        client.get_collection(collection_name)
        # If collection exists, delete it
        client.delete_collection(collection_name)
    except UnexpectedResponse:
        # Collection doesn't exist, safe to ignore
        pass
    # Create collection (if not already exists)
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=rest.VectorParams(size=768, distance=rest.Distance.COSINE)
    )

    for i in range(0, len(original_chunked_text), batch_size):
        batch_chunks = original_chunked_text[i:i+batch_size]
        batch_embeddings = embeddings[i:i+batch_size]

        client.upsert(
            collection_name=collection_name,
            points=[
                {
                    "id": i + j,
                    "vector": vec,
                    "payload": {"text": chunk}
                }
                for j, (vec, chunk) in enumerate(zip(batch_embeddings, batch_chunks))
            ],
        )

    return jsonify({"chunks_count":len(chunks)})
# ----------------------
# 6. Query
# ----------------------
@app.route("/query",methods=["POST"])
def query_text(limit:int=1):
    print("query called by server in rag")
    data = request.get_json()
    query = data.get("query", "")
    limit=data.get("limit")
    query_embedding = model.encode(query, convert_to_numpy=True).tolist()
    results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=limit
    )
    return jsonify([{"score": r.score, "text": r.payload["text"]} for r in results])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=False)