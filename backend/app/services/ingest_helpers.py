import io
import os
import random
import asyncio
from typing import List, Tuple
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from openai import AsyncOpenAI
import PyPDF2
import docx
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import numpy as np
from numpy.linalg import norm

def detect_language(text: str) -> tuple[str, str]:
    try:
        sample = text[:1000].strip()
        if len(sample) < 50:
            return ('simple', 'pg_catalog.simple')
        d = detect(sample)
        m = {'fr': ('french', 'pg_catalog.french'), 'en': ('english', 'pg_catalog.english'), 'es': ('spanish', 'pg_catalog.spanish'), 'de': ('german', 'pg_catalog.german'), 'it': ('italian', 'pg_catalog.italian'), 'pt': ('portuguese', 'pg_catalog.portuguese')}
        return m.get(d, ('simple', 'pg_catalog.simple'))
    except (LangDetectException, Exception):
        return ('simple', 'pg_catalog.simple')

def split_text(content: str, chunk_size: int=1024, overlap: int=128) -> List[Tuple[str, int, int]]:
    chunks, start, L = ([], 0, len(content))
    if chunk_size <= 0:
        chunk_size = 1024
    if overlap < 0:
        overlap = 0
    while start < L:
        end = min(start + chunk_size, L)
        chunks.append((content[start:end], start, end))
        if end == L:
            return chunks
        start = max(end - overlap, start + 1)
    return chunks

def parse_bytes_by_ext(data: bytes, ext: str) -> str:
    ext = ext.lower()
    if ext in ['.txt', '.md']:
        return data.decode('utf-8', errors='ignore')
    if ext == '.pdf':
        reader = PyPDF2.PdfReader(io.BytesIO(data))
        out = []
        for p in reader.pages:
            t = p.extract_text() or ''
            out.append(t)
        return '\n'.join(out)
    elif ext == '.docx':
        d = docx.Document(io.BytesIO(data))
        return '\n'.join([p.text for p in d.paragraphs])
    else:
        if ext == '.html':
            soup = BeautifulSoup(data.decode('utf-8', errors='ignore'), 'html.parser')
            return soup.get_text(separator='\n', strip=True)
        raise ValueError(f'Format non supporté: {ext}')

async def add_context_to_chunks(chunks: List[Tuple[str, int, int]], document_text: str, model: str = 'google/gemini-2.5-flash', timeout_s: float = 30.0, concurrency: int = 8) -> List[Tuple[str, int, int]]:
    if len(document_text) > 700000:
        document_text = document_text[:700000]

    client = AsyncOpenAI(base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1'), api_key=os.getenv('OPENROUTER_API_KEY'))
    sem = asyncio.Semaphore(max(1, concurrency))

    async def one(c: Tuple[str, int, int]) -> Tuple[str, int, int]:
        chunk_text = c[0]
        messages = [
            {'role': 'system', 'content': 'You are a retrieval assistant. Given a chunk from the user, return a concise 1-4 sentence context label that situates the chunk within the cached document. Be specific, no fluff. YOU MUST USE THE SAME LANGUAGE AS THE DOCUMENT.'},
            {'role': 'user', 'content': f'\n<document>\n{document_text}\n</document>\n<chunk>\n{chunk_text}\n</chunk>\nGive only the succinct context (same language as the document).\nYOU MUST USE THE SAME LANGUAGE AS THE DOCUMENT.'}
        ]
        async with sem:
            r = await asyncio.wait_for(client.chat.completions.create(model=model, messages=messages, temperature=0.75, max_tokens=256), timeout=timeout_s)
        ctx = (r.choices[0].message.content or '').strip()
        return (f'{ctx} {chunk_text}'.strip(), c[1], c[2])

    # Traiter tous les chunks en parallèle
    return await asyncio.gather(*[one(chunk) for chunk in chunks])

def normalize_embedding(embedding: List[float]) -> List[float]:
    embedding_array = np.array(embedding)
    normalized = embedding_array / np.linalg.norm(embedding_array)
    return normalized.tolist()

def embed_texts(batch: List[str], model: str='gemini-embedding-001') -> List[List[float]]:
    if len(batch) == 0 or len(batch) > 100:
        raise ValueError('Batch size must be between 1 and 100')
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    resp = client.models.embed_content(model=model, contents=batch, config=types.EmbedContentConfig(task_type='retrieval_document', output_dimensionality=768))
    embs = [normalize_embedding(d.values) for d in resp.embeddings]
    return embs