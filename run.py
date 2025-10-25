
import logging
from src.app.server import app

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(app, host="0.0.0.0", port=8082, reload=True, log_level="debug")
