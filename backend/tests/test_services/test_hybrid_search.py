
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))
import re
from app.services.retriever import Retriever
from app.services.rag_agent import QueryItem

retriever = Retriever(user_id="b46a7229-2c29-4a88-ada1-c21a59f4eda1")

query_item = QueryItem(query="surface habitable", lang="french")

results = retriever.retrieve_from_knowledge_chunks(query_item.query, k=10, type='hybrid', query_lang=query_item.lang)

print(results)

# query = "surface     habitable maison "
# query = " ".join(query.split())
# query = re.sub(r'\s+', ' | ', query)
# print(query)