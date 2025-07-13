import httpx
from dataclasses import dataclass

@dataclass
class Provider:
    prefix: str
    domain: str

async def create_httpx_client(provider: Provider) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=f"https://{provider.prefix}.{provider.domain}")