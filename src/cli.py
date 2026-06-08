from src.cleaner import Cleaner
from src.utils import print_banner

def start_cli() -> int:
    print_banner()
    
    cleaner = Cleaner(dry_run=False)
    try:
        cleaner.run()
        return 0
    except KeyboardInterrupt:
        cleaner.print_status("Stopped by user", error=True)
        return 1
    except Exception as e:
        cleaner.print_status(f"Something broke: {e}", error=True)
        return 1