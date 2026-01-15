from fastapi import FastAPI
import uvicorn  # Add this import

app = FastAPI(title="learning cicd")

@app.get("/health")
def health():
    return {"message": "server running"}  # Fixed typo: "meaage" → "message"

