import json
import sys

import otk


def root() -> None:
    sys.stdout.write(
        json.dumps(
            {
                "tree": f"otk {otk.__version__}",
            }
        )
    )


def main():
    root()


if __name__ == "__main__":
    main()
