"""Tests for the StarMaker CLI surface and interactive-menu registry.

These tests exercise only the public CLI (``--help`` for the group and every
subcommand) and the static structure of the interactive-menu registry. They do
NOT invoke the interactive wizard or any live network/browser flow.
"""

from __future__ import annotations

import click
import pytest
from click.testing import CliRunner

from starmaker.cli import (
    MENU_COMMANDS,
    _MENU_DESCRIPTIONS,
    _QUIT_KEY,
    cli,
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# --- Group + subcommand --help all exit 0 -----------------------------------

def test_cli_help_exits_zero(runner: CliRunner) -> None:
    """``starmaker --help`` exits 0 and lists the commands."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    # A representative sampling of commands should appear in the help text.
    for name in ("init", "draft", "post", "audit", "auto-post", "all"):
        assert name in result.output


def test_version_option_exits_zero(runner: CliRunner) -> None:
    """``starmaker --version`` exits 0."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0


# All command names registered on the group.
_COMMAND_NAMES = sorted(cli.commands.keys())


def test_expected_commands_present() -> None:
    """The group exposes the full, stable command set."""
    assert set(_COMMAND_NAMES) == {
        "init", "draft", "post", "credentials", "setup", "audit",
        "awesome", "compare", "readme", "auto-post", "all",
    }


@pytest.mark.parametrize("command_name", _COMMAND_NAMES)
def test_subcommand_help_exits_zero(runner: CliRunner, command_name: str) -> None:
    """Every subcommand's ``--help`` exits 0."""
    result = runner.invoke(cli, [command_name, "--help"])
    assert result.exit_code == 0
    assert command_name in result.output


# --- Interactive-menu registry integrity ------------------------------------

def test_registry_values_are_registered_click_commands() -> None:
    """Every menu entry maps to a real, callable Click command on the group."""
    registered = set(cli.commands.values())
    assert MENU_COMMANDS, "registry should not be empty"
    for key, command in MENU_COMMANDS.items():
        assert isinstance(command, click.Command), f"{key!r} -> {command!r} is not a Click command"
        assert callable(command), f"{key!r} -> {command!r} is not callable"
        assert command in registered, f"{key!r} -> {command.name!r} is not registered on the cli group"


def test_registry_keys_match_descriptions() -> None:
    """Registry keys mirror the menu descriptions (minus the quit key)."""
    expected_keys = set(_MENU_DESCRIPTIONS) - {_QUIT_KEY}
    assert set(MENU_COMMANDS) == expected_keys


def test_quit_key_has_no_command() -> None:
    """The quit key is described but intentionally absent from the registry."""
    assert _QUIT_KEY in _MENU_DESCRIPTIONS
    assert _QUIT_KEY not in MENU_COMMANDS


def test_registry_commands_are_unique() -> None:
    """No two menu entries point at the same command."""
    commands = list(MENU_COMMANDS.values())
    assert len(commands) == len(set(commands))
