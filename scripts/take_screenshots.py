"""Automated screenshot capture script using Chrome DevTools Protocol (CDP).
Captures light and dark mode screenshots across all 7 pages at 1440px and 375px.
Output directories:
- docs/screenshots/light/
- docs/screenshots/dark/
"""

import os
import sys
import json
import time
import base64
import asyncio
import subprocess
import urllib.request
import websockets

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_LIGHT_DIR = os.path.join(PROJECT_ROOT, "docs", "screenshots", "light")
SCREENSHOTS_DARK_DIR = os.path.join(PROJECT_ROOT, "docs", "screenshots", "dark")
os.makedirs(SCREENSHOTS_LIGHT_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DARK_DIR, exist_ok=True)

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 9222

PAGES = [
    ("", "home"),
    ("recommend", "recommend"),
    ("prompt-lab", "prompt_lab"),
    ("test-results", "test_results"),
    ("automation-log", "automation_log"),
    ("history", "history"),
    ("about", "about")
]

VIEWPORTS = [
    (1440, 900, "1440px", False),
    (375, 812, "375px", True)
]


async def capture_page(ws_url: str, url: str, width: int, height: int, output_path: str, mobile: bool = False):
    async with websockets.connect(ws_url, max_size=25 * 1024 * 1024) as ws:
        msg_id = 0

        async def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            payload = {"id": msg_id, "method": method, "params": params or {}}
            await ws.send(json.dumps(payload))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == msg_id:
                    return resp.get("result", {})

        await send("Page.enable")
        await send("Runtime.enable")

        # Set viewport
        await send("Emulation.setDeviceMetricsOverride", {
            "width": width,
            "height": height,
            "deviceScaleFactor": 1,
            "mobile": mobile
        })

        # Navigate
        await send("Page.navigate", {"url": url})

        # Wait for Streamlit app to render content
        start = time.time()
        while time.time() - start < 10:
            check_js = """
            (() => {
                const header = document.querySelector('.rm-page-header') || document.querySelector('h1') || document.querySelector('.stMarkdown');
                const ready = document.readyState === 'complete';
                return { ready: Boolean(ready && header) };
            })()
            """
            res = await send("Runtime.evaluate", {"expression": check_js, "returnByValue": True})
            val = res.get("result", {}).get("value", {})
            if val.get("ready"):
                break
            await asyncio.sleep(0.4)

        # Allow extra time for layout and fonts to settle
        await asyncio.sleep(1.0)

        # Take screenshot
        ss_res = await send("Page.captureScreenshot", {"format": "png"})
        img_data = base64.b64decode(ss_res.get("data", ""))
        with open(output_path, "wb") as f:
            f.write(img_data)

        print(f"Captured: {os.path.basename(output_path)} ({width}x{height}) - {len(img_data)} bytes")
        return len(img_data) > 5000


def main():
    chrome_proc = subprocess.Popen([
        CHROME_BIN,
        "--headless=new",
        "--disable-gpu",
        f"--remote-debugging-port={PORT}",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        time.sleep(2)

        themes = [
            ("light", SCREENSHOTS_LIGHT_DIR),
            ("dark", SCREENSHOTS_DARK_DIR)
        ]

        total_captured = 0

        for theme_name, out_dir in themes:
            print(f"\n--- Capturing Theme: {theme_name.upper()} ---")
            for page_route, page_name in PAGES:
                url = f"http://localhost:8501/{page_route}?theme={theme_name}"
                for width, height, vp_label, is_mobile in VIEWPORTS:
                    fname = f"{page_name}_{vp_label}.png"
                    out_path = os.path.join(out_dir, fname)

                    # Create new tab via PUT
                    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new", data=b"", method="PUT")
                    with urllib.request.urlopen(req) as resp:
                        tab_data = json.loads(resp.read().decode())
                    ws_url = tab_data["webSocketDebuggerUrl"]
                    tab_id = tab_data["id"]

                    try:
                        ok = asyncio.run(capture_page(ws_url, url, width, height, out_path, is_mobile))
                        if ok:
                            total_captured += 1
                    finally:
                        try:
                            close_req = urllib.request.Request(f"http://127.0.0.1:{PORT}/json/close/{tab_id}", data=b"", method="PUT")
                            with urllib.request.urlopen(close_req):
                                pass
                        except Exception:
                            pass

        print(f"\nTotal screenshots successfully captured: {total_captured} / 28")

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()


if __name__ == "__main__":
    main()
