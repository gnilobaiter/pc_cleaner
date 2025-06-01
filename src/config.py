import os
from typing import List, Tuple

VERSION = "v1.0.0"

def get_temp_dirs() -> List[Tuple[str, str, str, bool]]:
    temp_dirs: List[Tuple[str, str, str, bool]] = [
        # Without confirmation (False)
        ("System Temp", os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), 'Temp'), 
            "Temporary system files", False),
        ("User Temp", os.path.join(os.getenv('USERPROFILE', ''), 'AppData', 'Local', 'Temp'),
            "Temporary user files in Local directory", False),
        ("User Temp", os.path.join(os.getenv('USERPROFILE', ''), 'AppData', 'LocalLow', 'Temp'),
            "Temporary user files in LocalLow directory", False),
        ("User Cache", os.path.join(os.getenv('USERPROFILE', ''), '.cache'),
            "Cache directory in user directory (.cache)", False),
        ("Internet Cache", os.path.join(os.getenv('USERPROFILE', ''), 'AppData', 'Local', 'Microsoft', 'Windows', 'INetCache'),
            "Internet Explorer and Edge browser cache", False),
        ("Thumbnail Cache", os.path.join(os.getenv('USERPROFILE', ''), 'AppData', 'Local', 'Microsoft', 'Windows', 'Explorer'),
            "Thumbnail cache for file explorer (will regenerate on demand)", False),
        ("Crash Dumps", os.path.join(os.getenv('USERPROFILE', ''), 'AppData', 'Local', 'CrashDumps'),
            "Application crash dump files", False),
        ("Live Kernel Reports", os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), 'LiveKernelReports'),
            "System diagnostic reports", False),
        ("Event Logs", os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), 'System32', 'winevt', 'Logs'),
            "Windows event log files (system and application logs)", False),
        ("Delivery Optimization", os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), 'SoftwareDistribution', 'DeliveryOptimization'),
            "Windows Update delivery optimization cache", False),
        ("Windows Updates", os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), 'SoftwareDistribution', 'Download'),
            "Windows Update downloads", False),
        ("Windows.old", os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), '..', 'Windows.old'),
            "Previous Windows installation files (removes rollback option)", False),
        ("Spotify Cache", os.path.join(os.getenv('USERPROFILE', ''), 'AppData', 'Local', 'Spotify', 'Data'),
            "Spotify data cache", False),
        
        # With confirmation (True)
        ("NVIDIA GL Cache", os.path.join(os.getenv('USERPROFILE', ''), 'AppData', 'Local', 'NVIDIA', 'GLCache'),
            "NVIDIA OpenGL cache (may cause temporary shader recompilation)", True),
        ("NVIDIA DX Cache", os.path.join(os.getenv('USERPROFILE', ''), 'AppData', 'Local', 'NVIDIA', 'DXCache'),
            "NVIDIA DirectX cache (may cause temporary graphics reload)", True),
        ("Prefetch", os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), 'Prefetch'),
            "System prefetch files (may slow initial program loading if cleared)", True),
        ("Recycle Bin", os.path.join(os.getenv('SystemDrive', 'C:'), '$Recycle.Bin'),
            "Files in the Recycle Bin (permanent deletion)", True),
        ("Gradle Cache", os.path.join(os.getenv('USERPROFILE', ''), '.gradle', 'caches'),
            "Gradle build cache (may require re-downloading dependencies)", True),
        # TODO: Add AI cache dirs (with confrimation)
    ]
    return temp_dirs