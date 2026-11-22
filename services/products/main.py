from fastapi import FastAPI

app = FastAPI(title="Products Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"service": "products", "version": "0.2"}
