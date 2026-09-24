from __future__ import annotations

import ctypes
import os
import stat
from pathlib import Path
from typing import Tuple

# This version is used by GitHub Actions and the CLI.
VERSION = "v1.2.0"

CleanupEntry = Tuple[str, str, str, bool]


def _windows_directory() -> str:
    if os.name != "nt":
        return os.getenv("SystemRoot", "C:\\Windows")

    buffer = ctypes.create_unicode_buffer(260)
    if ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer)) == 0:
        raise OSError("Unable to determine the Windows directory")
    return buffer.value


def _known_folder(csidl: int, fallback_env: str) -> str:
    if os.name != "nt":
        return os.getenv(fallback_env, "")

    buffer = ctypes.create_unicode_buffer(260)
    if ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buffer) != 0:
        raise OSError("Unable to determine a Windows known folder")
    return buffer.value


def get_appdata_dir() -> Path:
    return Path(_known_folder(0x1A, "APPDATA"))


def get_trusted_roots() -> tuple[str, ...]:
    windows_dir = _windows_directory()
    return (
        windows_dir,
        _known_folder(0x28, "USERPROFILE"),
        _known_folder(0x1C, "LOCALAPPDATA"),
        _known_folder(0x1A, "APPDATA"),
        _known_folder(0x23, "PROGRAMDATA"),
    )


def is_reparse_free_path(path: str, trusted_root: str) -> bool:
    candidate = Path(os.path.abspath(path))
    root = Path(os.path.abspath(trusted_root))
    try:
        relative_parts = candidate.relative_to(root).parts
    except ValueError:
        return False

    current = root
    for part in relative_parts:
        current /= part
        try:
            path_stat = current.lstat()
        except FileNotFoundError:
            break
        except OSError:
            return False
        attributes = getattr(path_stat, "st_file_attributes", 0)
        if current.is_symlink() or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            return False
    return True


def is_trusted_cleanup_path(path: str, name: str = "") -> bool:
    candidate = os.path.normcase(os.path.abspath(path))
    windows_dir = _windows_directory()
    system_drive = os.path.splitdrive(windows_dir)[0]
    special_paths = {
        "Windows.old": os.path.join(windows_dir, "..", "Windows.old"),
        "Recycle Bin": os.path.join(system_drive + os.sep, "$Recycle.Bin"),
    }
    if name in special_paths:
        expected = os.path.normcase(os.path.abspath(special_paths[name]))
        return candidate == expected and is_reparse_free_path(
            candidate, os.path.dirname(expected)
        )

    for root in get_trusted_roots():
        if not root:
            continue
        trusted_root = os.path.normcase(os.path.abspath(root))
        try:
            if os.path.commonpath(
                (candidate, trusted_root)
            ) == trusted_root and is_reparse_free_path(candidate, trusted_root):
                return True
        except ValueError:
            continue
    return False


def _entry(
    name: str, path: str, description: str, needs_confirmation: bool = False
) -> CleanupEntry:
    return name, path, description, needs_confirmation


def _matching_entries(
    name: str,
    base: str,
    pattern: str,
    description: str,
    needs_confirmation: bool,
    distinguish_parent: bool = False,
) -> list[CleanupEntry]:
    if not base:
        return []
    return [
        _entry(
            f"{name} ({path.parent.name})" if distinguish_parent else name,
            str(path),
            description,
            needs_confirmation,
        )
        for path in sorted(Path(base).glob(pattern))
        if path.is_dir()
    ]


