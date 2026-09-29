"""
Start the Social Media Privacy Risk Assessment Framework.

    python run.py

Then open http://127.0.0.1:5000 in your browser.
"""

import logging

from backend.app import create_app
from backend.config import Config

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    app = create_app()
    print(f"\n  Privacy Risk Assessment running at http://{Config.HOST}:{Config.PORT}\n")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
