#!/usr/bin/python
"""Command line interface for pymend."""

import platform
import re
import traceback
from collections.abc import Iterable
from enum import Enum
from pathlib import Path
from re import Pattern
from typing import Any
from click import click

from .const import (DEFAULT_EXCLUDES,