from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import json, uuid, time

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# Store documents in memory for now
DOCS: dict[str, dict] = {}

class DocMeta(BaseModel):
    id: str
    name: str
    language: str
    kind: str      # "pdf" | "json"
    size: int
    created_at: float

# Convert JSON into plain text
def _flatten_json_bytes(content: bytes) -> str:
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    def walk(node):
        if isinstance(node, dict):
            return "\n".join(f"{k}: {walk(v)}" for k, v in node.items())
        if isinstance(node, list):
            return "\n".join(walk(x) for x in node)
        return str(node)
    return walk(data)

# Dummy PDF parser (we can add real one later)
def _extract_pdf_text(content: bytes) -> str:
    return "PDF_TEXT_PLACEHOLDER"

# Stub indexer
def _index_text(doc_id: str, text: str, language: str):
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text to index")

@router.get("/health")
def health():
    return {"ok": True, "service": "knowledge"}

@router.post("/upload")
async def upload(language: str, file: UploadFile = File(...)):
    name = file.filename or "file"
    ext = name.rsplit(".", 1)[-1].lower()
    if ext not in {"pdf", "json"}:
        raise HTTPException(400, detail="Only .pdf or .json allowed")

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
    DOCS[doc_id] = meta.model_dump()
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
        raise HTTPException(404, detail="Not found")
    del DOCS[doc_id]
    return {"ok": True}