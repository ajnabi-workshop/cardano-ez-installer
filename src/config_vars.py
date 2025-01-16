import json
import os
import sys
import urllib.request
from typing import Callable, NoReturn, TypedDict

from .utils import ind, ind2, print_fail, print_neutral, print_success


ConfigVars = TypedDict('ConfigVars', {
    'NODE_RELEASE': str,
    'AIKEN_RELEASE': str,
    'CARDANO_PATH': str,
    'CARDANO_SRC_PATH': str
})


def get_var(var: str, validate: Callable[[str],
                                         str | None]) -> tuple[str | None, str |
                                                               None]:
    val = os.environ.get(var)
    if not val:
        return (None, "not exported in .env")
    err = validate(val)
    return (val if not err else None, err)


def check_release_var(org: str, repo: str, release: str) -> str | None:
    tags_url = f"https://api.github.com/repos/{org}/{repo}/releases"
    req = urllib.request.Request(tags_url)
    req.add_header("User-Agent", "Mozilla/5.0")

    try:
        with urllib.request.urlopen(req) as response:
            data = response.read().decode()
            releases = json.loads(data)
            tags = [release["tag_name"] for release in releases]
            err = None if release in tags else f"{release} is not a valid tag."

            return err

    except Exception as e:
        error_message = f"An error occurred with call to GitHub API: {e}"
        return error_message


def check_node_release_var(release: str) -> str | None:
    check_release_var("input-output-hk", "cardano-node", release)


def check_aiken_release_var(release: str) -> str | None:
    # aiken prefixes release tags with 'v' (but we omit this in .env)
    check_release_var("aiken-lang", "aiken", f"v{release}")




def check_path_var(val: str) -> str | None:
    if not os.path.exists(val):
        try:
            os.mkdir(val)
        except OSError as e:
            return (f"unable to create directory ({e})")
    return None


def make_cfg() -> ConfigVars | NoReturn:
    print_neutral(f'\n{ind("Checking .env variables...")}')
    var_checks = {
        'NODE_RELEASE': check_node_release_var,
        'AIKEN_RELEASE': check_aiken_release_var,
        'CARDANO_SRC_PATH': check_path_var,
        'CARDANO_PATH': check_path_var,
    }
    cfg = {}
    all_valid = True
    for var, validate in var_checks.items():
        val, err = get_var(var, validate)
        if val:
            print_success(ind2(f"* {var}: PASSED"))
            cfg[var] = val
        else:
            print_fail(ind(f"{var}: {err}"))
            all_valid = False

    if not all_valid:
        print_fail(
            f'\n{ind(".env variables error: correct the issue(s) above and try again (See README for help).")}\n')
        sys.exit(1)

    return {
        'NODE_RELEASE': cfg['NODE_RELEASE'],
        'AIKEN_RELEASE': cfg['AIKEN_RELEASE'],
        'CARDANO_PATH': cfg['CARDANO_PATH'],
        'CARDANO_SRC_PATH': cfg['CARDANO_SRC_PATH']
    }
