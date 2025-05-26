import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from jinja2 import Template
from faker import Faker

from pyapimocker.models import MockConfig, ResponseConfig, RouteConfig


class MockServer:
    def __init__(self, config_path: str, record_mode: bool = False, proxy_base_url: str = None):
        self.config = self._load_config(config_path)
        self.app = FastAPI(title="pyapimocker")
        self.faker = Faker()
        self.record_mode = record_mode
        self.proxy_base_url = proxy_base_url
        self.recorded_mocks = self._load_recorded_mocks()
        self._setup_routes()
        self._add_catch_all()

    def _load_config(self, config_path: str) -> MockConfig:
        with open(config_path) as f:
            if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                config_dict = yaml.safe_load(f)
            else:
                config_dict = json.load(f)
        return MockConfig(**config_dict)

    def _load_recorded_mocks(self):
        path = Path("recorded_mocks.yaml")
        if not path.exists():
            return []
        with open(path) as f:
            return yaml.safe_load(f) or []

    def _save_recorded_mock(self, record):
        path = Path("recorded_mocks.yaml")
        all_records = self._load_recorded_mocks()
        all_records.append(record)
        with open(path, "w") as f:
            yaml.dump(all_records, f)

    def _find_recorded_mock(self, method, path, query):
        for rec in self.recorded_mocks:
            if rec["method"] == method and rec["path"] == path and rec["query"] == query:
                return rec
        return None

    def _setup_routes(self):
        registered = []
        
        def make_handler(route_config):
            async def handler(request: Request) -> Response:
                return await self._handle_route(request, route_config)
            return handler

        for route in self.config.routes:
            path = route.path
            if self.config.base_path:
                path = f"{self.config.base_path.rstrip('/')}/{path.lstrip('/')}"

            handler = make_handler(route)
            self.app.add_api_route(path, handler, methods=[route.method])
            registered.append((route.method, path))
        print("Registered routes:")
        for method, path in registered:
            print(f"  {method} {path}")

    def _add_catch_all(self):
        @self.app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
        async def catch_all(request: Request):
            return await self._handle_route(request, None)

    async def _handle_route(self, request: Request, route: RouteConfig) -> Response:
        if route is not None:
            if route.proxy:
                return await self._handle_proxy(request, route.proxy)
            if route.switch:
                return await self._handle_switch(request, route.switch)
            if route.response:
                return await self._handle_response(route.response)

        # Record + replay logic
        if self.record_mode and self.proxy_base_url:
            # Try to find a recorded mock
            method = request.method
            path = request.url.path
            query = str(request.url.query)
            rec = self._find_recorded_mock(method, path, query)
            if rec:
                return Response(
                    content=rec["response_body"],
                    status_code=rec["status"],
                    headers=rec.get("response_headers", {}),
                )
            # Proxy to real backend
            real_url = f"{self.proxy_base_url}{path}"
            if query:
                real_url += f"?{query}"
            async with httpx.AsyncClient() as client:
                proxy_response = await client.request(
                    method=method,
                    url=real_url,
                    headers=dict(request.headers),
                    content=await request.body(),
                )
            # Save the request/response pair
            record = {
                "method": method,
                "path": path,
                "query": query,
                "request_headers": dict(request.headers),
                "request_body": (await request.body()).decode("utf-8", errors="ignore"),
                "status": proxy_response.status_code,
                "response_headers": dict(proxy_response.headers),
                "response_body": proxy_response.text,
            }
            self._save_recorded_mock(record)
            self.recorded_mocks.append(record)
            return Response(
                content=proxy_response.content,
                status_code=proxy_response.status_code,
                headers=dict(proxy_response.headers),
            )
        return JSONResponse(
            status_code=404,
            content={"error": "No response configuration found"},
        )

    async def _handle_proxy(self, request: Request, proxy_url: str) -> Response:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=proxy_url,
                headers=dict(request.headers),
                params=dict(request.query_params),
                content=await request.body(),
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

    async def _handle_switch(
        self, request: Request, switch_config: Any
    ) -> Response:
        param = switch_config.param
        param_type = getattr(switch_config, "param_type", "path")
        cases = switch_config.cases
        default = getattr(switch_config, "default", None)

        param_value = None
        if param_type == "path":
            param_value = request.path_params.get(param)
        elif param_type == "query":
            param_value = request.query_params.get(param)
        elif param_type == "body":
            try:
                body = await request.json()
                param_value = body.get(param)
            except:
                pass
        elif param_type == "header":
            param_value = request.headers.get(param)
        else:
            # fallback to path
            param_value = request.path_params.get(param)

        if param_value in cases:
            return await self._handle_response(cases[param_value])
        elif default:
            return await self._handle_response(default)

        return JSONResponse(
            status_code=404,
            content={"error": f"No matching case found for {param}={param_value}"},
        )

    async def _handle_response(self, response_config: ResponseConfig) -> Response:
        if response_config.delay:
            await asyncio.sleep(response_config.delay / 1000)

        headers = dict(self.config.global_headers or {})
        if response_config.headers:
            headers.update(response_config.headers)

        if response_config.file:
            file_path = Path(response_config.file)
            if not file_path.exists():
                return JSONResponse(
                    status_code=500,
                    content={"error": f"File not found: {response_config.file}"},
                )
            with open(file_path) as f:
                content = f.read()
                return Response(
                    content=content,
                    status_code=response_config.status,
                    headers=headers,
                )

        # Render body with Jinja2/Faker if needed
        body = response_config.body or {}
        rendered_body = self._render_with_faker(body)
        return JSONResponse(
            content=rendered_body,
            status_code=response_config.status,
            headers=headers,
        )

    def _render_with_faker(self, data):
        """
        Recursively render all string values in data using Jinja2 with Faker context.
        """
        if isinstance(data, str):
            try:
                template = Template(data)
                return template.render(faker=self.faker)
            except Exception:
                return data
        elif isinstance(data, dict):
            return {k: self._render_with_faker(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._render_with_faker(item) for item in data]
        else:
            return data 