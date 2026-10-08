#!/usr/bin/env python3
"""Stdio-to-Streamable-HTTP MCP proxy (stdlib only).

Lola's Agent Plugins validator rejects `${VAR}` in remote `url`/`headers`,
so authenticated or dynamic-URL MCP servers cannot be declared as
streamable-http. This process speaks MCP stdio to the client and POSTs
Streamable HTTP upstream.

Each plugin pack must ship its own copy under scripts/ (PLUGIN_ROOT cannot
reach another pack). Keep rh-sre, rh-automation, and rh-ai-engineer in sync.

Environment (first non-empty wins):
  URL:   MCP_HTTP_URL | AAP_MCP_SERVER | AI_OBSERVABILITY_MCP_URL
  Token: MCP_HTTP_TOKEN | AAP_API_TOKEN  (optional Bearer; required for AAP)
"""
from __future__ import annotations

import asyncio
import ipaddress
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request


_ENDPOINT_PATH = re.compile(r"^[a-zA-Z0-9_\-]+(/[a-zA-Z0-9_\-]+)*$")
_METADATA_HOSTS = {
    "metadata.google.internal",
    "metadata.goog",
    "metadata.internal",
}


class SSRFValidationError(Exception):
    """Raised when the configured upstream target fails security checks."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect())


def sanitize_endpoint_path(endpoint_path: str) -> str:
    path = endpoint_path.strip()
    if not _ENDPOINT_PATH.fullmatch(path):
        raise SSRFValidationError(f"Invalid path format '{endpoint_path}'.")
    return path


def resolve_upstream() -> tuple[str, str]:
    url = (
        os.environ.get("MCP_HTTP_URL", "").strip()
        or os.environ.get("AAP_MCP_SERVER", "").strip()
        or os.environ.get("AI_OBSERVABILITY_MCP_URL", "").strip()
    )
    token = (
        os.environ.get("MCP_HTTP_TOKEN", "").strip()
        or os.environ.get("AAP_API_TOKEN", "").strip()
    )
    using_aap = bool(os.environ.get("AAP_MCP_SERVER", "").strip()) and not os.environ.get(
        "MCP_HTTP_URL", ""
    ).strip()
    if not url:
        raise SSRFValidationError(
            "Set MCP_HTTP_URL (or AAP_MCP_SERVER / AI_OBSERVABILITY_MCP_URL)."
        )
    if using_aap and not token:
        raise SSRFValidationError("AAP_MCP_SERVER and AAP_API_TOKEN must be set.")
    return url, token


def compose_upstream_url(server_env: str, endpoint_path: str) -> str:
    """Join a hostname or base URL with /<endpoint>.

    Host-only values get ``https://``. If the base path already ends with the
    endpoint (for example a full ``.../mcp`` URL), it is not appended again.
    """
    raw = server_env.strip()
    if not raw:
        raise SSRFValidationError("Upstream URL is empty.")
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urllib.parse.urlparse(raw)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise SSRFValidationError("Only HTTP or HTTPS endpoints are allowed.")
    if parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise SSRFValidationError(
            "Upstream URL must not include credentials, query, or fragment."
        )
    if not parsed.hostname:
        raise SSRFValidationError("Upstream URL has no hostname.")
    base_path = parsed.path.rstrip("/")
    already = base_path.endswith("/" + endpoint_path) or base_path == f"/{endpoint_path}"
    if already:
        full_path = base_path
    elif base_path:
        full_path = f"{base_path}/{endpoint_path}"
    else:
        full_path = f"/{endpoint_path}"
    return urllib.parse.urlunparse((scheme, parsed.netloc, full_path, "", "", ""))


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    # Private and loopback are allowed (on-prem AAP, cluster services,
    # local port-forwards). ::1 is both loopback and reserved in ipaddress.
    if ip.is_loopback:
        return False
    return (
        ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified
        or ip.is_reserved
    )


def assert_host_allowed(host: str, port: int | None, *, allow_cleartext: bool) -> None:
    lowered = host.lower().rstrip(".")
    if lowered in _METADATA_HOSTS:
        raise SSRFValidationError(f"Restricted target host '{host}'.")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None and _is_blocked_ip(literal):
        raise SSRFValidationError(f"Host '{host}' is a restricted IP ({literal}).")
    if literal is not None and allow_cleartext and not (
        literal.is_private or literal.is_loopback
    ):
        raise SSRFValidationError("Cleartext HTTP is only allowed for private or loopback hosts.")

    try:
        addr_info = socket.getaddrinfo(host, port or 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise SSRFValidationError(f"DNS resolution failed for '{host}': {exc}") from exc

    resolved = {info[4][0] for info in addr_info}
    if not resolved:
        raise SSRFValidationError(f"DNS resolution failed for '{host}'.")
    for ip_str in resolved:
        ip = ipaddress.ip_address(ip_str)
        if _is_blocked_ip(ip):
            raise SSRFValidationError(f"Host '{host}' resolved to restricted IP ({ip}).")
        if allow_cleartext and not (ip.is_private or ip.is_loopback):
            raise SSRFValidationError(
                f"Cleartext HTTP is only allowed for private or loopback hosts ({ip})."
            )


def sse_or_json_messages(body: bytes, content_type: str) -> list[bytes]:
    """Turn an HTTP body into newline-delimited JSON-RPC payloads."""
    if not body.strip():
        return []
    ctype = content_type.lower()
    chunks: list[bytes]
    if "text/event-stream" in ctype:
        chunks = _sse_data_payloads(body)
    else:
        chunks = [body.strip()]
    messages: list[bytes] = []
    for chunk in chunks:
        try:
            parsed = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        messages.append(json.dumps(parsed, separators=(",", ":")).encode("utf-8"))
    return messages


def _sse_data_payloads(body: bytes) -> list[bytes]:
    payloads: list[bytes] = []
    current: list[str] = []
    text = body.decode("utf-8", errors="replace")
    for line in text.splitlines():
        if line == "":
            if current:
                payloads.append("\n".join(current).encode("utf-8"))
                current = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            current.append(line[5:].lstrip(" "))
    if current:
        payloads.append("\n".join(current).encode("utf-8"))
    return payloads


def _jsonrpc_id(payload: bytes) -> object:
    try:
        message = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if isinstance(message, dict):
        return message.get("id")
    return None


def _write_stdout_messages(messages: list[bytes]) -> None:
    for message in messages:
        sys.stdout.buffer.write(message)
        sys.stdout.buffer.write(b"\n")
    if messages:
        sys.stdout.buffer.flush()


def _write_jsonrpc_error(rpc_id: object, message: str) -> None:
    error = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "error": {"code": -32000, "message": message},
    }
    _write_stdout_messages(
        [json.dumps(error, separators=(",", ":")).encode("utf-8")]
    )


class HttpMcpProxy:
    def __init__(self, endpoint_path: str):
        self.server_env, self.token = resolve_upstream()
        self.endpoint_path = sanitize_endpoint_path(endpoint_path)
        self.session_id: str | None = None
        self.protocol_version: str | None = None

    def validate_and_build_url(self) -> str:
        target_url = compose_upstream_url(self.server_env, self.endpoint_path)
        parsed = urllib.parse.urlparse(target_url)
        host = parsed.hostname
        if not host:
            raise SSRFValidationError("Upstream URL has no hostname.")
        default_port = 80 if parsed.scheme == "http" else 443
        assert_host_allowed(
            host,
            parsed.port or default_port,
            allow_cleartext=(parsed.scheme == "http"),
        )
        return target_url

    def _note_protocol_version(self, payload: bytes) -> None:
        try:
            message = json.loads(payload)
        except json.JSONDecodeError:
            return
        if not isinstance(message, dict) or message.get("method") != "initialize":
            return
        params = message.get("params")
        if not isinstance(params, dict):
            return
        version = params.get("protocolVersion")
        if isinstance(version, str) and version:
            self.protocol_version = version

    def _post_sync(self, target_url: str, payload: bytes) -> tuple[bytes, str]:
        parsed = urllib.parse.urlparse(target_url)
        origin = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "MCP-HTTP-Proxy/1.0",
            "Origin": origin.rstrip("/"),
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        if self.protocol_version:
            headers["MCP-Protocol-Version"] = self.protocol_version
        req = urllib.request.Request(
            target_url,
            data=payload,
            headers=headers,
            method="POST",
        )
        with _OPENER.open(req, timeout=30) as response:
            session = response.headers.get("Mcp-Session-Id")
            if session:
                self.session_id = session
            content_type = response.headers.get("Content-Type", "")
            return response.read(), content_type

    async def start(self) -> None:
        target_url = self.validate_and_build_url()
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line = await reader.readline()
            if not line:
                break
            payload = line.strip()
            if not payload:
                continue
            rpc_id = _jsonrpc_id(payload)
            self._note_protocol_version(payload)
            try:
                body, content_type = await asyncio.to_thread(
                    self._post_sync, target_url, payload
                )
            except urllib.error.HTTPError as err:
                sys.stderr.write(f"Proxy HTTP Error {err.code}: {err.reason}\n")
                _write_jsonrpc_error(rpc_id, f"HTTP {err.code}: {err.reason}")
                continue
            except (urllib.error.URLError, TimeoutError, OSError) as err:
                sys.stderr.write(f"Proxy Network Error: {err}\n")
                _write_jsonrpc_error(rpc_id, "Network error contacting upstream MCP")
                continue
            messages = sse_or_json_messages(body, content_type)
            if messages:
                _write_stdout_messages(messages)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Error: Missing endpoint path argument.\n")
        sys.exit(1)

    try:
        proxy = HttpMcpProxy(sys.argv[1])
        asyncio.run(proxy.start())
    except SSRFValidationError as exc:
        sys.stderr.write(f"SSRF Security Error: {exc}\n")
        sys.exit(1)
