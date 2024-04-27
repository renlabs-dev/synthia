#!/bin/bash

# MIT License - Copyright (c) 2023 Bakobiibizo (https://github.com/bakobiibizo)

set -e

burn_fee=2.5
source_miner="src/synthia/miner/anthropic.py"
source_validator="src/synthia/validator/text_validator.py"

# Install Synthia
install_synthia() {
    # Downloading synthia
    echo "Installing Synthia"
    git clone https://github.com/agicommies/synthia.git
    cd synthia || exit

    if [ ! -x "/usr/bin/python3" ]; then
        echo "Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi
    if [ ! -x "/usr/bin/pip3" ]; then
        echo "Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi

    # Setting up virtual environment
    python3 -m venv .venv
    # shellcheck source=/dev/null
    source ".venv/bin/activate"
    python3 -m pip install --upgrade pip
    pip3 install setuptools wheel gnureadline

    # Installing poetry and setting up shell
    # shellcheck disable=SC2162
    curl -sSL https://install.python-poetry.org | python3 -
    echo "PATH=~/.local/share/pypoetry/venv/bin/poetry:$PATH" >>~/.bashrc
    echo "PATH=~/.local/bin:$PATH" >>~/.bashrc
    # shellcheck source=/dev/null
    source ~/.bashrc
    # shellcheck source=/dev/null
    source .venv/bin/activate

    # Installing dependencies
    poetry install

    # Installing synthia
    poetry run pip3 install -e .

    # Installing communex
    poetry run pip3 install --upgrade communex
    echo "Synthia installed."
}

# Sets up the environment for the miner or validator
create_setup() {
    echo "This will walk you through configuring your setup to launch miners and validators on CommuneAI."
    echo "The instillation will only work on Linux. If you are on Windows, please refer to the Synthia readme for instructions."
    echo "https://github.com/agicommies/synthia/blob/main/README.md"
    # shellcheck disable=SC2162
    read -p "Install Synthia (y/n): " install_synthia
    if [ "$install_synthia" = "y" ]; then
        install_synthia
    fi

    echo "Setting up environment"
    cat <<'EOF' >ecosystem.config.js
    module.exports = {
    apps: [
        {
            name: `${process.env.MODULE_KEYNAME}`,
            script: 'src/synthia/cli.py',
            interpreter: 'python3',
            args: process.env.MODULE_PATH,  // Using environment variable
            watch: true,
            env: {
                MODULE_ENV: 'development',
                MODULE_PATH: `${process.env.MODULE_PATH}`, // Default path that can be overridden
            }
        },
        {
            name: `${process.env.MODULE_KEYNAME}`,
            script: 'comx',
            # shellcheck disable:=SC2162
    
    args: `module serve --ip "${process.env.MODULE_IP}" --port "${process.env.MODULE_PORT}" --subnets-whitelist "${process.env.MODULE_NETUID}" "synthia.miner.${process.env.MODULE_PATH}" "${process.env.MODULE_KEYNAME}"`,
            watch: true,
            env: {
                MODULE_ENV: 'development',
                MODULE_IP: '0.0.0.0', // Default IP
                MODULE_PORT: '8000',    // Default Port
                MODULE_NETUID: '3',   // Default Netuid
                MODULE_PATH: 'anthropic.AnthropicModule',
                MODULE_KEYNAME: 'module',
                MODULE_STAKE: '300'
            }
        }
    ]
};
EOF
    echo "An config file has been created in ecosystem.config.js to facilitate pm2. You do not need to edit this file."
    cp env/config.env.sample env/config.env
    echo "An environment file has been created in env/config.env. For your miner and validators to function you need an OpenAI API key and Anthropic API key."
    echo "OpenAI API key: https://platform.openai.com/api-keys"
    echo "Anthropic API key: https://console.anthropic.com/settings/keys"
    echo Setup complete.
}

