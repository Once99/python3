#!/usr/bin/env python3
"""
Send a text message to a Microsoft Teams chat/group.

Default target group/chat: Dev Avram
Default message: 好的

Requirements:
- macOS
- Microsoft Teams installed and logged in
- Python/Terminal is allowed under System Settings > Privacy & Security > Accessibility
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time


DEFAULT_GROUP = "Dev Avram"
DEFAULT_MESSAGE = "好的"
TEAMS_APP_CANDIDATES = ("Microsoft Teams", "Teams")
ENGLISH_INPUT_SOURCES = ("ABC", "U.S.", "US", "English")


class CommandError(RuntimeError):
    pass


def run_command(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise CommandError(f"Command failed: {' '.join(command)}\n{details}")
    return result


def open_teams() -> None:
    errors: list[str] = []

    for app_name in TEAMS_APP_CANDIDATES:
        result = run_command(["open", "-a", app_name], check=False)
        if result.returncode == 0:
            return
        errors.append(result.stderr.strip() or f"Unable to open {app_name}")

    raise CommandError("Could not open Microsoft Teams.\n" + "\n".join(errors))


def applescript_text(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def clipboard_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def send_message_to_teams(
    group_name: str,
    message: str,
    *,
    send_delay: float,
    dry_run: bool,
) -> None:
    group_name_text = applescript_text(group_name)
    message_text = clipboard_text(message)
    app_names = ", ".join(applescript_text(name) for name in TEAMS_APP_CANDIDATES)
    english_sources = ", ".join(applescript_text(name) for name in ENGLISH_INPUT_SOURCES)
    script = f"""
on typeText(theText)
    tell application "System Events"
        keystroke theText
    end tell
end typeText

on activateTeams(theDelay)
    set teamsApps to {{{app_names}}}
    repeat with appName in teamsApps
        try
            tell application appName to activate
            exit repeat
        end try
    end repeat
    delay theDelay

    tell application "System Events"
        set teamsProcesses to {{"Microsoft Teams", "MSTeams", "Teams"}}
        repeat with processName in teamsProcesses
            if exists process processName then
                tell process processName
                    set frontmost to true
                end tell
                exit repeat
            end if
        end repeat
    end tell
    delay theDelay
end activateTeams

on selectEnglishInput()
    set englishSources to {{{english_sources}}}
    tell application "System Events"
        if not (exists process "TextInputMenuAgent") then return false
        tell process "TextInputMenuAgent"
            repeat with barIndex in {{1, 2}}
                try
                    click menu bar item 1 of menu bar barIndex
                    delay 0.2
                    repeat with sourceName in englishSources
                        try
                            click menu item sourceName of menu 1 of menu bar item 1 of menu bar barIndex
                            delay 0.2
                            return true
                        end try
                    end repeat
                    key code 53
                end try
            end repeat
        end tell
    end tell
    return false
end selectEnglishInput

on focusTeamsComposeBox(theDelay)
    tell application "System Events"
        key code 53
    end tell
    delay theDelay

    tell application "System Events"
        set teamsProcesses to {{"Microsoft Teams", "MSTeams", "Teams"}}
        repeat with processName in teamsProcesses
            if exists process processName then
                tell process processName
                    set frontmost to true
                    try
                        repeat with theWindow in windows
                            if my clickFirstTextArea(theWindow) then return true
                        end repeat
                    end try

                    try
                        set windowPosition to position of window 1
                        set windowSize to size of window 1
                        set clickX to (item 1 of windowPosition) + ((item 1 of windowSize) / 2)
                        set clickY to (item 2 of windowPosition) + (item 2 of windowSize) - 80
                        click at {{clickX, clickY}}
                        delay theDelay
                        return true
                    end try
                end tell
            end if
        end repeat
    end tell
    return false
end focusTeamsComposeBox

on clickFirstTextArea(theElement)
    tell application "System Events"
        try
            set elementRole to role of theElement
            if elementRole is "AXTextArea" or elementRole is "AXTextField" then
                click theElement
                delay 0.2
                return true
            end if
        end try

        try
            repeat with childElement in UI elements of theElement
                if my clickFirstTextArea(childElement) then return true
            end repeat
        end try
    end tell
    return false
end clickFirstTextArea

activateTeams({send_delay})

if not selectEnglishInput() then
    error "Could not switch to an English input source. Add ABC or U.S. in System Settings > Keyboard > Input Sources."
end if
delay {send_delay}

tell application "System Events"
    keystroke "e" using command down
end tell
delay {send_delay}

typeText({group_name_text})
delay {send_delay}

tell application "System Events"
    key code 36
end tell
delay {send_delay * 1.5}

if not focusTeamsComposeBox({send_delay}) then
    error "Could not focus the Teams 'Type a message' box."
end if
set the clipboard to "{message_text}"
tell application "System Events"
    keystroke "v" using command down
end tell
delay {send_delay}
"""

    if not dry_run:
        script += """
tell application "System Events"
    key code 36
end tell
"""

    run_command(["osascript", "-e", script])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a text message to a Microsoft Teams group/chat."
    )
    parser.add_argument(
        "-g",
        "--group",
        default=DEFAULT_GROUP,
        help=f"Teams group/chat name to send to. Default: {DEFAULT_GROUP}",
    )
    parser.add_argument(
        "-m",
        "--message",
        default=DEFAULT_MESSAGE,
        help=f"Message text to send. Default: {DEFAULT_MESSAGE}",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.2,
        help="Delay between Teams UI actions in seconds. Increase this on slow machines.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Open the group and type the message, but do not press Enter to send.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        open_teams()
        time.sleep(args.delay)
        send_message_to_teams(
            args.group,
            args.message,
            send_delay=args.delay,
            dry_run=args.dry_run,
        )
    except CommandError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    action = "typed into" if args.dry_run else "sent to"
    print(f"Message {action} Teams group/chat: {args.group}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
