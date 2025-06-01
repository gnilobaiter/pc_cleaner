# PC Cleaner

A system cleanup utility for Windows.

## Features
- Cleans system and user temporary files.
- Flushes DNS cache.
- Purges pip cache.

## Cleaned Directories
Below is a list of directories that PC Cleaner targets for cleanup. Some directories are cleaned automatically, while others require user confirmation due to potential impacts.

<details>
<summary>Folders list</summary>

| Directory Name | Path | Description | Requires Confirmation |
|----------------|------|-------------|----------------------|
| System Temp | `C:\Windows\Temp` | Temporary system files | No |
| User Temp | `%USERPROFILE%\AppData\Local\Temp` | Temporary user files in Local directory | No |
| User Temp | `%USERPROFILE%\AppData\LocalLow\Temp` | Temporary user files in LocalLow directory | No |
| User Cache | `%USERPROFILE%\.cache` | Cache directory in user directory (.cache) | No |
| Internet Cache | `%USERPROFILE%\AppData\Local\Microsoft\Windows\INetCache` | Internet Explorer and Edge browser cache | No |
| Thumbnail Cache | `%USERPROFILE%\AppData\Local\Microsoft\Windows\Explorer` | Thumbnail cache for file explorer (will regenerate on demand) | No |
| Crash Dumps | `%USERPROFILE%\AppData\Local\CrashDumps` | Application crash dump files | No |
| Live Kernel Reports | `C:\Windows\LiveKernelReports` | System diagnostic reports | No |
| Event Logs | `C:\Windows\System32\winevt\Logs` | Windows event log files (system and application logs) | No |
| Delivery Optimization | `C:\Windows\SoftwareDistribution\DeliveryOptimization` | Windows Update delivery optimization cache | No |
| Windows Updates | `C:\Windows\SoftwareDistribution\Download` | Windows Update downloads | No |
| Windows.old | `C:\Windows.old` | Previous Windows installation files (removes rollback option) | No |
| Spotify Cache | `%USERPROFILE%\AppData\Local\Spotify\Data` | Spotify data cache | No |
| NVIDIA GL Cache | `%USERPROFILE%\AppData\Local\NVIDIA\GLCache` | NVIDIA OpenGL cache (may cause temporary shader recompilation) | Yes |
| NVIDIA DX Cache | `%USERPROFILE%\AppData\Local\NVIDIA\DXCache` | NVIDIA DirectX cache (may cause temporary graphics reload) | Yes |
| Prefetch | `C:\Windows\Prefetch` | System prefetch files (may slow initial program loading if cleared) | Yes |
| Recycle Bin | `C:\$Recycle.Bin` | Files in the Recycle Bin (permanent deletion) | Yes |
| Gradle Cache | `%USERPROFILE%\.gradle\caches` | Gradle build cache (may require re-downloading dependencies) | Yes |

</details>

## Requirements
- Python 3.8+
- Windows 10+
- Dependencies listed in `requirements.txt`

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/gnilobaiter/pc_cleaner
   cd pc_cleaner
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the cleaner:
```bash
python main.py
```

## Using Pre-built Binary
Download from [**releases**](https://github.com/gnilobaiter/pc_cleaner/releases) and run.