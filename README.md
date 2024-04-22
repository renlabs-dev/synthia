# Synthia
> Commune synthetic data generation subnet, this subnet is planned to be released shortly after the incentives v1 "Coherence" update (incoming blockchain version 1.3.0)

Welcome to the Synthia subnet, a bleeding edge initiative to accelerate the open-source AI space. Our mission is to harness the power of Commune's decentralized incentive markets to produce synthetic training data with verified quality at web-scale.

In the rapidly evolving world of artificial intelligence, synthetic data has emerged as a crucial component in the training of advanced models. By utilizing the state-of-the-art Anthropic Claude3 API, we can generate open-ended subject-unconstrained high-quality and diverse synthetic in-depth explanations. While any model or API can theoretically mine in the subnet, the validation is designed to target Claude3-level quality, due to its substantially superior ability to generate the desired synthetic data. Hence we advise mining with the Claude3 API, although support for OpenAI's API is available.

Major AI labs have already recognized the potential of synthetic data and are actively utilizing it to enhance their models. However, access to such data remains limited for the broader open-source community. The Synthia subnet aims to change that.

By harnessing the power of Commune's decentralized cryptoeconomic incentives we aim to create the largest reliably high-quality synthetic intelligence dataset in the world that will serve as a catalyst for innovation in the Open-Source AI space. Join us on this important journey as we distill the Closed-Source intelligence right into the hands of the Open-Source Community!

## Running Miner

1. Get an API key from Anthropic Claude (https://console.anthropic.com/).

2. Create a file named `config.env` in the `env` folder with the following content:

   ```
   ANTHROPIC_API_KEY=<your-api-key>
   ANTHROPIC_MODEL=claude-3-opus-20240229
   ANTHROPIC_MAX_TOKENS=1000
   ANTHROPIC_TEMPERATURE=0.5
   ```

3. Serve the miner:

   For Anthropic:
   ```bash
   comx module serve synthia.miner.anthropic.AnthropicModule <key> --subnets-whitelist <synthia netuid> --ip 0.0.0.0
   ```

    For OpenAI:
   ```bash
   comx module serve synthia.miner.openai.OpenAIModule <key> --subnets-whitelist <synthia netuid> --ip 0.0.0.0
   ```
   
   The ip is passed as 0.0.0.0 to accept outside connections, since the default,
   127.0.0.1 accepts only local connections.

5. Register the module on the Synthia subnet:

   ```bash
   comx module register <name> <public-ip> <port> <key> <synthia netuid>
   ```

### Note

- Make sure to serve and register the module with the same key.
- If you are not sure about your `public ip` address: 

   ```bash
   curl -4 https://ipinfo.io/ip
   ```

- If you are not sure about the `synthia netuid` number:

   ```bash
   comx subnet list
   ```

   Look for the name `synthia` and copy the netuid number.

## Running A Validator
To run a validator, simply execute `python3 -m synthia.cli <your_anthropic_key> <your_commune_key>`
