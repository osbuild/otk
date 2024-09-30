import json
import sys
from typing import List, Optional, TextIO


def find_pkg_by_name(packages: List[dict], pkg_name: str) -> Optional[dict]:
    for pkg in packages:
        if pkg["name"] == pkg_name:
            return pkg
    return None


def root(input_stream: TextIO) -> None:
    data = json.load(input_stream)
    pkg_name = data["tree"]["packagename"]
    packages = data["tree"]["packageset"]["const"]["internal"]["packages"]

    pkg = find_pkg_by_name(packages, pkg_name)
    if not pkg:
        raise KeyError(f"cannot find package {pkg_name}")
    sys.stdout.write(
        json.dumps(
            {
                "tree": {
                    "name": pkg["name"],
                    "version": pkg["version"],
                    "release": pkg["release"],
                    "arch": pkg["arch"],
                }
            }
        )
    )


def main():
    root(sys.stdin)


if __name__ == "__main__":
    main()
