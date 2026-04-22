# PC Cleaner

A system cleanup utility for Windows.

## Features
* Cleans system and user temporary files.
* Cleans browser, application, development and launcher caches.
* Flushes DNS cache.
* Purges pip, npm, yarn, gradle caches.

## Cleaned Directories
Below is a list of directories that PC Cleaner targets for cleanup. Some directories are cleaned automatically, while others require user confirmation due to potential impacts.

<details>
<summary>Folders list</summary>

| Directory Name          | Path                                                                 | Description                                | Requires Confirmation |
| ----------------------- | -------------------------------------------------------------------- | ------------------------------------------ | --------------------- |
| System Temp             | `C:\Windows\Temp`                                                    | Temporary system files                     | No                    |
| User Temp               | `%USERPROFILE%\AppData\Local\Temp`                                   | Temporary user files in Local directory    | No                    |
| User Temp               | `%USERPROFILE%\AppData\LocalLow\Temp`                                | Temporary user files in LocalLow directory | No                    |
| User Cache              | `%USERPROFILE%\.cache`                                               | Cache directory in user directory (.cache) | No                    |
| Internet Cache          | `%USERPROFILE%\AppData\Local\Microsoft\Windows\INetCache`            | Internet Explorer and Edge browser cache   | No                    |
| Thumbnail Cache         | `%USERPROFILE%\AppData\Local\Microsoft\Windows\Explorer`             | Thumbnail cache for file explorer          | No                    |
| Crash Dumps             | `%USERPROFILE%\AppData\Local\CrashDumps`                             | Application crash dump files               | No                    |
| Live Kernel Reports     | `C:\Windows\LiveKernelReports`                                       | System diagnostic reports                  | No                    |
| Event Logs              | `C:\Windows\System32\winevt\Logs`                                    | Windows event log files                    | No                    |
| Delivery Optimization   | `C:\Windows\SoftwareDistribution\DeliveryOptimization`               | Windows Update delivery optimization cache | No                    |
| Windows Updates         | `C:\Windows\SoftwareDistribution\Download`                           | Windows Update downloads                   | No                    |
| Windows.old             | `C:\Windows.old`                                                     | Previous Windows installation files        | No                    |
| Spotify Cache           | `%USERPROFILE%\AppData\Local\Spotify\Data`                           | Spotify data cache                         | No                    |
| Windows Error Reporting | `%USERPROFILE%\AppData\Local\Microsoft\Windows\WER`                  | Windows Error Reporting crash reports      | No                    |
| Microsoft Store Cache   | `%LOCALAPPDATA%\Packages\Microsoft.WindowsStore_8wekyb3d8bbwe\LocalCache` | Microsoft Store local cache           | No                    |
| Windows WebCache        | `%LOCALAPPDATA%\Microsoft\Windows\WebCache`                          | Windows web component cache                | No                    |
| Pytest Cache            | `%USERPROFILE%\.pytest_cache`                                        | Python pytest cache                        | No                    |
| Ruff Cache              | `%USERPROFILE%\.cache\ruff`                                         | Ruff linter cache                          | No                    |
| Mypy Cache              | `%USERPROFILE%\.mypy_cache`                                         | Mypy type checker cache                    | No                    |
| Corepack Cache          | `%LOCALAPPDATA%\node\corepack`                                      | Node Corepack package manager cache        | No                    |
| pip Cache               | `%USERPROFILE%\AppData\Local\pip\cache`                              | Python pip package cache                   | No                    |
| npm Cache               | `%USERPROFILE%\AppData\Local\npm-cache`                              | npm package manager cache                  | No                    |
| Yarn Cache              | `%USERPROFILE%\AppData\Local\Yarn\Cache`                             | Yarn package manager cache                 | No                    |
| Visual Studio Cache     | `%USERPROFILE%\AppData\Local\Microsoft\VisualStudio`                 | Visual Studio local cache files            | No                    |
| VS Code Cache           | `%APPDATA%\Code\Cache`                                               | Visual Studio Code cache                   | No                    |
| VS Code Cached Data     | `%APPDATA%\Code\CachedData`                                          | Visual Studio Code cached data             | No                    |
| Edge Cache              | `%USERPROFILE%\AppData\Local\Microsoft\Edge\User Data\Default\Cache` | Microsoft Edge browser cache               | Yes                   |
| Chrome Cache            | `%USERPROFILE%\AppData\Local\Google\Chrome\User Data\Default\Cache`  | Google Chrome browser cache                | Yes                   |
| Chrome Code Cache       | `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache`          | Google Chrome JavaScript code cache        | Yes                   |
| Chrome GPU Cache        | `%LOCALAPPDATA%\Google\Chrome\User Data\Default\GPUCache`            | Google Chrome GPU cache                    | Yes                   |
| Chrome Service Worker Cache | `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Service Worker\CacheStorage` | Google Chrome service worker offline cache | Yes             |
| Edge Code Cache         | `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Code Cache`         | Microsoft Edge JavaScript code cache       | Yes                   |
| Edge GPU Cache          | `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\GPUCache`           | Microsoft Edge GPU cache                   | Yes                   |
| Edge Service Worker Cache | `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Service Worker\CacheStorage` | Microsoft Edge service worker offline cache | Yes              |
| Direct3D Shader Cache   | `%LOCALAPPDATA%\D3DSCache`                                           | Direct3D shader cache                      | Yes                   |
| NVIDIA GL Cache         | `%USERPROFILE%\AppData\Local\NVIDIA\GLCache`                         | NVIDIA OpenGL cache                        | Yes                   |
| NVIDIA DX Cache         | `%USERPROFILE%\AppData\Local\NVIDIA\DXCache`                         | NVIDIA DirectX cache                       | Yes                   |
| Prefetch                | `C:\Windows\Prefetch`                                                | System prefetch files                      | Yes                   |
| Recycle Bin             | `C:\$Recycle.Bin`                                                    | Files in the Recycle Bin                   | Yes                   |
| Gradle Cache            | `%USERPROFILE%\.gradle\caches`                                       | Gradle build cache                         | Yes                   |
| Gradle Temp             | `%USERPROFILE%\.gradle\.tmp`                                         | Gradle temp files                          | Yes                   |
| Windows Logs            | `C:\Windows\Logs`                                                    | Windows diagnostic and update logs         | Yes                   |
| Discord Cache           | `%APPDATA%\discord\Cache`                                            | Discord application cache                  | Yes                   |
| Discord Code Cache      | `%APPDATA%\discord\Code Cache`                                       | Discord code cache                         | Yes                   |
| Steam HTML Cache        | `%LOCALAPPDATA%\Steam\htmlcache`                                     | Steam embedded browser cache               | Yes                   |
| Steam Shader Cache      | `%LOCALAPPDATA%\Steam\shadercache`                                   | Steam shader cache                         | Yes                   |
| Epic Games Cache        | `%LOCALAPPDATA%\EpicGamesLauncher\Saved\webcache`                    | Epic Games Launcher web cache              | Yes                   |
| Battle.net Cache        | `%PROGRAMDATA%\Battle.net\Cache`                                     | Battle.net application cache               | Yes                   |
| Adobe Media Cache       | `%APPDATA%\Adobe\Common\Media Cache Files`                           | Adobe media cache files                    | Yes                   |

</details>

## Requirements
* Python 3.8+
* Windows 10+
* Dependencies listed in `requirements.txt`

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