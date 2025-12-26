import shutil
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from etl.etl_rag_builder import process_csv

router = APIRouter(
    prefix="/etl",
    tags=["etl"]
)

@router.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only .csv files are allowed.")
    
    # Save to a temp file
    # We use a temp file in a location we know or just system temp
    # Since we are in docker, /tmp is fine.
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
            
        # Run ETL
        result = process_csv(tmp_path, source_filename=file.filename)
        
        # Cleanup
        os.remove(tmp_path)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
