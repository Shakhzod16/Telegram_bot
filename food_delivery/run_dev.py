from __future__ import annotations

import asyncio
import os
import random
import re
import string
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit


def _terminate(proc: subprocess.Popen[object]) -> None:
    if proc.poll() is None:
        proc.terminate()


def _kill(proc: subprocess.Popen[object]) -> None:
    if proc.poll() is None:
        proc.kill()


async def _wait_with_timeout(proc: subprocess.Popen[object], timeout: float) -> None:
    try:
        await asyncio.wait_for(asyncio.to_thread(proc.wait), timeout=timeout)
    except TimeoutError:
        _kill(proc)
        await asyncio.to_thread(proc.wait)


def _load_dotenv(dotenv_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not dotenv_path.exists():
        return values

    for raw in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _is_enabled(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _build_subdomain() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"foodexpress-{int(time.time()) % 100000}-{suffix}"


def _normalize_provider(value: str | None) -> str | None:
    if value is None:
        return None
    provider = value.strip().lower()
    if not provider:
        return None
    if provider not in {"none", "auto", "cloudflared", "localtunnel"}:
        raise RuntimeError(
            "Unsupported DEV_TUNNEL_PROVIDER. Use one of: none, auto, cloudflared, localtunnel."
        )
    return provider


def _is_dynamic_host(host: str) -> bool:
    dynamic_domains = (
        "loca.lt",
        "localtunnel.me",
        "trycloudflare.com",
        "lhr.life",
        "pinggy.io",
    )
    normalized = host.lower().split(":", 1)[0]
    return any(normalized == domain or normalized.endswith(f".{domain}") for domain in dynamic_domains)


def _requires_runtime_tunnel(webapp_url: str) -> bool:
    raw = webapp_url.strip()
    if not raw:
        return True
    parsed = urlsplit(raw)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        return True
    return _is_dynamic_host(parsed.netloc)


def _pick_tunnel_provider(env: dict[str, str]) -> str:
    configured = _normalize_provider(env.get("DEV_TUNNEL_PROVIDER"))
    if configured:
        return configured
    if _is_enabled(env.get("DEV_USE_LOCALTUNNEL"), default=False):
        return "localtunnel"
    if _requires_runtime_tunnel(env.get("WEBAPP_URL", "")):
        return "auto"
    return "none"


def _extract_matching_url(line: str, allowed_suffixes: tuple[str, ...]) -> str | None:
    for match in re.findall(r"https://[A-Za-z0-9.-]+", line):
        parsed = urlsplit(match)
        host = parsed.netloc.lower()
        if any(host == suffix or host.endswith(f".{suffix}") for suffix in allowed_suffixes):
            return f"https://{host}"
    return None


def _start_output_watcher(
    *,
    proc: subprocess.Popen[object],
    name: str,
    extractor: Callable[[str], str | None],
) -> dict[str, str | None]:
    state: dict[str, str | None] = {"url": None}

    def _worker() -> None:
        stream = proc.stdout
        if stream is None:
            return
        for raw in stream:
            line = raw.rstrip()
            if line:
                print(f"[{name}] {line}")
            if state["url"] is None:
                maybe_url = extractor(line)
                if maybe_url:
                    state["url"] = maybe_url.rstrip("/")

    threading.Thread(target=_worker, daemon=True, name=f"{name}-log-reader").start()
    return state


async def _await_tunnel_url(
    *,
    proc: subprocess.Popen[object],
    provider: str,
    state: dict[str, str | None],
    timeout_seconds: float,
) -> str:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if state["url"]:
            return str(state["url"])
        code = proc.poll()
        if code is not None:
            raise RuntimeError(f"{provider} exited early with code {code}")
        await asyncio.sleep(0.2)
    raise RuntimeError(f"{provider} did not provide a public URL within {int(timeout_seconds)}s")


async def _start_tunnel_provider(
    *,
    provider: str,
    root: Path,
    env: dict[str, str],
) -> tuple[subprocess.Popen[object], str]:
    if provider == "cloudflared":
        print("Starting cloudflared quick tunnel ...")
        proc: subprocess.Popen[object] = subprocess.Popen(
            ["npx.cmd", "-y", "cloudflared", "tunnel", "--url", "http://localhost:8000", "--protocol", "http2"],
            cwd=str(root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        state = _start_output_watcher(
            proc=proc,
            name="cloudflared",
            extractor=lambda line: _extract_matching_url(line, ("trycloudflare.com", "lhr.life")),
        )
        try:
            base_url = await _await_tunnel_url(
                proc=proc,
                provider=provider,
                state=state,
                timeout_seconds=45,
            )
            return proc, base_url
        except Exception:
            _terminate(proc)
            await _wait_with_timeout(proc, timeout=10)
            raise

    if provider == "localtunnel":
        subdomain = env.get("LT_SUBDOMAIN", "").strip() or _build_subdomain()
        expected_url = f"https://{subdomain}.loca.lt"
        print(f"Starting localtunnel on {expected_url} ...")
        proc = subprocess.Popen(
            ["npx.cmd", "-y", "localtunnel", "--port", "8000", "--subdomain", subdomain],
            cwd=str(root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        state = _start_output_watcher(
            proc=proc,
            name="localtunnel",
            extractor=lambda line: _extract_matching_url(line, ("loca.lt", "localtunnel.me")),
        )
        try:
            base_url = await _await_tunnel_url(
                proc=proc,
                provider=provider,
                state=state,
                timeout_seconds=35,
            )
            return proc, base_url
        except Exception:
            _terminate(proc)
            await _wait_with_timeout(proc, timeout=10)
            raise

    raise RuntimeError(f"Unsupported tunnel provider: {provider}")


async def _start_tunnel_if_needed(
    *,
    root: Path,
    env: dict[str, str],
) -> subprocess.Popen[object] | None:
    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    runtime_webapp_file = logs_dir / "runtime_webapp_url.txt"
    runtime_backend_file = logs_dir / "runtime_backend_url.txt"

    provider = _pick_tunnel_provider(env)
    print(f"Using DEV_TUNNEL_PROVIDER={provider}")
    if provider == "none":
        runtime_backend_file.write_text(f"{env.get('BACKEND_URL', '').strip()}\n", encoding="utf-8")
        runtime_webapp_file.write_text(f"{env.get('WEBAPP_URL', '').strip()}\n", encoding="utf-8")
        return None

    candidates = ("cloudflared", "localtunnel") if provider == "auto" else (provider,)
    errors: list[str] = []
    for candidate in candidates:
        try:
            proc, base_url = await _start_tunnel_provider(provider=candidate, root=root, env=env)
            env["BACKEND_URL"] = base_url
            env["WEBAPP_URL"] = f"{base_url}/webapp/"
            print(f"Using BACKEND_URL={env['BACKEND_URL']}")
            print(f"Using WEBAPP_URL={env['WEBAPP_URL']}")
            runtime_backend_file.write_text(f"{env['BACKEND_URL']}\n", encoding="utf-8")
            runtime_webapp_file.write_text(f"{env['WEBAPP_URL']}\n", encoding="utf-8")
            return proc
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")
            print(f"{candidate} setup failed: {exc}")

    error_text = "; ".join(errors) if errors else "unknown error"
    raise RuntimeError(f"Unable to establish tunnel. {error_text}")


async def main() -> None:
    root = Path(__file__).resolve().parent
    env = os.environ.copy()
    env.update(_load_dotenv(root / ".env"))
    npm_cache_dir = root / ".npm-cache"
    npm_cache_dir.mkdir(parents=True, exist_ok=True)
    env.setdefault("npm_config_cache", str(npm_cache_dir))
    env.setdefault("NPM_CONFIG_CACHE", str(npm_cache_dir))

    print(f"Using DATABASE_URL={env.get('DATABASE_URL', '')}")
    print(f"Using REDIS_URL={env.get('REDIS_URL', '')}")
    print(f"Using WEBAPP_URL={env.get('WEBAPP_URL', '')}")
    print(f"Using npm cache={env.get('npm_config_cache', '')}")
    reload_enabled = env.get("DEV_RELOAD", "0").strip().lower() in {"1", "true", "yes", "on"}
    print(f"Using DEV_RELOAD={'1' if reload_enabled else '0'}")
    tunnel_proc = await _start_tunnel_if_needed(root=root, env=env)

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--port",
        "8000",
        "--host",
        "0.0.0.0",
    ]
    if reload_enabled:
        backend_cmd.append("--reload")

    backend = subprocess.Popen(
        backend_cmd,
        cwd=str(root),
        env=env,
    )
    bot_proc = subprocess.Popen([sys.executable, "-m", "bot.main"], cwd=str(root), env=env)

    processes: dict[str, subprocess.Popen[object]] = {"backend": backend, "bot": bot_proc}
    if tunnel_proc is not None:
        processes["tunnel"] = tunnel_proc
    exit_code = 0

    try:
        while True:
            await asyncio.sleep(1)
            for name, proc in processes.items():
                code = proc.poll()
                if code is not None:
                    print(f"{name} exited with code {code}. Stopping remaining process...")
                    exit_code = code or exit_code
                    return
    except KeyboardInterrupt:
        print("Stopping services...")
    finally:
        for proc in processes.values():
            _terminate(proc)
        await asyncio.gather(*(_wait_with_timeout(proc, timeout=10) for proc in processes.values()))
        print("Stopped.")
        if exit_code:
            raise SystemExit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
