{
  description = "Synthetic data generation subnet";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=23.11";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          system = system;
          config.allowUnfree = true;
        };
        p2n = poetry2nix.lib.mkPoetry2Nix {
          inherit pkgs;
        };
        p2n-overrides = import ./nix/poetry2nix-overrides.nix {
          inherit pkgs p2n;
        };

        shellrc = ''
          # when this variable is set it's used as a new pm2 app name
          # https://discourse.nixos.org/t/environment-variables-set-by-nix/4133
          unset name

          #root="$(git rev-parse --show-toplevel)"
          #export PYTHONPATH="$root/src:$PYTHONPATH"
        '';

        shellrc_nopy = shellrc + ''
          export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:$LD_LIBRARY_PATH
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          shellHook = shellrc_nopy;
          buildInputs = [
            pkgs.python310
            pkgs.poetry
            pkgs.ruff
          ];
        };
        packages = rec {
          synthia = p2n.mkPoetryApplication {
            projectDir = ./.;
            python = pkgs.python311;
            overrides = p2n-overrides;
          };
          default = synthia;
        };
      });
}
