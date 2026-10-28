"""Public download of the packaged project deliverables (whitelisted files only; no secrets)."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import PROJECT_ROOT

router = APIRouter(prefix="/api/deliverables", tags=["Deliverables"])
DIST, DOCS = PROJECT_ROOT / "dist", PROJECT_ROOT / "docs"
FILES = {
    "air-gapped-mpls-copilot.zip": DIST / "air-gapped-mpls-copilot.zip",
    "er_diagram_detailed.png": DOCS / "er" / "er_diagram_detailed.png",
    "er_diagram_detailed.pdf": DOCS / "er" / "er_diagram_detailed.pdf",
    "er_diagram_detailed.svg": DOCS / "er" / "er_diagram_detailed.svg",
    "er_diagram_presentation.png": DOCS / "er" / "er_diagram_presentation.png",
    "er_diagram.mmd": DOCS / "er" / "er_diagram.mmd",
    "relational_schema.md": DOCS / "09_relational_schema.md",
    "data_dictionary.md": DOCS / "10_data_dictionary.md",
    "compliance_matrix.pdf": DOCS / "20_compliance_matrix.pdf",
    "testing_results.md": DOCS / "18_testing_results.md",
}


@router.get("")
def list_deliverables():
    return [name for name, path in FILES.items() if path.exists()]


@router.get("/{name}")
def download(name: str):
    path = FILES.get(name)
    if path is None or not path.exists():
        raise HTTPException(404, "Deliverable not found")
    return FileResponse(path, filename=name)
