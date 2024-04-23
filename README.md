# Synthia

Welcome to the Synthia subnet, a bleeding edge initiative to accelerate the
open-source AI space. Our mission is to harness the power of Commune's
decentralized incentive markets to produce synthetic training data with verified
quality at web-scale. You can check the HuggingFace leaderboard
[here][synthia_subnet_leaderboard]!

[synthia_subnet_leaderboard]:
    https://huggingface.co/spaces/agicommies/synthia_subnet_leaderboard

In the rapidly evolving world of artificial intelligence, synthetic data has
emerged as a crucial component in the training of advanced models. By utilizing
the state-of-the-art Anthropic Claude3 API, we can generate open-ended
subject-unconstrained high-quality and diverse synthetic in-depth explanations.
While any model or API can theoretically mine in the subnet, the validation is
designed to target Claude3-level quality, due to its substantially superior
ability to generate the desired synthetic data. Hence we advise mining with the
Claude3 API, although support for OpenAI's API is available.

Major AI labs have already recognized the potential of synthetic data and are
actively utilizing it to enhance their models. However, access to such data
remains limited for the broader open-source community. The Synthia subnet aims
to change that.

By harnessing the power of Commune's decentralized crypto-economic incentives we
aim to create the largest reliably high-quality synthetic intelligence dataset
in the world that will serve as a catalyst for innovation in the Open-Source AI
space. Join us on this important journey as we distill the Closed-Source
intelligence right into the hands of the Open-Source Community!

##  Installation

### Setup your environment

#### With Nix

- Install Nix with [install.determinate.systems]
- You can enter the nix shell environment with with `nix develop` or setup
  [direnv](https://direnv.net/) to automatically load the environment when you
  enter the directory.
- Install the Python dependencies with `poetry install`
- Get into the Python environment:
  - If you are using `direnv`, just re-entering the directory will do the trick.
    - Tip: you can force-reload with `direnv reload`
  - If not, you can run `poetry shell` to enter the Python environment.

[install.determinate.systems]: https://install.determinate.systems/

#### or manually, on Ubuntu 22.04

- Install Python 3
  - `sudo apt install python3`
- [Install Poetry](https://python-poetry.org/docs/)
- Install the Python dependencies with `poetry install`
- Enter the Python environment with `poetry shell`

## Running the Miner

1. Get an API key from [Anthropic](https://console.anthropic.com/).

2. Create a file named `config.env` in the `env/` folder with the following
   contents:

   ```sh
   ANTHROPIC_API_KEY="<your-api-key>"
   ANTHROPIC_MODEL=claude-3-opus-20240229
   ANTHROPIC_MAX_TOKENS=1000
   ANTHROPIC_TEMPERATURE=0.5
   ```

3. Serve the miner:

   ```sh
   comx module serve synthia.miner.anthropic.AnthropicModule <key> --subnets-whitelist <synthia netuid> --ip 0.0.0.0
   ```

   The ip is passed as 0.0.0.0 to accept outside connections, since the default,
   127.0.0.1 accepts only local connections.

   Note: you need to keep this process alive, running in the background. One
   option is to use [tmux](https://www.tmux.org/) or [nohup](https://en.wikipedia.org/wiki/Nohup).

4. Register the module on the Synthia subnet:

   ```sh
   comx module register <name> <public-ip> <port> <key> <synthia netuid>
   ```

### Note

- Make sure to serve and register the module with the same key.
- If you are not sure about your `public ip` address:

   ```sh
   curl -4 https://ipinfo.io/ip
   ```

- If you are not sure about the `synthia netuid` number:

   ```sh
   comx subnet list
   ```

   Look for the name `synthia` and copy the netuid number.

## Running A Validator

```sh
python3 -m synthia.cli <your_anthropic_key> <your_commune_key>
```
