# lica
 
 Assorte collection of source code with utilities (functions, classes, etc.) 
 used in other projects at LICA (UCM) or STARS4ALL

## Installation

### Stable version

```bash
pip install lica
```

### Development version using UV 
This must be handed a source code in your client package with one of the two commands below.

```bash
uv add git+https://github.com/guaix-ucm/lica --branch main
uv add git+https://github.com/guaix-ucm/lica --tag x.y.z
```

*** Note: ***
lica library uses different modules in its subpackages
In order not to install them all, your client code should declare
dpendencies to tehse packages, as needed:

1. 'rawpy',
2. 'exifread',
3. 'numpy',
4. 'tabulate',
5. 'jinja2',
6. 'python-decouple'