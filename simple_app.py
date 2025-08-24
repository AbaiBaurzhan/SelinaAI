from fastapi import FastAPI
import uvicorn
app = FastAPI()
@app.get("/healthz")
def healthz(): return {"status": "healthy"}
