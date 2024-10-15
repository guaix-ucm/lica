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

# Publish the package in (pypi|testpypi)
publish repo="pypi" : build
    twine upload --verbose -r {{ repo }} dist/*

# install version from Test PyPi server
tinstall pkg="lica":
    uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ {{pkg}}
