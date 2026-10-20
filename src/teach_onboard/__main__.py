"""teach-onboard: start the onboarding web app."""
from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from pathlib import Path

from .llm import LLMError, make_provider
from .method import load_method, packs_dir
from .onboarding import Onboarding
from .packs import list_packs
from .server import serve


def default_home() -> Path:
    return Path(os.environ.get("TEACH_HOME") or "~/teach-courses").expanduser()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="teach-onboard", description="Set up a mastery-learning course in your browser.")
    ap.add_argument("--host", default="127.0.0.1", help="interface to listen on (default: this machine only)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--courses-dir", type=Path, default=None, help="where courses are saved (default: $TEACH_HOME or ~/teach-courses)")
    ap.add_argument("--provider", default=None, help="anthropic (default), bedrock, or fake (offline demo)")
    ap.add_argument("--model", default=None, help="model id (default: claude-opus-5-5, or its Bedrock profile)")
    ap.add_argument("--packs-dir", type=Path, default=None, help="extra folder of course packs")
    ap.add_argument("--open", action="store_true", help="open the page in your browser")
    args = ap.parse_args(argv)

    method = load_method()
    try:
        provider = make_provider(args.provider, args.model)
    except LLMError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # missing credentials or SDK extras surface here
        print(f"error: could not start the {args.provider or 'anthropic'} provider: {e}", file=sys.stderr)
        return 2

    packs = list_packs(packs_dir(), method)
    if args.packs_dir:
        packs.update(list_packs(args.packs_dir.expanduser(), method))
    home = (args.courses_dir or default_home()).expanduser()
    app = Onboarding(provider, method, home, packs)
    info = {
        "provider": provider.name, "model": provider.model, "courses_home": str(home),
        "packs": [{"name": p.name, "title": p.title, "description": p.description, "skills": len(p.skills)}
                  for p in packs.values()],
        "placement_max_items": method.placement_max_items,
        "session_minutes": method.session_minutes,
    }
    httpd = serve(app, info, args.host, args.port)
    url = f"http://{'localhost' if args.host in ('127.0.0.1', 'localhost') else args.host}:{args.port}/"
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print("warning: listening beyond this machine. There is no login; anyone who can reach the port can use it.",
              file=sys.stderr)
    print(f"teach-onboard on {url}  (provider: {provider.name}, model: {provider.model})", flush=True)
    print(f"courses are saved under {home}", flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
