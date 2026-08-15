from __future__ import annotations

import os
import threading
import webbrowser

from waitress import serve

from app import create_app


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0").lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    host = os.getenv("SPOTIFY_ANALYTICS_HOST", "127.0.0.1")
    port = int(os.getenv("SPOTIFY_ANALYTICS_PORT", "5000"))
    debug = env_bool("SPOTIFY_ANALYTICS_DEBUG")
    app = create_app({"DEBUG": debug})
    url = f"http://{host}:{port}"
    if env_bool("SPOTIFY_ANALYTICS_OPEN_BROWSER", True):
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"Spotify Listening Analytics is running at {url}")
    if debug:
        app.run(host=host, port=port, debug=True, use_reloader=False)
    else:
        serve(app, host=host, port=port, threads=6)
