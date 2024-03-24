from communex.module.module import Module # type: ignore
from communex.client import CommuneClient # type: ignore

class TextValidator(Module):
    def __init__(self) -> None:
        super().__init__()
        self.node_url = "wss://commune.api.onfinality.io/public-ws"
        self.client = CommuneClient(url=self.node_url)

    def get_synthia_netuid(self, client: CommuneClient):
        """
        Retrives the netuid of the synthia subnet 
        """
        pass

    def get_modules(self, client: CommuneClient):
        """
        Retrives all modules from the subnet
        """
        pass