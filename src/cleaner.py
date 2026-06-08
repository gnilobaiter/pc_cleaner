import shutil
import subprocess
from pathlib import Path

from src.config import get_temp_dirs
from src.utils import convert_size, print_status, has_access, get_user_confirmation

class Cleaner:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.total_deleted_size: int = 0

    def print_status(self, message: str, error: bool = False, emoji: str = "[🧹]") -> None:
        print_status(message, error=error, emoji=emoji)

    def clear_folder(self, folder: Path, name: str) -> int:
        if not has_access(folder):
            return 0
        
        deleted_size = 0
        if not folder.exists():
            return 0
        
        try:
            items = list(folder.iterdir())
            for item in items:
                try:
                    if item.is_file() or item.is_symlink():
                        size = item.stat().st_size
                        if not self.dry_run:
                            item.unlink()
                        deleted_size += size
                    elif item.is_dir():
                        size = self.get_directory_size(item)
                        if not self.dry_run:
                            shutil.rmtree(item)
                        deleted_size += size
                except PermissionError:
                    pass
                except Exception as e:
                    self.print_status(f"Error processing {item}: {e}", error=True, emoji="[❗]")
        except Exception as e:
            self.print_status(f"Failed to process {folder}: {e}", error=True, emoji="[❗]")
        return deleted_size

    @staticmethod
    def get_directory_size(directory: Path) -> int:
        total_size = 0
        for item in directory.rglob('*'):
            try:
                if item.is_file():
                    total_size += item.stat().st_size
            except OSError:
                pass
        return total_size

    def flush_dns(self) -> None:
        if not get_user_confirmation("DNS Cache", "Flush DNS resolver cache"):
            self.print_status("Skipping DNS Flush\n", emoji="[💽]")
            return
        
        self.print_status("Flushing DNS cache...", emoji="[💽]")
        try:
            subprocess.run(['ipconfig', '/flushdns'], check=True)
            self.print_status("DNS cache flushed successfully\n", emoji="[✅]")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_status("Failed to flush DNS cache.\n", error=True, emoji="[❗]")

    def run(self) -> None:
        temp_dirs = get_temp_dirs()
        for name, path, desc, needs_confirm in temp_dirs:
            if needs_confirm and not get_user_confirmation(name, desc):
                self.print_status(f"Skipping {name}\n", emoji="[💽]")
                continue
            
            self.print_status(f"Cleaning {name} ({path})...", emoji="[💽]")
            size = self.clear_folder(Path(path), name)
            self.total_deleted_size += size
            self.print_status(f"Freed {convert_size(size)} from {name}\n", emoji="[✅]")
        
        self.flush_dns()
        
        self.print_status(f"{'═' * 50}")
        self.print_status(f"Total space freed: {convert_size(self.total_deleted_size)}")
        self.print_status(f"{'═' * 50}")
        input("Press Enter to exit...")