def get_temp_dirs() -> list[CleanupEntry]:
    system_root = os.getenv("SystemRoot", "C:\\Windows")
    system_drive = os.getenv("SystemDrive", "C:")
    user_profile = os.getenv("USERPROFILE", "")
    local_appdata = os.getenv("LOCALAPPDATA", "")
    appdata = os.getenv("APPDATA", "")
    program_data = os.getenv("PROGRAMDATA", "C:\\ProgramData")

    entries: list[CleanupEntry] = [
        # Windows and system cleanup.
        _entry(
            "System Temp", os.path.join(system_root, "Temp"), "Temporary system files"
        ),
        _entry(
            "Delivery Optimization",
            os.path.join(system_root, "SoftwareDistribution", "DeliveryOptimization"),
            "Windows Update delivery optimization cache",
        ),
        _entry(
            "Windows Updates",
            os.path.join(system_root, "SoftwareDistribution", "Download"),
            "Downloaded Windows Update files (may be downloaded again)",
            True,
        ),
        _entry(
            "Windows Logs",
            os.path.join(system_root, "Logs"),
            "Windows diagnostic and update log files",
            True,
        ),
        _entry(
            "Event Logs",
            os.path.join(system_root, "System32", "winevt", "Logs"),
            "Windows event log files (system and application logs)",
            True,
        ),
        _entry(
            "Prefetch",
            os.path.join(system_root, "Prefetch"),
            "System prefetch files (may slow initial program loading if cleared)",
            True,
        ),
        _entry(
            "Live Kernel Reports",
            os.path.join(system_root, "LiveKernelReports"),
            "System diagnostic reports",
            True,
        ),
        _entry(
            "Windows.old",
            os.path.join(system_root, "..", "Windows.old"),
            "Previous Windows installation files (removes rollback option)",
            True,
        ),
        _entry(
            "Recycle Bin",
            os.path.join(system_drive + os.sep, "$Recycle.Bin"),
            "Files in Recycle Bins on all drives (permanent deletion)",
            True,
        ),
        # Current-user temporary files and diagnostics.
        _entry(
            "User Temp",
            os.path.join(local_appdata, "Temp"),
            "Temporary user files in Local directory",
        ),
        _entry(
            "User Temp (LocalLow)",
            os.path.join(user_profile, "AppData", "LocalLow", "Temp"),
            "Temporary user files in LocalLow directory",
        ),
        _entry(
            "User Cache",
            os.path.join(user_profile, ".cache"),
            "Cache directory in the user profile (.cache)",
            True,
        ),
        _entry(
            "Thumbnail Cache",
            os.path.join(local_appdata, "Microsoft", "Windows", "Explorer"),
            "File Explorer thumbnail and icon caches",
        ),
        _entry(
            "Internet Cache",
            os.path.join(local_appdata, "Microsoft", "Windows", "INetCache"),
            "Windows internet cache",
        ),
        _entry(
            "Windows WebCache",
            os.path.join(local_appdata, "Microsoft", "Windows", "WebCache"),
            "Windows web component cache",
        ),
        _entry(
            "Microsoft Store Cache",
            os.path.join(
                local_appdata,
                "Packages",
                "Microsoft.WindowsStore_8wekyb3d8bbwe",
                "LocalCache",
            ),
            "Microsoft Store local cache",
        ),
        _entry(
            "Crash Dumps",
            os.path.join(local_appdata, "CrashDumps"),
            "Application crash dump files (removes diagnostic data)",
            True,
        ),
        _entry(
            "Windows Error Reporting",
            os.path.join(local_appdata, "Microsoft", "Windows", "WER"),
            "Windows Error Reporting reports (removes diagnostic data)",
            True,
        ),
        _entry(
            "System Error Reporting",
            os.path.join(program_data, "Microsoft", "Windows", "WER"),
            "System-wide Windows Error Reporting reports",
            True,
        ),
        # Browser caches.
        _entry(
            "Edge Cache",
            os.path.join(
                local_appdata, "Microsoft", "Edge", "User Data", "Default", "Cache"
            ),
            "Microsoft Edge browser cache",
            True,
        ),
        _entry(
            "Edge Code Cache",
            os.path.join(
                local_appdata, "Microsoft", "Edge", "User Data", "Default", "Code Cache"
            ),
            "Microsoft Edge JavaScript code cache",
            True,
        ),
        _entry(
            "Edge GPU Cache",
            os.path.join(
                local_appdata, "Microsoft", "Edge", "User Data", "Default", "GPUCache"
            ),
            "Microsoft Edge GPU cache",
            True,
        ),
        _entry(
            "Edge Service Worker Cache",
            os.path.join(
                local_appdata,
                "Microsoft",
                "Edge",
                "User Data",
                "Default",
                "Service Worker",
                "CacheStorage",
            ),
            "Microsoft Edge service worker offline cache",
            True,
        ),
        _entry(
            "Chrome Cache",
            os.path.join(
                local_appdata, "Google", "Chrome", "User Data", "Default", "Cache"
            ),
            "Google Chrome browser cache",
            True,
        ),
        _entry(
            "Chrome Code Cache",
            os.path.join(
                local_appdata, "Google", "Chrome", "User Data", "Default", "Code Cache"
            ),
            "Google Chrome JavaScript code cache",
            True,
        ),
        _entry(
            "Chrome GPU Cache",
            os.path.join(
                local_appdata, "Google", "Chrome", "User Data", "Default", "GPUCache"
            ),
            "Google Chrome GPU cache",
            True,
        ),
        _entry(
            "Chrome Service Worker Cache",
            os.path.join(
                local_appdata,
                "Google",
                "Chrome",
                "User Data",
                "Default",
                "Service Worker",
                "CacheStorage",
            ),
            "Google Chrome service worker offline cache",
            True,
        ),
        _entry(
            "Brave Cache",
            os.path.join(
                local_appdata,
                "BraveSoftware",
                "Brave-Browser",
                "User Data",
                "Default",
                "Cache",
            ),
            "Brave browser cache",
            True,
        ),
        _entry(
            "Opera Cache",
            os.path.join(local_appdata, "Opera Software", "Opera Stable", "Cache"),
            "Opera browser cache",
            True,
        ),
        # Development tool caches.
        _entry(
            "Pytest Cache",
            os.path.join(user_profile, ".pytest_cache"),
            "Python pytest cache",
        ),
        _entry(
            "Ruff Cache",
            os.path.join(user_profile, ".cache", "ruff"),
            "Ruff linter cache",
        ),
        _entry(
            "Mypy Cache",
            os.path.join(user_profile, ".mypy_cache"),
            "Mypy type checker cache",
        ),
        _entry(
            "pip Cache",
            os.path.join(local_appdata, "pip", "cache"),
            "Python pip package cache",
        ),
        _entry(
            "uv Cache",
            os.path.join(local_appdata, "uv", "cache"),
            "uv Python package manager cache",
        ),
        _entry(
            "Poetry Cache",
            os.path.join(local_appdata, "pypoetry", "Cache"),
            "Poetry Python package manager cache",
        ),
        _entry(
            "npm Cache",
            os.path.join(local_appdata, "npm-cache"),
            "npm package manager cache",
        ),
        _entry(
            "Yarn Cache",
            os.path.join(local_appdata, "Yarn", "Cache"),
            "Yarn package manager cache",
        ),
        _entry(
            "pnpm Cache",
            os.path.join(local_appdata, "pnpm-cache"),
            "pnpm package manager cache",
        ),
        _entry(
            "Corepack Cache",
            os.path.join(local_appdata, "node", "corepack"),
            "Node Corepack package manager cache",
        ),
        _entry(
            "Bun Cache",
            os.path.join(local_appdata, "bun", "install", "cache"),
            "Bun JavaScript runtime cache",
        ),
        _entry(
            "NuGet HTTP Cache",
            os.path.join(local_appdata, "NuGet", "v3-cache"),
            "NuGet downloaded package metadata and archives",
        ),
        _entry(
            "NuGet Plugins Cache",
            os.path.join(local_appdata, "NuGet", "plugins-cache"),
            "NuGet credential and plugin cache",
        ),
        _entry(
            "Go Build Cache",
            os.path.join(local_appdata, "go-build"),
            "Go compiler build cache (will be rebuilt)",
            True,
        ),
        _entry(
            "Cargo Registry Cache",
            os.path.join(user_profile, ".cargo", "registry", "cache"),
            "Downloaded Rust crates (will be downloaded again)",
            True,
        ),
        _entry(
            "Gradle Cache",
            os.path.join(user_profile, ".gradle", "caches"),
            "Gradle build and dependency cache",
            True,
        ),
        _entry(
            "Gradle Temp",
            os.path.join(user_profile, ".gradle", ".tmp"),
            "Gradle temporary files",
            True,
        ),
        _entry(
            "Visual Studio Cache",
            os.path.join(local_appdata, "Microsoft", "VisualStudio"),
            "Visual Studio local cache files",
            True,
        ),
        _entry(
            "VS Code Cache",
            os.path.join(appdata, "Code", "Cache"),
            "Visual Studio Code cache",
        ),
        _entry(
            "VS Code Cached Data",
            os.path.join(appdata, "Code", "CachedData"),
            "Visual Studio Code cached data",
        ),
        _entry(
            "VS Code Logs",
            os.path.join(appdata, "Code", "logs"),
            "Visual Studio Code log files",
        ),
        # Communication and media application caches.
        _entry(
            "Discord Cache",
            os.path.join(appdata, "discord", "Cache"),
            "Discord application cache",
            True,
        ),
        _entry(
            "Discord Code Cache",
            os.path.join(appdata, "discord", "Code Cache"),
            "Discord JavaScript code cache",
            True,
        ),
        _entry(
            "Teams Cache",
            os.path.join(appdata, "Microsoft", "Teams", "Cache"),
            "Microsoft Teams application cache",
            True,
        ),
        _entry(
            "Slack Cache",
            os.path.join(appdata, "Slack", "Cache"),
            "Slack application cache",
            True,
        ),
        _entry(
            "Zoom Cache",
            os.path.join(appdata, "Zoom", "data"),
            "Zoom application data cache",
            True,
        ),
        _entry(
            "Spotify Cache",
            os.path.join(local_appdata, "Spotify", "Data"),
            "Spotify downloaded data cache",
            True,
        ),
        _entry(
            "Adobe Media Cache",
            os.path.join(appdata, "Adobe", "Common", "Media Cache Files"),
            "Adobe media cache files",
            True,
        ),
        # Game launcher caches.
        _entry(
            "Steam HTML Cache",
            os.path.join(local_appdata, "Steam", "htmlcache"),
            "Steam embedded browser cache",
            True,
        ),
        _entry(
            "Steam Shader Cache",
            os.path.join(local_appdata, "Steam", "shadercache"),
            "Steam shader cache (may recompile shaders)",
            True,
        ),
        _entry(
            "Epic Games Cache",
            os.path.join(local_appdata, "EpicGamesLauncher", "Saved", "webcache"),
            "Epic Games Launcher web cache",
            True,
        ),
        _entry(
            "Battle.net Cache",
            os.path.join(program_data, "Battle.net", "Cache"),
            "Battle.net application cache",
            True,
        ),
        # Graphics caches.
        _entry(
            "Direct3D Shader Cache",
            os.path.join(local_appdata, "D3DSCache"),
            "Direct3D shader cache (may cause shader recompilation)",
            True,
        ),
        _entry(
            "NVIDIA GL Cache",
            os.path.join(local_appdata, "NVIDIA", "GLCache"),
            "NVIDIA OpenGL cache (may cause shader recompilation)",
            True,
        ),
        _entry(
            "NVIDIA DX Cache",
            os.path.join(local_appdata, "NVIDIA", "DXCache"),
            "NVIDIA DirectX cache (may cause shader recompilation)",
            True,
        ),
        _entry(
            "Intel Shader Cache",
            os.path.join(local_appdata, "Intel", "ShaderCache"),
            "Intel GPU shader cache (may cause shader recompilation)",
            True,
        ),
        _entry(
            "AMD DX Cache",
            os.path.join(local_appdata, "AMD", "DxCache"),
            "AMD DirectX shader cache (may cause shader recompilation)",
            True,
        ),
    ]

    firefox_entries = _matching_entries(
        "Firefox Cache",
        os.path.join(local_appdata, "Mozilla", "Firefox", "Profiles"),
        "*/cache2",
        "Mozilla Firefox profile cache",
        True,
        True,
    )
    first_development_entry = next(
        index for index, entry in enumerate(entries) if entry[0] == "Pytest Cache"
    )
    entries[first_development_entry:first_development_entry] = firefox_entries

    jetbrains_entries = _matching_entries(
        "JetBrains Cache",
        os.path.join(local_appdata, "JetBrains"),
        "*/caches",
        "JetBrains IDE indexes and caches (will be rebuilt)",
        True,
        True,
    ) + _matching_entries(
        "JetBrains Logs",
        os.path.join(local_appdata, "JetBrains"),
        "*/log",
        "JetBrains IDE log files",
        False,
        True,
    )
    first_application_entry = next(
        index for index, entry in enumerate(entries) if entry[0] == "Discord Cache"
    )
    entries[first_application_entry:first_application_entry] = jetbrains_entries

    trusted_entries = [
        entry for entry in entries if is_trusted_cleanup_path(entry[1], entry[0])
    ]
    return list(dict.fromkeys(trusted_entries))
