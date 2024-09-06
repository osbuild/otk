import json
import subprocess
import sys


def root():
    data = json.loads(sys.stdin.read())

    tree = data["tree"]

    request = {
        "command": "depsolve",
        "arch": tree["architecture"],
        "module_platform_id": "platform:" + tree["module_platform_id"],
        "releasever": tree["releasever"],
        "cachedir": "/tmp",
        "arguments": {
            "root_dir": "/tmp",
            "repos": tree["repositories"],
            "transactions": [
                {
                    "package-specs": tree["packages"]["include"],
                    "exclude-specs": tree["packages"].get("exclude", []),
                },
            ],
        },
    }

    process = subprocess.run(
        ["/usr/libexec/osbuild-depsolve-dnf"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        input=json.dumps(request),
        encoding="utf8",
        check=False,
    )

    if process.returncode != 0:
        raise RuntimeError(f"{process.stdout=}{process.stderr=}")

    results = json.loads(process.stdout)
    packages = results.get("packages", [])

    sys.stdout.write(
        json.dumps(
            {
                "tree": packages,
            },
        ),
    )


def main():
    root()


if __name__ == "__main__":
    main()
