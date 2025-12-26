from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import RagDocument
from typing import List, Optional

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

@router.get("/")
def get_documents(doc_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(RagDocument)
    if doc_type:
        query = query.filter(RagDocument.doc_type == doc_type)
    
    # Limit content length for list view to avoid huge payload
    documents = query.all()
    
    # We return a simplified version for the list
    results = []
    for doc in documents:
        results.append({
            "id": str(doc.id),
            "doc_type": doc.doc_type,
            "skill": doc.skill,
            "topic": doc.topic,
            "difficulty_band": doc.difficulty_band,
            "source_file": doc.source_file,
            "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
        })
    return results

@router.get("/{doc_id}")
def get_document_detail(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(RagDocument).filter(RagDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/duplicates/check")
def check_duplicates(db: Session = Depends(get_db)):
    """Finds documents with identical content."""
    from sqlalchemy import func
    
    # helper to find duplicates
    subquery = db.query(
        RagDocument.content,
        func.count(RagDocument.id).label('count')
    ).group_by(RagDocument.content).having(func.count(RagDocument.id) > 1).subquery()
    
    duplicates = db.query(RagDocument).join(
        subquery, RagDocument.content == subquery.c.content
    ).order_by(RagDocument.content).all()
    
    # Group by content for response
    result = {}
    for doc in duplicates:
        preview = doc.content[:50] + "..."
        if preview not in result:
            result[preview] = {"count": 0, "ids": [], "doc_type": doc.doc_type}
        result[preview]["count"] += 1
        result[preview]["ids"].append(str(doc.id))
        
    return {"duplicate_groups": len(result), "total_duplicates_items": len(duplicates), "details": result}

@router.delete("/duplicates/clean")
def clean_duplicates(db: Session = Depends(get_db)):
    """Deletes all duplicates, keeping one instance per content group."""
    from sqlalchemy import func
    
    # 1. Identify IDs to keep (e.g. min ID for each content group)
    subquery = db.query(
        func.min(RagDocument.id).label('keep_id'),
        RagDocument.content
    ).group_by(RagDocument.content).subquery()
    
    # 2. Find IDs that represent duplicates (NOT in the keep list)
    # This is a bit complex in pure ORM delete, simpler to fetch IDs to delete
    
    # Get all IDs
    all_docs = db.query(RagDocument.id, RagDocument.content).all()
    seen = set()
    to_delete = []
    
    for doc_id, content in all_docs:
        # Use content hash or direct string
        if content in seen:
            to_delete.append(doc_id)
        else:
            seen.add(content)
            
    if not to_delete:
        return {"deleted_count": 0, "message": "No duplicates found"}
        
    # Delete them
    db.query(RagDocument).filter(RagDocument.id.in_(to_delete)).delete(synchronize_session=False)
    db.commit()
    
    return {"deleted_count": len(to_delete), "message": f"Cleaned {len(to_delete)} duplicate documents."}
