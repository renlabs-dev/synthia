from synthia.validator.text_validator import TextValidator
from synthia.validator._config import ValidatorSettings
from communex.compat.key import classic_load_key
from communex._common import get_node_url
from communex.client import CommuneClient

async def test_text_validator():
    key = classic_load_key("dev01")

    node_url = get_node_url()
    com_client = CommuneClient(node_url)
    validator = TextValidator(key,3, com_client)
    val_dataset = validator._get_validation_dataset(ValidatorSettings(), 1)[0] #type: ignore
    ip_port = ["127.0.0.1", "8000"]
    target_ss58 = ""
    miner_info = (ip_port, target_ss58)
    answer = await validator._get_miner_prediction(val_dataset, miner_info) # type: ignore
    print(answer)
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_text_validator())