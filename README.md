# PC Cleaner

A Windows cleanup utility with guarded system cleanup, reusable presets, and a fully mocked test suite.

## Features

- Cleans Windows, browser, application, development-tool, launcher, and graphics caches.
- Removes JetBrains AF_UNIX socket reparse points without following links; protected directory junctions are skipped silently.
- Empties Recycle Bins on all drives through the Windows Shell API.
- Flushes the DNS resolver cache.
- Saves the last yes/no cleanup choices in `%APPDATA%\PC_CLEANER\preset.json` and offers to reuse them at the next launch.
- Requires confirmation for cleanup that removes diagnostics, triggers large downloads/rebuilds, or has another meaningful side effect.

## Download

Download the latest `.exe` from [Releases](https://github.com/gnilobaiter/pc_cleaner/releases) and run it—no Python installation is required.

## Cleanup order

Targets are presented in the following order. Dynamic Firefox and JetBrains entries are added only when matching profile/product directories exist; their prompts include the profile or product directory name.

### Windows and system

| Directory | Path | Confirmation |
| --- | --- | --- |
| System Temp | `%SystemRoot%\Temp` | No |
| Delivery Optimization | `%SystemRoot%\SoftwareDistribution\DeliveryOptimization` | No |
| Windows Updates | `%SystemRoot%\SoftwareDistribution\Download` | Yes |
| Windows Logs | `%SystemRoot%\Logs` | Yes |
| Event Logs | `%SystemRoot%\System32\winevt\Logs` | Yes |
| Prefetch | `%SystemRoot%\Prefetch` | Yes |
| Live Kernel Reports | `%SystemRoot%\LiveKernelReports` | Yes |
| Windows.old | `%SystemDrive%\Windows.old` | Yes |
| Recycle Bin | All drives | Yes |

### User temporary files and diagnostics

| Directory | Path | Confirmation |
| --- | --- | --- |
| User Temp | `%LOCALAPPDATA%\Temp` | No |
| User Temp (LocalLow) | `%USERPROFILE%\AppData\LocalLow\Temp` | No |
| User Cache | `%USERPROFILE%\.cache` | Yes |
| Thumbnail Cache | `%LOCALAPPDATA%\Microsoft\Windows\Explorer` | No |
| Internet Cache | `%LOCALAPPDATA%\Microsoft\Windows\INetCache` | No |
| Windows WebCache | `%LOCALAPPDATA%\Microsoft\Windows\WebCache` | No |
| Microsoft Store Cache | `%LOCALAPPDATA%\Packages\Microsoft.WindowsStore_8wekyb3d8bbwe\LocalCache` | No |
| Crash Dumps | `%LOCALAPPDATA%\CrashDumps` | Yes |
| Windows Error Reporting | `%LOCALAPPDATA%\Microsoft\Windows\WER` | Yes |
| System Error Reporting | `%PROGRAMDATA%\Microsoft\Windows\WER` | Yes |

### Browsers

| Directory | Path | Confirmation |
| --- | --- | --- |
| Edge Cache | `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache` | Yes |
| Edge Code Cache | `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Code Cache` | Yes |
| Edge GPU Cache | `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\GPUCache` | Yes |
| Edge Service Worker Cache | `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Service Worker\CacheStorage` | Yes |
| Chrome Cache | `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache` | Yes |
| Chrome Code Cache | `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache` | Yes |
| Chrome GPU Cache | `%LOCALAPPDATA%\Google\Chrome\User Data\Default\GPUCache` | Yes |
| Chrome Service Worker Cache | `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Service Worker\CacheStorage` | Yes |
| Brave Cache | `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Cache` | Yes |
| Opera Cache | `%LOCALAPPDATA%\Opera Software\Opera Stable\Cache` | Yes |
| Firefox Cache | `%LOCALAPPDATA%\Mozilla\Firefox\Profiles\*\cache2` | Yes |

### Development tools

| Directory | Path | Confirmation |
| --- | --- | --- |
| Pytest Cache | `%USERPROFILE%\.pytest_cache` | No |
| Ruff Cache | `%USERPROFILE%\.cache\ruff` | No |
| Mypy Cache | `%USERPROFILE%\.mypy_cache` | No |
| pip Cache | `%LOCALAPPDATA%\pip\cache` | No |
| uv Cache | `%LOCALAPPDATA%\uv\cache` | No |
| Poetry Cache | `%LOCALAPPDATA%\pypoetry\Cache` | No |
| npm Cache | `%LOCALAPPDATA%\npm-cache` | No |
| Yarn Cache | `%LOCALAPPDATA%\Yarn\Cache` | No |
| pnpm Cache | `%LOCALAPPDATA%\pnpm-cache` | No |
| Corepack Cache | `%LOCALAPPDATA%\node\corepack` | No |
| Bun Cache | `%LOCALAPPDATA%\bun\install\cache` | No |
| NuGet HTTP Cache | `%LOCALAPPDATA%\NuGet\v3-cache` | No |
| NuGet Plugins Cache | `%LOCALAPPDATA%\NuGet\plugins-cache` | No |
| Go Build Cache | `%LOCALAPPDATA%\go-build` | Yes |
| Cargo Registry Cache | `%USERPROFILE%\.cargo\registry\cache` | Yes |
| Gradle Cache | `%USERPROFILE%\.gradle\caches` | Yes |
| Gradle Temp | `%USERPROFILE%\.gradle\.tmp` | Yes |
| Visual Studio Cache | `%LOCALAPPDATA%\Microsoft\VisualStudio` | Yes |
| VS Code Cache | `%APPDATA%\Code\Cache` | No |
| VS Code Cached Data | `%APPDATA%\Code\CachedData` | No |
| VS Code Logs | `%APPDATA%\Code\logs` | No |
| JetBrains Cache | `%LOCALAPPDATA%\JetBrains\*\caches` | Yes |
| JetBrains Logs | `%LOCALAPPDATA%\JetBrains\*\log` | No |

### Communication and media applications

| Directory | Path | Confirmation |
| --- | --- | --- |
| Discord Cache | `%APPDATA%\discord\Cache` | Yes |
| Discord Code Cache | `%APPDATA%\discord\Code Cache` | Yes |
| Teams Cache | `%APPDATA%\Microsoft\Teams\Cache` | Yes |
| Slack Cache | `%APPDATA%\Slack\Cache` | Yes |
| Zoom Cache | `%APPDATA%\Zoom\data` | Yes |
| Spotify Cache | `%LOCALAPPDATA%\Spotify\Data` | Yes |
| Adobe Media Cache | `%APPDATA%\Adobe\Common\Media Cache Files` | Yes |

### Game launchers

| Directory | Path | Confirmation |
| --- | --- | --- |
| Steam HTML Cache | `%LOCALAPPDATA%\Steam\htmlcache` | Yes |
| Steam Shader Cache | `%LOCALAPPDATA%\Steam\shadercache` | Yes |
| Epic Games Cache | `%LOCALAPPDATA%\EpicGamesLauncher\Saved\webcache` | Yes |
| Battle.net Cache | `%PROGRAMDATA%\Battle.net\Cache` | Yes |

### Graphics

| Directory | Path | Confirmation |
| --- | --- | --- |
| Direct3D Shader Cache | `%LOCALAPPDATA%\D3DSCache` | Yes |
| NVIDIA GL Cache | `%LOCALAPPDATA%\NVIDIA\GLCache` | Yes |
| NVIDIA DX Cache | `%LOCALAPPDATA%\NVIDIA\DXCache` | Yes |
| Intel Shader Cache | `%LOCALAPPDATA%\Intel\ShaderCache` | Yes |
| AMD DX Cache | `%LOCALAPPDATA%\AMD\DxCache` | Yes |

## Development

Requirements: Python 3.8+ for the application and Python 3.10+ for the test toolchain.

```powershell
git clone https://github.com/gnilobaiter/pc_cleaner
cd pc_cleaner
python -m pip install -r requirements.txt
python main.py
```

### Tests

All destructive filesystem deletion, Recycle Bin, DNS, input, preset, and CLI effects are isolated or mocked. CI enforces at least 95% line coverage.

```powershell
python -m pip install -r requirements-test.txt
python -m pytest tests --cov=src --cov=main --cov-report=term-missing --cov-fail-under=95
python -m ruff check .
```

### Build

```bat
build.bat
```

The executable is created at `dist\PC_CLEANER.exe`.
