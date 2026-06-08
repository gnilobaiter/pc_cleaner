import platform
import os
import sys
from pathlib import Path
from src.config import VERSION

try:
    from colorama import init, Fore, Style
    init()
    USE_COLORS = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
except ImportError:
    USE_COLORS = False
    Fore = Style = type('Dummy', (), {'RED': '', 'GREEN': '', 'CYAN': '', 'YELLOW': '', 'WHITE': '', 'MAGENTA': '', 'RESET_ALL': ''})()

_SUPPORTS_EMOJI: bool = (
    sys.stdout.encoding.lower().startswith('utf')
    and (platform.system() != "Windows" or platform.release() >= "10")
)

_EMOJI_FALLBACKS: dict[str, str] = {
    "[🧹]": "[-]",
    "[✅]": "[+]",
    "[❓]": "[?]",
    "[💽]": "[>]",
    "[❗]": "[!]",
}

def print_status(message: str, error: bool = False, emoji: str = "[🧹]") -> None:
    if emoji == "[✅]":
        color = Fore.GREEN
    elif emoji == "[❓]":
        color = Fore.YELLOW
    elif emoji == "[💽]":
        color = Fore.CYAN
    elif error:
        color = Fore.RED
    else:
        color = Fore.MAGENTA
    display = emoji if _SUPPORTS_EMOJI else _EMOJI_FALLBACKS.get(emoji, "[*]")
    if USE_COLORS:
        print(f"{color}{display} {message}{Style.RESET_ALL}")
    else:
        print(f"{display} {message}")

def print_banner() -> None:
    if USE_COLORS:
        print(f"{Fore.RED}          PC_CLEANER {VERSION}")
        print(f"------------------------------------{Style.RESET_ALL}")
    else:
        print(f"          PC_CLEANER {VERSION}")
        print("------------------------------------")

def convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    unit_idx = min(len(units) - 1, int((len(str(size_bytes)) - 1) // 3))
    size = size_bytes / (1024 ** unit_idx)
    return f"{size:.2f} {units[unit_idx]}"

def has_access(folder: Path) -> bool:
    return folder.exists() and os.access(folder, os.R_OK | os.W_OK)

def get_user_confirmation(name: str, description: str) -> bool:
    print_status(f"{name}: {description}", emoji="[❓]")
    while True:
        q = "[❓]" if _SUPPORTS_EMOJI else "[?]"
        prompt = f"{Fore.YELLOW}{q} Clear this? (y/n): {Style.RESET_ALL}" if USE_COLORS else f"{q} Clear this? (y/n): "
        choice = input(prompt).lower().strip()
        if choice in ('y', 'n'):
            return choice == 'y'
        print_status("Please enter 'y' or 'n'", error=True, emoji="[❗]")