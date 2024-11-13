# To install just on a per-project basis
# 1. Activate your virtual environemnt
# 2. uv add --dev rust-just
# 3. Use just within the activated environment

# list all recipes
default:
    just --list

# Install tools globally
tools:
    uv tool install twine
    uv tool install ruff

# Add conveniente development dependencies
dev:
    uv add --dev pytest

# Build the package
build:
    rm -fr dist/*
    uv build

# Publish the package in PyPi
publish: build
    twine upload --verbose -r pypi dist/*

# test installed version from PyPi server
install pkg="tess-ida-tools":
    uv run  --no-project --with {{pkg}} --refresh-package {{pkg}} \
        -- python -c "from lica import __version__; print(__version__)"

# Publish the package in Test PyPi
test-publish: build
    twine upload --verbose -r testpypi dist/*

# test installed version from Test PyPi server
test-install pkg="lica":
    uv run --with {{pkg}} --refresh-package {{pkg}} \
        --index-url https://test.pypi.org/simple/ \
        --extra-index-url https://pypi.org/simple/ \
        --no-project  -- python -c "from lica import __version__; print(__version__)"
