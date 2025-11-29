# Building WhiskForge on macOS

This guide explains how to build the WhiskForge application for macOS.

## Prerequisites

1.  **Python 3.10+**: Ensure Python is installed.
    ```bash
    python3 --version
    ```
2.  **Git**: To clone the repository (if not already present).

## Setup

1.  **Create a Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install pyinstaller
    ```

## Building the Application

1.  **Run PyInstaller**:
    To create a macOS `.app` bundle, use the `--windowed` (or `-w`) flag.
    ```bash
    pyinstaller WhiskForge.spec --noconfirm --windowed
    ```

2.  **Locate the App**:
    The built application will be at `dist/WhiskForge.app`.

## Creating a .dmg (Optional)

To create a distributable `.dmg` file, you can use a tool like `create-dmg`.

1.  **Install create-dmg**:
    ```bash
    brew install create-dmg
    ```

2.  **Create the DMG**:
    ```bash
    create-dmg \
      --volname "WhiskForge Installer" \
      --volicon "assets/logo.png" \
      --window-pos 200 120 \
      --window-size 800 400 \
      --icon-size 100 \
      --icon "WhiskForge.app" 200 190 \
      --hide-extension "WhiskForge.app" \
      --app-drop-link 600 185 \
      "WhiskForge-Installer.dmg" \
      "dist/WhiskForge.app"
    ```

## Troubleshooting

-   **Permission Issues**: If you encounter permission errors, try `chmod +x dist/WhiskForge.app/Contents/MacOS/WhiskForge`.
-   **Gatekeeper**: macOS might block the app because it's not signed. You can usually bypass this by right-clicking the app and selecting "Open", or via System Settings > Privacy & Security.