# Configures the module launch
configure_launch() {
    # Enter the path of the module
    echo "The module path in the format of \"filename.ClassName\" (eg. anthropic.AnthropicModule)"
    # shellcheck disable=SC2162
    read -p "Module Path: " module_path

    # Check if the module path is valid
    if [ "$module_path" = "" ]; then
        echo "Error, must provide a valid module path."
        # shellcheck disable=SC2162
        read -p "Module Path: " module_path
    elif [ -z "$module_path" ]; then
        echo "Error, must provide a valid module path."
        exit 1
    fi

    # Extract the filename and classname
    filename="${module_path%%.*}"
    classname="${module_path#*.}"

    echo "Checking file path"
    # Create the miner module if it doesn't exist
    if [ "$is_miner" = "true" ]; then
        if [ ! -f "src/synthia/miner/$filename.py" ]; then
            # Copy the source miner file to the destination
            destination_file="src/synthia/miner/$filename.py"
            cp "$source_miner" "$destination_file"
            # Replace the class name in the destination file
            sed -i "s/AnthropicModule/$classname/g" "$destination_file"
            echo "Miner module created at src/synthia/miner/$filename.py"
        fi
    fi

    # Create the validator module if it doesn't exist
    if [ "$is_validator" = "true" ]; then
        if [ ! -f "src/synthia/validator/$filename.py" ]; then
            # Copy the source validator file to the destination
            destination_file="src/synthia/validator/$filename.py"
            cp "$source_validator" "$destination_file"
            # Replace the class name in the destination file
            sed -i "s/TextValidator/$classname/g" "$destination_file"
            echo "Validator module created at src/synthia/validator/$filename.py"
        fi
    fi
    echo "Module path exists"
    echo ""

    # Enter the name of the key that will be used to stake the validator
    echo "The name of the key that will be used to stake the validator. Defaults to Module Path ($module_path) if not provided."
    # shellcheck disable=SC2162
    read -p "Module key name: " key_name
    if [ "$key_name" = "" ]; then
        key_name=$module_path
    fi
    echo "Module key name: $key_name"
    echo ""

    # Select if the key needs to be created
    echo "You can create a key if it does not exist."
    # shellcheck disable=SC2162
    read -p "Create key (y/n): " createkey
    if [ "$createkey" = "y" ]; then
        create_key
    fi
    echo "Key name: $key_name"
    echo ""

    # Select if a balance needs to be transfered to the key
    echo "You can transfer a balance to another key."
    echo "If you have created a key during the registration process then the transfer reciepent will be the new key."
    echo "The sending key must be in the ~/.commune/key folder with enough com to transfer."
    # shellcheck disable=SC2162
    read -p "Transfer balance (y/n): " transfer_balance
    if [ "$transfer_balance" = "y" ]; then
        transfer_balance
    fi
    echo ""

    # Enter the IP and port of the module
    # shellcheck disable=SC2162
    read -p "Module IP address (default 0.0.0.0): " ip_address
    if [ "$ip_address" = "" ]; then
        ip_address="0.0.0.0"
    fi
    echo "Module IP address: $ip_address"
    echo ""

    # Enter the port of the module
    # shellcheck disable=SC2162
    read -p "Module port(default 8000) int: " port
    if [ "$port" = "" ]; then
        port=8000
    fi
    echo "Module port: $port"
    echo ""

    # Enter the netuid of the module
    # shellcheck disable=SC2162
    read -p "Deploying to subnet (default 3): int: " netuid
    if [ -z "$netuid" ]; then
        netuid=3
    fi
    echo "Module netuid: $netuid"
    echo ""

    # Check if the module needs to be staked
    if [ "$needs_stake" = "true" ]; then
        echo "Set the stake. This is the amount of tokens that will be staked by the module."
        echo "Validators require a balance of 5200, not including fees, to vote."
        echo "Miners require a balance of 256, not including fees, to mine."
        echo "$burn_fee com will be burned as a fee to stake."
        # shellcheck disable=SC2162
        read -p "Set stake: " stake
        echo "Setting stake: $stake"
        echo ""
    fi

    # Enter the delegation fee
    if [ "$is_update" = "true" ]; then
        echo "Set the delegation fee. This the percentage of the emission that are collected as a fee to delegate the staked votes to the module."
        # shellcheck disable=SC2162
        read -p "Delegation fee (default 20) int: " delegation_fee
        echo ""
    fi

    # Check it is above minimum
    if [ "$delegation_fee" -lt 5 ] || [ -z "$delegation_fee" ]; then
        echo "Minimum delegation fee is 5%. Setting to 5%"
        delegation_fee=5
        echo "Module delegation fee: $delegation_fee"
        echo ""
    fi

    # Enter the metadata
    if [ "$is_update" = "true" ]; then
        echo "Set the metadata. This is an optional field."
        echo "It is a JSON object that is passed to the module in the format:"
        echo "{\"key\": \"value\"}."
        # shellcheck disable=SC2162

        read -p "Add metadata (y/n): " choose_metadata
        if [ "$choose_metadata" = "y" ]; then
            # shellcheck disable=SC2162
            read -p "Enter metadata object: " metadata
            echo "Module metadata: $metadata"
        fi
        echo ""
    fi

    # Confirm settings
    echo "Confirm module settings:"
    echo "Module path:        $module_path"
    echo "Module IP address:  $ip_address"
    echo "Module port:        $port"
    echo "Module netuid:      $netuid"
    echo "Module key name:    $key_name"
    if [ "$needs_stake" = "true" ]; then
        echo "Module stake:   $stake"
    fi
    if [ "$is_update" = "true" ]; then
        echo "Delegation fee: $delegation_fee"
        echo "Metadata:       $metadata"
    fi
    # shellcheck disable=SC2162
    read -p "Confirm settings (y/n): " confirm
    if [ "$confirm" = "y" ]; then
        echo "Deploying..."
        echo ""
    else
        echo "Aborting..."
        exit 1
    fi

    # Export the variables for use in ecosystem.config.js. This allows us to use pm2 in the bash script.
    export MODULE_PATH="$module_path"
    export MODULE_IP="$ip_address"
    export MODULE_PORT="$port"
    export MODULE_NETUID="$netuid"
    export MODULE_KEYNAME="$key_name"
    export MODULE_STAKE="$stake"
    export MODULE_DELEGATION_FEE="$delegation_fee"
    export MODULE_METADATA="$metadata"
}

