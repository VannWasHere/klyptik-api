import uvicorn
from app.main import app
from app.config import PORT, HOST, DEBUG

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)
