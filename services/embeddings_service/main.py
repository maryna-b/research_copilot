from fastapi import FastAPI
import os

app = FastAPI(title="Embeddings Service", version="1.0.0")

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "embeddings-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
