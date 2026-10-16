"""Servidor web local para el análisis estadístico del Caso 1."""

from __future__ import annotations

import argparse
import csv
import io
import json
import mimetypes
import os
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from case1_stats import DATASET, DEFAULT_SEED, complete_analysis


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class Case1Handler(BaseHTTPRequestHandler):
    server_version = "Caso1Web/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _send_bytes(self, content: bytes, content_type: str, status: int = 200, extra_headers: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store" if content_type.startswith("application/json") else "no-cache")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        content = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self._send_bytes(content, "application/json; charset=utf-8", status)

    def _serve_static(self, relative_path: str) -> None:
        requested = (STATIC_DIR / relative_path).resolve()
        try:
            requested.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self._send_json({"error": "Ruta no permitida."}, HTTPStatus.FORBIDDEN)
            return
        if not requested.is_file():
            self._send_json({"error": "Recurso no encontrado."}, HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(requested.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type += "; charset=utf-8"
        self._send_bytes(requested.read_bytes(), content_type)

    def do_GET(self) -> None:  # noqa: N802 - nombre exigido por BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json({"status": "ok", "service": "Caso 1 · Apolo 11"})
            return
        if parsed.path == "/api/analysis":
            query = parse_qs(parsed.query)
            try:
                seed = int(query.get("seed", [DEFAULT_SEED])[0])
                if not 0 <= seed <= 2**32 - 1:
                    raise ValueError
            except (TypeError, ValueError):
                self._send_json({"error": "La semilla debe ser un entero entre 0 y 4294967295."}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json(complete_analysis(seed))
            return
        if parsed.path == "/api/data.csv":
            stream = io.StringIO()
            writer = csv.DictWriter(stream, fieldnames=["scenario", "load", "time_a", "time_b"])
            writer.writeheader()
            writer.writerows(DATASET)
            self._send_bytes(
                stream.getvalue().encode("utf-8-sig"),
                "text/csv; charset=utf-8",
                extra_headers={"Content-Disposition": 'attachment; filename="caso1_apolo11_datos.csv"'},
            )
            return
        if parsed.path in {"/", "/index.html"}:
            self._serve_static("index.html")
            return
        if parsed.path.startswith("/static/"):
            self._serve_static(parsed.path.removeprefix("/static/"))
            return
        self._send_json({"error": "Ruta no encontrada."}, HTTPStatus.NOT_FOUND)


def main() -> None:
    parser = argparse.ArgumentParser(description="Aplicación web del Caso 1 de Estadística y Probabilidades.")
    parser.add_argument(
        "--host",
        default=os.environ.get("HOST", "127.0.0.1"),
        help="Dirección de escucha; HOST permite configurarla en alojamiento web.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8765")),
        help="Puerto; PORT permite usar el valor asignado por el proveedor.",
    )
    parser.add_argument("--open", action="store_true", help="Abrir el navegador automáticamente.")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Case1Handler)
    display_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
    url = f"http://{display_host}:{args.port}"
    print(f"Aplicación disponible en {url}")
    print("Presiona Ctrl+C para detenerla.")
    if args.open:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

