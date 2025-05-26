from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl


class ResponseConfig(BaseModel):
    status: int = 200
    body: Optional[Union[Dict[str, Any], List[Any]]] = None
    file: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    delay: Optional[int] = Field(None, description="Delay in milliseconds")


class SwitchCase(BaseModel):
    param: str
    param_type: str = "path"  # can be 'path', 'query', 'body', 'header'
    cases: Dict[str, ResponseConfig]
    default: Optional[ResponseConfig] = None


class RouteConfig(BaseModel):
    path: str
    method: str
    response: Optional[ResponseConfig] = None
    switch: Optional[SwitchCase] = None
    proxy: Optional[HttpUrl] = None


class MockConfig(BaseModel):
    global_headers: Optional[Dict[str, str]] = None
    base_path: Optional[str] = None
    routes: List[RouteConfig] 