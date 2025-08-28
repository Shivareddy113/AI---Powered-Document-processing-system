from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import os, shutil, json
from app.services import ocr_service, nlp_service, validation

app = FastAPI(title="AI Document Processing System")

UPLOAD_DIR = "uploads"
RESULTS_DIR = "results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# ✅ Home route
@app.get("/")
def home():
    return {"message": "🚀 AI Document Processing System is running. Go to /docs to test the API."}

# ✅ Document processing route
@app.post("/process-document/")
async def process_document(file: UploadFile = File(...)):
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Step 1: OCR
    text = ocr_service.extract_text(file_path)

    # Step 2: NLP (NER)
    entities = nlp_service.extract_entities(text)

    # Step 3: Validation
    validated = validation.apply_rules(entities)

    # Save results into results folder
    result_data = {
        "filename": file.filename,
        "raw_text": text[:500],   # preview
        "entities": entities,
        "validated": validated
    }
    result_path = os.path.join(RESULTS_DIR, file.filename + ".json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=4)

    return JSONResponse(result_data)

# ✅ List processed documents
@app.get("/processed-documents/")
def get_processed_documents():
    files = os.listdir(RESULTS_DIR)
    return {"processed_files": files}

# ✅ Fetch specific processed document
@app.get("/processed-documents/{filename}")
def get_document_result(filename: str):
    result_path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(result_path):
        return {"error": "File not found"}
    with open(result_path, "r", encoding="utf-8") as f:
        return json.load(f)
