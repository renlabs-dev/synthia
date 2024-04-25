# Synthia

Welcome to the Synthia subnet, a bleeding-edge initiative to accelerate the open-source AI space. Our mission is to harness the power of Commune's decentralized incentive markets to produce a continuous stream of synthetic training data with verified quality at scale.

## Table of Contents

- [Synthia](#synthia)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Motivation](#motivation)
  - [Resources](#resources)
  - [Installation](#installation)
    - [Setup your environment](#setup-your-environment)
      - [With Nix](#with-nix)
      - [Manually, on Ubuntu 22.04](#manually-on-ubuntu-2204)
      - [With Docker](#with-docker)
        - [Operating with docker](#operating-with-docker)
  - [Running A Miner](#running-a-miner)
    - [Note](#note)
  - [Running A Validator](#running-a-validator)

## Overview

Synthia is utilizing the state-of-the-art Anthropic Claude3 API to generate open-ended high-quality and diverse synthetic in-depth explanations of subjects picked from the Opus latent space based on varying esotericity, with varying target-audience, level of detail and abstraction at scale.

While any model or API can theoretically mine in the subnet, the validation is designed to target Claude3-level quality, due to its substantially superior ability to generate the desired synthetic data. Hence, we advise mining with the Claude3 API, although support for OpenAI's API is available.

## Motivation

In the rapidly evolving world of artificial intelligence, synthetic data has emerged as a crucial component in the training of advanced models. By utilizing the state-of-the-art Anthropic Claude3 API, we can generate open-ended subject-unconstrained high-quality and diverse synthetic in-depth explanations.

Major AI labs have already recognized the potential of synthetic data and are actively utilizing it to enhance their models. However, access to such data remains limited for the broader open-source community. The Synthia subnet aims to change that.

By harnessing the power of Commune's decentralized crypto-economic incentives, we aim to create the largest reliably high-quality synthetic intelligence dataset in the world that will serve as a catalyst for innovation in the Open-Source AI space.

Join us on this important journey as we distill the Closed-Source intelligence right into the hands of the Open-Source Community!

## Resources

- You can check the HuggingFace leaderboard [here](https://huggingface.co/spaces/agicommies/synthia_subnet_leaderboard)!
- You can see the real-time dataset produced by Synthia [here](https://huggingface.co/datasets/agicommies/synthia)!

## Installation

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

#### Manually, on Ubuntu 22.04

- Install Python 3
  - `sudo apt install python3`
- [Install Poetry](https://python-poetry.org/docs/)
- Install the Python dependencies with `poetry install`
- **! IMPORTANT** Enter the Python environment with `poetry shell` 

#### With Docker
- [Install Docker](https://docs.docker.com/get-docker/)
- Run `docker pull ghcr.io/agicommies/synthia:0.2`
- Run `docker run -v ~/.commune:/root/.commune -it ghcr.io/agicommies/synthia:0.2`
- Run `poetry shell` to enter the enviroment
  
  ##### Operating with docker
  - You can quit docker with ctrl+d
  - You can pass enviroments variables to docker with `-e <VARIABLE>=<value>`.
  
    e.g `docker run -e ANTHROPIC_API_KEY=<your-anthropic-api-key> -v ~/.commune:/root/.commune -it ghcr.io/agicommies/synthia:0.2`


## Running A Miner

1. Get an API key from [Anthropic](https://console.anthropic.com/).

2. Create a file named `config.env` in the `env/` folder with the following
   contents (you can also see the `env/config.env.sample` as an example):

   ```sh
   ANTHROPIC_API_KEY="<your-anthropic-api-key>"
   ANTHROPIC_MODEL=claude-3-opus-20240229
   ANTHROPIC_MAX_TOKENS=1000
   ANTHROPIC_TEMPERATURE=0.5
   ```

   Alternatively, you can set up those values as enviroment variables.

3. Serve the miner:

   Make sure to be located in the root of synthia repository

   ```sh  
   cd synthia
   ```

   Proceed with running the miner:

   ```sh
   comx module serve synthia.miner.anthropic.AnthropicModule <your_commune_key> --subnets-whitelist <synthia netuid> --ip 0.0.0.0
   ```

   The **ip** is passed as **0.0.0.0** to accept **outside connections**, since the default,
   **127.0.0.1** accepts **only local** connections. Synthia has the **netuid 3**. Key is a name of your commune wallet/key.
   If you don't have a wallet, generate one by running

   ```bash
   comx key create <name>
   ```

   **Note**: you need to keep this process alive, running in the background. Some
   options are [tmux](https://www.tmux.org/](https://ioflood.com/blog/install-tmux-command-linux/)), [pm2](https://pm2.io/docs/plus/quick-start/) or [nohup](https://en.wikipedia.org/wiki/Nohup).

   Example using pm2

   ```bash
   pm2 start "comx module serve synthia.miner.anthropic.AnthropicModule <key> --subnets-whitelist <synthia netuid> --ip 0.0.0.0" --name <name>
   ```

4. Finally register the module on the Synthia subnet:

   ```sh
   comx module register <name> <your_commune_key> --ip <your-ip-address> --port <port> --netuid <synthia netuid>  
   ```

### Note

- Make sure to **serve and register** the module using the **same key**.
- If you are not sure about your `public ip` address:

   ```sh
   curl -4 https://ipinfo.io/ip
   ```

- Current `<synthia netuid>` is 3. If you want to check for yourself, you can run:

   ```sh
   comx subnet list
   ```

   And look for the name `synthia`

## Running A Validator

1. Get an API key from [Anthropic](https://console.anthropic.com/).
2. Gen an API key for embeddings from [OpenAi](https://openai.com/product)
3. Create a file named `config.env` in the `env/` folder with the following contents (you can also see the `env/config.env.sample` as an example):

   ```sh
   ANTHROPIC_API_KEY="<your-anthropic-claude-api-key>"
   ANTHROPIC_MODEL=claude-3-opus-20240229
   ANTHROPIC_MAX_TOKENS=1000
   ANTHROPIC_TEMPERATURE=0.5
   OPENAI_API_KEY="<your-openai-api-key>"
   ```
  
    Alternatively, you can set up those values as enviroment variables.
  

1. Register the validator

   Note that you are required to register the validator first, this is because the validator has to be on the network in order to set weights. You can do this by running the following command:

   ```sh
   comx module register <name> <your_commune_key> --netuid <synthia netuid>
   ```

   The current synthia **netuid** is **3**.

2. Serve the validator

   ```sh
   python3 -m synthia.cli <your_commune_key>
   ```

   Note: you need to keep this process alive, running in the background. Some options are [tmux](https://www.tmux.org/](https://ioflood.com/blog/install-tmux-command-linux/)), [pm2](https://pm2.io/docs/plus/quick-start/) or [nohup](https://en.wikipedia.org/wiki/Nohup).