# Function to create a key
create_key() {
    echo "Creating key"
    echo "This creates a json key in ~/.commune/key with the given name."
    echo "Once you create the key you will want to save the mnemonic somewhere safe."
    echo "The mnemonic is the only way to recover your key if it lost then the key is unrecoverable."
    echo "Note that commune does not encrypt the key file so do not fund a key on an unsafe machine."
    if [ -z "$key_name" ]; then
        # shellcheck disable=SC2162
        read -p "Key name: " key_name
    fi
    comx key create "$key_name"
    echo "This is your key. Save the mnemonic somewhere safe."
    cat ~/.commune/key/"$key_name".json
    echo "$key_name created and saved at ~/.commune/key/$key_name.json"
}

# Function to perform a balance transfer
transfer_balance() {
    echo "Initiating Balance Transfer"
    echo "There is a 2.5 com fee on the balance of the transfer."
    echo "Example: 300 com transfered will arrive as 297.5 com"
    # shellcheck disable=SC2162
    read -p "From Key (sender): " key_from
    # shellcheck disable=SC2162
    read -p "Amount to Transfer: " amount
    if [ -z "$key_name" ]; then
        # shellcheck disable=SC2162
        read -p "To Key (recipient): " key_to
    else
        key_to="$key_name"
    fi
    comx balance transfer "$key_from" "$amount" "$key_to"
    echo "Transfer of $amount from $key_from to $key_to initiated."
}

# Function to serve a miner
serve_miner() {
    echo "Serving Miner"
    pm2 start "comx module serve synthia.miner.$module_path ${key_name} --ip  $ip_address --port $port --subnets-whitelist $netuid" --name "$module_path"
    echo "Miner served."
}

# Function to register a miner
register_miner() {
    echo "Registering Miner"
    comx module register "$module_path" "$key_name" --netuid "$netuid" --stake "$stake"
    echo "Miner registered."
}

