from communex.compat.key import classic_load_key # type: ignore
from communex.module.client import ModuleClient # type: ignore
import asyncio

if __name__ == "__main__":
    from communex.compat.key import classic_load_key # type: ignore
    keypair = classic_load_key("t6")
    client = ModuleClient("localhost", 8000, keypair)
    result = asyncio.run(client.call("generate", {"prompt": "what's the meaning of life?"}))
    print(result)