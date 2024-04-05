from communex.client import CommuneClient  # type: ignore
from communex.compat.key import classic_load_key  # type: ignore


client = CommuneClient("wss://testnet-commune-api-node-0.communeai.net")


num_votes = 120
uids = [i + 1 for i in range(0, num_votes)]
weights = [1 for _ in range(num_votes)]
key = classic_load_key("callit")

print(client.vote(key=key, uids=uids, weights=weights, netuid=0))