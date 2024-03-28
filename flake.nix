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
          inherit system;
          config.allowUnfree = true;
        };

        p2n = poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };

        p2n-overrides = import ./nix/poetry2nix-overrides.nix {
          inherit pkgs p2n;
        };

        python_dependencies = [
          pkgs.python310
          pkgs.poetry
        ];

        runtime_dependencies = [
          # Node
          pkgs.nodejs_20
          pkgs.pm2
        ];

        dev_dependencies = [
          pkgs.ruff
        ];

        shellRc = ''
          # when this variable is set it's used as a new pm2 app name
          # https://discourse.nixos.org/t/environment-variables-set-by-nix/4133
          unset name
          root="$(git rev-parse --show-toplevel)"
          export PYTHONPATH="$root/src:$PYTHONPATH"
        '';

        shellRcNoPy = shellRc + ''
          export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:$LD_LIBRARY_PATH
        '';
      in
      rec {
        packages.synthia-py-app = p2n.mkPoetryApplication {
          projectDir = ./.;
          python = pkgs.python311;
          overrides = p2n-overrides;
        };

        devShells = rec {
          default = poetry;

          poetry = pkgs.mkShell {
            shellHook = shellRcNoPy;
            packages = python_dependencies ++ runtime_dependencies ++ dev_dependencies;
          };

          nixpy = pkgs.mkShell {
            shellHook = shellRc;
            packages = python_dependencies ++ runtime_dependencies ++ dev_dependencies;
            inputsFrom = [ packages.synthia-py-app.dependencyEnv ];
          };
        };

        packages.default = pkgs.buildEnv {
          name = "synthia";
          paths = runtime_dependencies ++ [
            packages.synthia-py-app.dependencyEnv
          ];
          pathsToLink = [ "/bin" ];
        };
      });
}