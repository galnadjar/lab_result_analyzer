from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
import polars as pl
from src.sqldb import SQLiteDB
from src.handler import handle_upload, handle_bootstrap
from src.constants import UPLOAD_DIR, STATIC_DIR

# initialize DB & API
app = FastAPI(lifespan=lifespan)
db = SQLiteDB("experiments.db")


async def startup_event():
    handle_bootstrap(db)

async def shutdown_event():
    db.close_connection()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_event()
    yield
    await shutdown_event()

@app.get("/")
def serve_root_page():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/upload")
async def upload_file(fileInput: UploadFile = File(...)):

    # for convenience
    file = fileInput

    # # Validate file type if necessary
    if not (file.filename.endswith(".csv") or file.filename.endswith((".xlsx", ".xls"))):
        raise HTTPException(status_code=400, detail="Only CSV or Excel files are allowed.")

    # Save the uploaded file to the server
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    error_level = handle_upload(db, file)
    if error_level:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid results in file: {file.filename}"
        )
    return {"message": "File uploaded and processed successfully", "filename": file.filename}



@app.get("/api/charts/{experiment_type}")
async def get_results(experiment_type: str):
    data = db.fetch_all(f"SELECT * FROM {experiment_type}")
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for the {experiment_type} chart. Please upload data first."
        )
    df = pl.DataFrame(data)

    # Calculate statistics
    statistics = {
        "median": df["calculated_value"].median(),
        "average": df["calculated_value"].mean(),
        "std_dev": df["calculated_value"].std(),
    }
    return {"results": data, "statistics": statistics}


