# Installation

As `otk` is still in a proof of concept state it is not yet packaged for any distributions. Installation thus requires you to work from [source](https://github.com/osbuild/otk).

To start hacking on `otk` you can:

```
€ git checkout https://github.com/osbuild/otk
# ...
€ python3 -m venv venv
# ...
€ . venv/bin/activate
# ...
€ pip install -e ".[dev]"
# ...
```

This will get you an activated Python virtual environment with an editable install of `otk`. You can then run edit source in `src/` and run `otk` as long as your virtual environment is enabled.

You can read more about [contributing](./contributing)
