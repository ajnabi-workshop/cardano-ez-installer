import os
import shutil
from typing import NoReturn

from .config_vars import ConfigVars
from .utils import ind, print_neutral, print_success_generic, run, run_quiet
from .paths import Network, NetworkPaths, Paths


def install_node(cfg: ConfigVars) -> None | NoReturn:
    original_cwd = os.getcwd()
    print_neutral(f"\n{ind('Installing cardano-node...')}")

    os.chdir(cfg['CARDANO_SRC_PATH'])

    if not os.path.exists("cardano-node"):
        run_quiet(
            ["git", "clone", "https://github.com/input-output-hk/cardano-node"],
            "Error cloning cardano-node repository")
        os.chdir("cardano-node")
    else:
        os.chdir("cardano-node")
        run_quiet(
            ["git", "fetch"],
            "Error fetching cardano-node repository")

    run_quiet(
        ["git", "reset", "--hard", cfg['NODE_RELEASE']],
        f"Error resetting git to release {cfg['NODE_RELEASE']}")

    run_quiet(
        ["nix", "profile", "remove", ".*cardano-node*"],
        "Error removing cardano-node from nix profile")
    run(
        ["nix", "profile", "install", "--accept-flake-config",
         "--extra-substituters", "https://cache.zw3rk.com",
         "--extra-trusted-public-keys",
         "loony-tools:pr9m4BkM/5/eSTZlkQyRt57Jz7OMBxNSUiMC4FkcNfk=",
         ".#cardano-node"],
        "Error installing cardano-node")

    print_success_generic()

    print_neutral(ind("Installing cardano-cli..."))

    run_quiet(
        ["nix", "profile", "remove", ".*cardano-cli*"],
        "Error removing cardano-cli from nix profile")
    run(
        ["nix", "profile", "install", "--accept-flake-config",
         "--extra-substituters", "https://cache.zw3rk.com",
         "--extra-trusted-public-keys",
         "loony-tools:pr9m4BkM/5/eSTZlkQyRt57Jz7OMBxNSUiMC4FkcNfk=",
         "--no-warn-dirty", ".#cardano-cli"],
        "Error installing cardano-cli")

    print_success_generic()

    os.chdir(original_cwd)


def prompt_install_ogmios(cfg: ConfigVars) -> None | NoReturn:
    while True:
        user_input = input("Do you want to install Ogmios? (Y/N): ").lower()
        print("")

        if user_input == 'y':
            install_ogmios(cfg)
            break
        elif user_input == 'n':
            break
        else:
            print("Invalid response. Please enter 'Y' to install or 'N' to cancel.")
            continue


def install_ogmios(cfg: ConfigVars) -> None | NoReturn:
    original_cwd = os.getcwd()
    ogmios_src_path = f"{cfg['CARDANO_SRC_PATH']}/ogmios"
    print_neutral(ind('Installing ogmios...'))

    if not os.path.exists(ogmios_src_path):
        os.chdir(cfg['CARDANO_SRC_PATH'])
        run_quiet(
            ["git", "clone", "https://github.com/CardanoSolutions/ogmios"],
            "Error cloning ogmios repository")
        os.chdir(ogmios_src_path)
    else:
        os.chdir(ogmios_src_path)
        run_quiet(
            ["git", "fetch"],
            "Error fetching ogmios repository")

    release = f"v{cfg['OGMIOS_RELEASE']}"

    run_quiet(
        ["git", "reset", "--hard", release],
        f"Error resetting git to release {release}")

    ogmios_server_path = f"{ogmios_src_path}/server"

    for ogmios_asset in ["flake.nix", "cabal.project.local"]:
        ez_installer_path = os.path.dirname(
            os.path.dirname(os.path.realpath(__file__)))
        source_path = os.path.join(
            ez_installer_path, "ogmios-assets", ogmios_asset)
        shutil.copy(
            source_path,
            f"{ogmios_server_path}/{ogmios_asset}")

    for dirpath, _, filenames in os.walk(ogmios_server_path):
        for filename in filenames:
            if filename == 'package.yaml':
                os.remove(os.path.join(dirpath, filename))

    os.chdir(ogmios_src_path)
    run_quiet(
        ["git", "add", "."],
        f"Error staging ogmios changes")

    run_quiet(
        ["git", "add", "-f", "server/cabal.project.local"],
        f"Error staging ogmios cabal.project.local file")

    os.chdir(ogmios_server_path)

    run_quiet(
        ["nix", "flake", "lock"],
        f"Error creating flake.lock file")

    run_quiet(
        ["nix", "profile", "remove", ".*ogmios*"],
        "Error removing ogmios from nix profile")
    run(
        ["nix", "profile", "install", "--accept-flake-config",
         "--no-warn-dirty", ".#ogmios"],
        "Error installing ogmios")

    print_success_generic()
    os.chdir(original_cwd)


def download_node_configs(
        paths: Paths) -> None | NoReturn:
    print_neutral(ind("Downloading node config files..."))
    config_files = [
        "config",
        "db-sync-config",
        "submit-api-config",
        "topology",
        "alonzo-genesis",
        "byron-genesis",
        "conway-genesis",
        "shelley-genesis",
    ]
    for net in Network:
        network_paths: NetworkPaths = getattr(paths, net.value)
        config_path = network_paths.config
        os.chdir(config_path)
        config_src = f"https://book.world.dev.cardano.org/environments/{net.value}"

        for file in config_files:
            run_quiet(
                ["curl", "-O", "-J", f"{config_src}/{file}.json"],
                f"Error downloading '{file}.json'")

    print_success_generic()
