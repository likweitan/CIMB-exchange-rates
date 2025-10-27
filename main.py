from __future__ import annotations

import os

from app import create_app

app = create_app()


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=debug)
