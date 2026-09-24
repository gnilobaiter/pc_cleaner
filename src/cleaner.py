from __future__ import annotations

import ctypes
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Optional

from src.config import get_temp_dirs, is_trusted_cleanup_path
from src.presets import PresetStore, cleanup_choice_key
from src.utils import (
    convert_size,
    get_user_confirmation,
    get_yes_no,
    has_access,
    print_status,
)

DNS_CHOICE_KEY = "action:flush-dns"
IO_REPARSE_TAG_AF_UNIX = 0x80000023
SHERB_NOCONFIRMATION = 0x00000001
SHERB_NOPROGRESSUI = 0x00000002
SHERB_NOSOUND = 0x00000004
LOCAL_DRIVE_TYPES = {2, 3, 6}


class RecycleBinInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_longlong),
        ("i64NumItems", ctypes.c_longlong),
    ]


class Cleaner:
    def __init__(
        self, dry_run: bool = False, preset_store: Optional[PresetStore] = None
    ):
        self.dry_run = dry_run
        self.total_deleted_size: int = 0
        self.preset_store = preset_store
        self._preset_choices: dict[str, bool] = {}
        self._use_preset = False

    def print_status(
        self, message: str, error: bool = False, emoji: str = "[🧹]"
    ) -> None:
        print_status(message, error=error, emoji=emoji)

    def clear_folder(self, folder: Path, name: str) -> int:
        if (
            not is_trusted_cleanup_path(str(folder), name)
            or self._is_reparse_point(folder)
            or not has_access(folder)
        ):
            return 0

        deleted_size = 0
        if not folder.exists():
            return 0

        try:
            items = list(folder.iterdir())
            for item in items:
                try:
                    if self._is_reparse_point(item):
                        reparse_size = self._remove_safe_reparse_point(item)
                        if reparse_size is not None:
                            deleted_size += reparse_size
                    elif item.is_file() or item.is_symlink():
                        size = item.stat().st_size
                        if not self.dry_run:
                            item.unlink()
                        deleted_size += size
                    elif item.is_dir():
                        size = self.get_directory_size(item)
                        if self._is_reparse_point(item):
                            continue
                        if self.dry_run:
                            deleted_size += size
                        else:
                            try:
                                shutil.rmtree(item)
                                deleted_size += size
                            except Exception:
                                remaining_size = (
                                    self.get_directory_size(item)
                                    if item.exists()
                                    else 0
                                )
                                deleted_size += max(0, size - remaining_size)
                                raise
                except PermissionError:
                    pass
                except Exception as error:  # noqa: BLE001
                    self.print_status(
                        f"Error processing {item}: {error}", error=True, emoji="[❗]"
                    )
        except Exception as error:  # noqa: BLE001
            self.print_status(
                f"Failed to process {folder}: {error}", error=True, emoji="[❗]"
            )
        return deleted_size

    def _remove_safe_reparse_point(self, path: Path) -> Optional[int]:
        try:
            path_stat = path.lstat()
        except OSError:
            return None

        reparse_tag = getattr(path_stat, "st_reparse_tag", 0)
        is_file_link = path.is_symlink() and not stat.S_ISDIR(path_stat.st_mode)
        if reparse_tag != IO_REPARSE_TAG_AF_UNIX and not is_file_link:
            return None

        if not self.dry_run:
            path.unlink()
        return path_stat.st_size

    @staticmethod
    def _is_reparse_point(path: Path) -> bool:
        try:
            attributes = path.lstat().st_file_attributes
        except (AttributeError, OSError):
            return path.is_symlink()
        return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)

    @classmethod
    def get_directory_size(cls, directory: Path) -> int:
        total_size = 0
        for item in directory.rglob("*"):
            try:
                if not cls._is_reparse_point(item) and item.is_file():
                    total_size += item.stat().st_size
            except OSError:
                pass
        return total_size

    @staticmethod
    def _shell32():
        return ctypes.windll.shell32

    @staticmethod
    def _kernel32():
        return ctypes.windll.kernel32

    @classmethod
    def get_local_drive_roots(cls) -> list[str]:
        kernel32 = cls._kernel32()
        drive_mask = kernel32.GetLogicalDrives()
        if drive_mask == 0:
            raise OSError("GetLogicalDrives failed")

        roots = []
        for index in range(26):
            if drive_mask & (1 << index):
                root = f"{chr(ord('A') + index)}:\\"
                if kernel32.GetDriveTypeW(root) in LOCAL_DRIVE_TYPES:
                    roots.append(root)
        return roots

    @staticmethod
    def _hresult(value: int) -> str:
        return f"0x{value & 0xFFFFFFFF:08X}"

    def clear_recycle_bin(self) -> int:
        shell32 = self._shell32()
        flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
        deleted_size = 0
        queried_drives = 0

        for root in self.get_local_drive_roots():
            recycle_bin_info = RecycleBinInfo()
            recycle_bin_info.cbSize = ctypes.sizeof(RecycleBinInfo)
            query_result = shell32.SHQueryRecycleBinW(
                root, ctypes.byref(recycle_bin_info)
            )
            if query_result != 0:
                self.print_status(
                    f"Could not inspect Recycle Bin on {root} "
                    f"(HRESULT {self._hresult(query_result)})",
                    error=True,
                    emoji="[❗]",
                )
                continue

            queried_drives += 1
            if self.dry_run:
                deleted_size += recycle_bin_info.i64Size
                continue
            if recycle_bin_info.i64NumItems == 0:
                continue

            empty_result = shell32.SHEmptyRecycleBinW(None, root, flags)
            if empty_result == 0:
                deleted_size += recycle_bin_info.i64Size
            else:
                self.print_status(
                    f"Could not empty Recycle Bin on {root} "
                    f"(HRESULT {self._hresult(empty_result)})",
                    error=True,
                    emoji="[❗]",
                )

        if queried_drives == 0:
            raise OSError("No local Recycle Bins could be inspected")
        return deleted_size

    def _choose(self, key: str, name: str, description: str) -> bool:
        if self._use_preset and key in self._preset_choices:
            return self._preset_choices[key]
        choice = get_user_confirmation(name, description)
        self._preset_choices[key] = choice
        return choice

    def _prepare_preset(self) -> None:
        if self.preset_store is None:
            self.preset_store = PresetStore()
        saved_choices = self.preset_store.load()
        if saved_choices is not None and get_yes_no("Use the last preset? (y/n): "):
            self._preset_choices = saved_choices
            self._use_preset = True
            self.print_status("Using the last saved preset\n", emoji="[💽]")
        else:
            self._preset_choices = {}
            self._use_preset = False

    def _save_preset(self) -> None:
        if self.preset_store is None:
            self.preset_store = PresetStore()
        if not self.preset_store.save(self._preset_choices):
            self.print_status(
                "Could not save the cleanup preset", error=True, emoji="[❗]"
            )

    def flush_dns(self, should_flush: Optional[bool] = None) -> None:
        if should_flush is None:
            should_flush = get_user_confirmation(
                "DNS Cache", "Flush DNS resolver cache"
            )
        if not should_flush:
            self.print_status("Skipping DNS Flush\n", emoji="[💽]")
            return

        self.print_status("Flushing DNS cache...", emoji="[💽]")
        try:
            subprocess.run(["ipconfig", "/flushdns"], check=True)
            self.print_status("DNS cache flushed successfully\n", emoji="[✅]")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_status("Failed to flush DNS cache.\n", error=True, emoji="[❗]")

    def run(self) -> None:
        self._prepare_preset()
        for name, path, description, needs_confirmation in get_temp_dirs():
            if needs_confirmation:
                key = cleanup_choice_key(name, path)
                if not self._choose(key, name, description):
                    self.print_status(f"Skipping {name}\n", emoji="[💽]")
                    continue

            self.print_status(f"Cleaning {name} ({path})...", emoji="[💽]")
            try:
                size = (
                    self.clear_recycle_bin()
                    if name == "Recycle Bin"
                    else self.clear_folder(Path(path), name)
                )
            except OSError as error:
                self.print_status(
                    f"Failed to clean {name}: {error}", error=True, emoji="[❗]"
                )
                size = 0
            self.total_deleted_size += size
            self.print_status(
                f"Removed {convert_size(size)} from {name}\n", emoji="[✅]"
            )

        should_flush_dns = self._choose(
            DNS_CHOICE_KEY, "DNS Cache", "Flush DNS resolver cache"
        )
        self.flush_dns(should_flush_dns)
        self._save_preset()

        self.print_status(f"{'═' * 50}")
        self.print_status(
            f"Total data removed: {convert_size(self.total_deleted_size)}"
        )
        self.print_status(f"{'═' * 50}")
        input("Press Enter to exit...")
