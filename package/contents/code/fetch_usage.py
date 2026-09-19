#!/usr/bin/env python3
"""Codex account bridge for the Codex Usage Plasma widget.

The bridge speaks to ``codex app-server`` over JSONL. It never reads Codex
credential files and never returns access tokens to QML.
"""

from __future__ import annotations

import json
import os
import select
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


APP_VERSION = "1.1.0"
CLIENT_INFO = {
    "name": "kde_codex_usage",
    "title": "Codex Usage for KDE Plasma",
    "version": APP_VERSION,
}


class BridgeError(RuntimeError):
    """A user-displayable bridge failure."""


class CodexNotFound(BridgeError):
    """Raised when no supported Codex executable can be located."""


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, separators=(",", ":")), flush=True)


def remaining(window: dict[str, Any] | None) -> dict[str, Any] | None:
    if not window:
        return None
    used = max(0, min(100, int(round(float(window.get("usedPercent", 0))))))
    return {
        "usedPercent": used,
        "remainingPercent": 100 - used,
        "windowDurationMins": window.get("windowDurationMins"),
        "resetsAt": window.get("resetsAt"),
    }


def executable_candidates() -> list[Path]:
    candidates: list[Path] = []
    override = os.environ.get("CODEX_USAGE_CODEX_BIN")
    if override:
        candidates.append(Path(override).expanduser())
    on_path = shutil.which("codex")
    if on_path:
        candidates.append(Path(on_path))
    candidates.extend(
        [
            Path.home() / ".local/bin/codex",
            Path("/usr/local/bin/codex"),
            Path("/usr/bin/codex"),
            Path("/usr/lib/chatgpt/resources/codex"),
        ]
    )
    return candidates


def codex_executable() -> str:
    seen: set[Path] = set()
    for candidate in executable_candidates():
        resolved = candidate.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise CodexNotFound("Codex is not installed or could not be found")


class AppServer:
    """Minimal synchronous client for the local Codex app server."""

    def __init__(self, executable: str, timeout_seconds: float = 20.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.process = subprocess.Popen(
            [executable, "app-server", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            start_new_session=True,
        )

    def __enter__(self) -> "AppServer":
        self.send(
            {
                "method": "initialize",
                "id": 0,
                "params": {"clientInfo": CLIENT_INFO},
            }
        )
        self.wait_for_id(0)
        self.send({"method": "initialized", "params": {}})
        return self

    def __exit__(self, *_: object) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)

    def send(self, message: dict[str, Any]) -> None:
        if self.process.stdin is None:
            raise BridgeError("Codex app server input is unavailable")
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def read_message(self, timeout_seconds: float | None = None) -> dict[str, Any]:
        if self.process.stdout is None:
            raise BridgeError("Codex app server output is unavailable")
        timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds
        readable, _, _ = select.select([self.process.stdout], [], [], timeout)
        if not readable:
            raise TimeoutError("Timed out while waiting for Codex")
        line = self.process.stdout.readline()
        if not line:
            raise BridgeError("Codex app server closed unexpectedly")
        try:
            return json.loads(line)
        except json.JSONDecodeError as error:
            raise BridgeError("Codex returned an invalid response") from error

    def wait_for_id(self, request_id: int) -> dict[str, Any]:
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            message = self.read_message(max(0.0, deadline - time.monotonic()))
            if message.get("id") != request_id:
                continue
            if message.get("error"):
                detail = message["error"].get("message", "Codex returned an error")
                raise BridgeError(detail)
            return message.get("result") or {}
        raise TimeoutError("Timed out while waiting for Codex")

    def request(self, method: str, request_id: int, params: dict[str, Any]) -> dict[str, Any]:
        self.send({"method": method, "id": request_id, "params": params})
        return self.wait_for_id(request_id)


def normalise_limits(response: dict[str, Any]) -> dict[str, Any]:
    limits = response.get("rateLimits") or {}
    credits = limits.get("credits") or {}
    reset_credits = response.get("rateLimitResetCredits") or {}
    primary = remaining(limits.get("primary"))
    secondary = remaining(limits.get("secondary"))
    if primary is None or secondary is None:
        raise BridgeError("Codex did not return both usage windows")
    return {
        "ok": True,
        "state": "ready",
        "fetchedAt": int(time.time()),
        "primary": primary,
        "secondary": secondary,
        "planType": limits.get("planType"),
        "credits": {
            "hasCredits": bool(credits.get("hasCredits", False)),
            "unlimited": bool(credits.get("unlimited", False)),
            "balance": str(credits.get("balance", "0")),
        },
        "resetCredits": int(reset_credits.get("availableCount", 0) or 0),
        "rateLimitReachedType": limits.get("rateLimitReachedType"),
        "spendControlReached": bool(limits.get("spendControlReached", False)),
    }


def account_state(server: AppServer) -> dict[str, Any]:
    account_response = server.request("account/read", 1, {"refreshToken": False})
    account = account_response.get("account")
    if account is None:
        return {
            "ok": False,
            "state": "auth_required",
            "message": "Sign in to Codex with ChatGPT to read usage limits",
        }
    if account.get("type") not in {"chatgpt", "chatgptAuthTokens"}:
        return {
            "ok": False,
            "state": "unsupported_auth",
            "message": "Codex is not signed in with a ChatGPT account",
        }
    return {"ok": True, "state": "authenticated"}


def read_limits() -> dict[str, Any]:
    executable = codex_executable()
    with AppServer(executable) as server:
        state = account_state(server)
        if not state["ok"]:
            return state
        response = server.request("account/rateLimits/read", 2, {})
        return normalise_limits(response)


def safe_auth_url(value: str) -> str:
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (
        hostname == "chatgpt.com" or hostname.endswith(".chatgpt.com")
    ):
        raise BridgeError("Codex returned an unexpected sign-in address")
    return value


def open_browser(url: str) -> None:
    opener = shutil.which("xdg-open") or shutil.which("kioclient6")
    if not opener:
        raise BridgeError("No desktop web browser opener was found")
    command = [opener, url]
    if Path(opener).name == "kioclient6":
        command = [opener, "exec", url]
    subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def sign_in(timeout_seconds: float = 300.0) -> dict[str, Any]:
    executable = codex_executable()
    with AppServer(executable, timeout_seconds=20.0) as server:
        state = account_state(server)
        if state["ok"]:
            return {"ok": True, "state": "login_complete"}

        login = server.request(
            "account/login/start",
            3,
            {
                "type": "chatgpt",
                "useHostedLoginSuccessPage": True,
                "appBrand": "codex",
            },
        )
        auth_url = safe_auth_url(str(login.get("authUrl", "")))
        login_id = login.get("loginId")
        open_browser(auth_url)

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            message = server.read_message(max(0.0, deadline - time.monotonic()))
            if message.get("method") != "account/login/completed":
                continue
            params = message.get("params") or {}
            if login_id and params.get("loginId") != login_id:
                continue
            if params.get("success"):
                return {"ok": True, "state": "login_complete"}
            raise BridgeError(params.get("error") or "ChatGPT sign-in was not completed")
        raise TimeoutError("ChatGPT sign-in timed out")


def main(argv: list[str]) -> int:
    action = argv[1] if len(argv) > 1 else "usage"
    try:
        if action == "usage":
            emit(read_limits())
        elif action == "login":
            emit(sign_in())
        else:
            raise BridgeError(f"Unknown action: {action}")
        return 0
    except CodexNotFound as error:
        emit({"ok": False, "state": "codex_missing", "message": str(error)})
        return 2
    except Exception as error:
        emit({"ok": False, "state": "error", "message": str(error)})
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