# Function to deploy a miner
deploy_miner() {
    echo "Registering Miner"
    register_miner
    echo "Serving Miner."
    serve_miner
    echo "Miner deployed."
}

# Function to serve a validator
serve_validator() {
    echo "Serving Validator"
    pm2 start "python -m synthia.cli $module_path"
    echo "Validator served."
}

# Function to register a validator
register_validator() {
    echo "Registering Validator"
    comx module register "$module_path" "$key_name" --netuid "$netuid" --stake "$stake"
    echo "Validator registered."
}

# Function to deploy a validator
deploy_validator() {
    echo "Serving Validator"
    serve_validator
    echo "Registering Validator"
    register_validator
    echo "Validator deployed."
}

# Function to update a module
update_module() {
    echo "Updating Module"
    # This will update the metadata, netuid, and/or delegation fee.
    if [ -z "$netuid" ] && [ -z "$delegation_fee" ] && [ -z "$metadata" ]; then
        comx module update "$module_path" "$key_name" "$ip_address" "$port"
    elif [ -z "$netuid" ]; then
        comx module update "$module_path" "$key_name" "$ip_address" "$port" --metadata "$metadata" --delegation-fee "$delegation_fee"
    elif [ -z "$metadata" ]; then
        comx module update "$module_path" "$key_name" "$ip_address" "$port" --netuid "$netuid" --delegation-fee "$delegation_fee"
    elif [ -z "$delegation_fee" ]; then
        comx module update "$module_path" "$key_name" "$ip_address" "$port" --netuid "$netuid" --metadata "$metadata"
    elif [ -z "$metadata" ] && [ -z "$netuid" ]; then
        comx module update "$module_path" "$key_name" "$ip_address" "$port" --delegation-fee "$delegation_fee"
    elif [ -z "$netuid" ] && [ -z "$delegation_fee" ]; then
        comx module update "$module_path" "$key_name" "$ip_address" "$port" --metadata "$metadata"
    else
        comx module update "$module_path" "$key_name" "$ip_address" "$port" --netuid "$netuid" --metadata "$metadata" --delegation-fee "$delegation_fee"
    fi
    echo "Module updated."
}

if [ "$1" = "--setup" ]; then
    create_setup
fi

echo "Choose your deployment:"
echo "1. Fully Deploy Validator"
echo "2. Fully Deploy Miner"
echo "3. Fully Deploy Both"
echo "4. Register Validator"
echo "5. Register Miner"
echo "6. Serve Validator"
echo "7. Serve Miner"
echo "8. Update Module"
echo "9. Transfer Balance"
echo "10. Create Key"
# shellcheck disable=SC2162
read -p "Choose an action " choice
echo ""

case "$choice" in
1)
    echo "Validator Configuration"
    is_validator=true
    needs_stake=true
    is_update=true
    configure_launch
    deploy_validator
    ;;
2)
    echo "Miner Configuration"
    is_miner=true
    needs_stake=true
    is_update=true
    configure_launch
    deploy_miner
    ;;
3)
    echo "Validator Configuration"
    is_validator=true
    needs_stake=true
    is_update=true
    configure_launch
    deploy_validator
    echo "Miner Configuration"
    is_validator=false
    is_miner=true
    needs_stake=true
    is_update=true
    configure_launch
    deploy_miner
    ;;
4)
    echo "Validator Configuration"
    is_validator=true
    needs_stake=true
    is_update=true
    configure_launch
    register_validator
    ;;
5)
    echo "Miner Configuration"
    is_miner=true
    needs_stake=true
    is_update=true
    configure_launch
    register_miner
    ;;
6)
    echo "Validator Configuration"
    is_validator=true
    configure_launch
    serve_validator
    ;;
7)
    echo "Miner Configuration"
    is_miner=true
    configure_launch
    serve_miner
    ;;
8)
    echo "Module Configuration"
    is_update=true
    configure_launch
    update_module
    ;;
9)
    transfer_balance
    ;;
10)
    create_key
    ;;
*)
    echo "Invalid choice"
    exit 1
    ;;
esac

echo "Deployment complete."
