"""
__main__.py — Entry point for python -m gui.

Launches the PyWebView window with the Api bridge class.
"""

import os

import webview

from gui.app import Api

html_path = os.path.join(os.path.dirname(__file__), "index.html")

if __name__ == "__main__":
    webview.create_window(
        "PokemonAgent GUI",
        url=html_path,
        js_api=Api(),
        width=500,
        height=500,
        resizable=False,
    )
    webview.start(gui="qt")
