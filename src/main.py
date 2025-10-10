"""SocFlow main entry point."""

import warnings

# Suppress Pydantic warnings about Field defaults
warnings.filterwarnings("ignore", message=".*default.*attribute.*Field.*")

from .app import cli

if __name__ == "__main__":
    cli()
