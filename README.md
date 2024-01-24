# lica
 
 Assorte collection of utilities (functions, classes, etc.) used in other projects at LICA, UCM

 ## Installation

No need to install, just declare it as a dependency in the `dependencies` section of your
`pyproject.toml` as `"lica@git+https://github.com/guaix-ucm"`


```bash
(main) ~/repos/own/lica$ python3 -m venv .venv
(main) ~/repos/own/lica$ source .venv/bin/activate
```
3. Install it.

```bash
(.venv)  (main) ~/repos/own/lica$ pip install -U pip
(.venv)  (main) ~/repos/own/lica$ pip install .
```

This assorted collections ***do not install dependencies*** as not all utilites
are used. They are commented in the dependencies section so that dependant projects 
can declare them in their own `pyproject.toml` 
