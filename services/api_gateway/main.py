from fastapi import FastAPI

app = FastAPI(title="API Gateway")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-gateway"}

@app.get("/info")
async def info():
    return {"name": "Research Copilot", "version": "0.1.0"}
