# Synthia

Welcome to the Synthia subnet, a bleeding edge initiative to accelerate the open-source AI space. Our mission is to harness the power of decentralized cryptoeconomics to produce synthetic training data with verified quality at mega-scale.

In the rapidly evolving world of artificial intelligence, synthetic data has emerged as a crucial component in the training of advanced models. By utilizing state-of-the-art APIs like OpenAI (GPT4) and Anthropic (Claude3) we can generate high-quality and diverse synthetic prompt-response pairs.

Major AI labs have already recognized the potential of synthetic data and are actively utilizing it to enhance their models. However, access to such data remains limited for the broader open-source community. This is where the Synthia subnet comes in.

By harnessing the power of Commune’s decentralized cryptoeconomic incentives we aim to create the largest reliably high-quality synthetic intelligence dataset in the world that will serve as a catalyst for innovation in the Open-Source AI space.

Join us on this important journey as we distill the Closed-Source intelligence right into the hands of the Open-Source Community!

# WIP

Commune synthetic data generation subnet, this subnet is planned to be released shortly after incentive update (incoming blockchain version 1.3.0)

- [ ] Implement Synthia Validator

  - [ ] Miner communication
  - [ ] Dataset generation
  - [ ] Data storage
  - [ ] Decentralized database setup
  - [ ] Data validation
  - [ ] Data retrieval

- [ ] Implement Synthia Miner
  - [ ] Claude / Openai / Gemini API support

## Running Miner

1. Get an API key from OpenAI or Claude.

2. Create a file named `config.env` in the `env` folder with the following content:

   ```
   OPENAI_API_KEY=your-api-key
   OPENAI_MODEL=gpt-3.5-turbo
   OPENAI_MAX_TOKENS=100
   OPENAI_TEMPERATURE=1.
   ```

3. Serve the miner:

   For OpenAI:
   ```bash
   comx module serve synthia.miner.openai.OpenAIModule <key> --subnets-whitelist <synthia netuid>
   ```

   For Anthropic:
   ```bash
   comx module serve synthia.miner.anthropic.AnthropicModule <key> --subnets-whitelist <synthia netuid>
   ```

4. Register the module on the Synthia subnet:

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
WIP
