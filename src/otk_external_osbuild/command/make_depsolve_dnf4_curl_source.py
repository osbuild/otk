import itertools
import json
import sys


def root():
    data = json.load(sys.stdin)
    tree = data["tree"]

    sources = {"org.osbuild.curl": {"items": {}}}

    for package in itertools.chain.from_iterable(
        s["const"]["internal"]["packages"] for s in tree["packages"]
    ):
        sources["org.osbuild.curl"]["items"][package["checksum"]] = {
            "url": package["remote_location"],
        }

    sys.stdout.write(
        json.dumps(
            {
                "tree": sources,
            }
        )
    )


def main():
    root()


if __name__ == "__main__":
    main()
