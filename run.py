
import logging
logging.basicConfig(level=logging.DEBUG)
from src.app.server import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082, reload=True, log_level="debug")
