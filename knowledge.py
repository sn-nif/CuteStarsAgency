# knowledge.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict
import uuid, time, json

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# --- simple in-memory registry (replace with DB/vector store later) ---
DOCS: Dict[str, dict] = {}   # doc_id -> metadata

class DocMeta(BaseModel):
    id: str
    name: str
    language: str           # e.g., "English", "Spanish", etc.
    kind: str               # "pdf" | "json" | "jsonl"
    size: int
    created_at: float

def _flatten_json_bytes(content: bytes) -> str:
    """Flatten JSON/JSONL to plain text for indexing."""
    try:
        text = content.decode("utf-8", errors="ignore")
    except Exception:
        raise HTTPException(400, "Invalid text encoding")
    # JSONL support
    if "\n" in text and text.strip().splitlines()[0].strip().startswith("{"):
        try:
            _ = [json.loads(line) for line in text.splitlines() if line.strip()]
        except Exception:
            pass  # It's okay if it's not pure JSONL; we still index raw text
        return text
    # JSON support
    try:
        data = json.loads(text)
    except Exception:
        # If it isn't valid JSON, still index raw text
        return text

    def walk(x):
        if isinstance(x, dict):
            return "\n".join(f"{k}: {walk(v)}" for k, v in x.items())
        if isinstance(x, list):
            return "\n".join(walk(v) for v in x)
        return str(x)
    return walk(data)

def _extract_pdf_text(_: bytes) -> str:
    """
    Placeholder: you can wire PyMuPDF/pdfminer later.
    Returning a marker string so the endpoint works today.
    """
    return "[PDF TEXT PLACEHOLDER – add real parser later]"

def _index_text(doc_id: str, text: str, language: str):
    """
    TODO: Upsert to your vector DB (Pinecone/Qdrant/etc.).
    For now just sanity-check we have something to index.
    """
    if not text or not text.strip():
        raise HTTPException(400, "No indexable text")

@router.get("/health")
def health():
    return {"ok": True, "service": "knowledge"}

@router.post("/upload")
async def upload(language: str, file: UploadFile = File(...)):
    name = file.filename or "file"
    ext = name.rsplit(".", 1)[-1].lower()
    if ext not in {"pdf", "json", "jsonl"}:
        raise HTTPException(400, "Only .pdf, .json, .jsonl allowed")

    content = await file.read()
    if ext == "pdf":
        text = _extract_pdf_text(content)
    else:
        text = _flatten_json_bytes(content)

    doc_id = str(uuid.uuid4())
    _index_text(doc_id, text, language)

    meta = DocMeta(
        id=doc_id, name=name, language=language,
        kind=ext, size=len(content), created_at=time.time()
    )
    DOCS[doc_id] = meta.model_dict() if hasattr(meta, "model_dict") else meta.dict()
    return {"ok": True, "doc": DOCS[doc_id]}

@router.get("")
def list_docs(language: str | None = None):
    items = list(DOCS.values())
    if language:
        items = [d for d in items if d["language"] == language]
    return {"docs": items}

@router.delete("/{doc_id}")
def delete_doc(doc_id: str):
    if doc_id not in DOCS:
        raise HTTPException(404, "Not found")
    # TODO: also delete from your vector DB using doc_id metadata/namespace.
    del DOCS[doc_id]
    return {"ok": True}