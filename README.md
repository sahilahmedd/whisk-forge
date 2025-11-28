# WhiskForge 🎨

**WhiskForge** is a powerful Windows desktop automation tool designed to streamline image generation using **Whisk AI (Google Labs)**. It empowers creators to queue prompts, manage sessions efficiently, and build their image libraries with ease.

![WhiskForge Banner](https://via.placeholder.com/1200x300?text=WhiskForge+Automation+Tool) *<!-- Replace with actual screenshot later -->*

## 🚀 Features

- **⚡ Automated Image Generation**: Queue hundreds of prompts and let WhiskForge handle the heavy lifting.
- **🔐 Secure Session Management**: seamless authentication using your Whisk AI session cookies.
- **🎛️ Granular Control**: Customize aspect ratios (Landscape, Portrait, Square), select image models, and more.
- **💾 Smart Job Persistence**: Never lose your progress. WhiskForge tracks every job and history in a local database.
- **🖼️ Integrated Gallery**: Preview, organize, and manage your downloaded masterpieces directly within the app.
- **⏯️ Pause & Resume**: Full control over your generation queue.

## 🛠️ Installation

### Option 1: Download the Executable (Recommended)
1.  Go to the [Releases](https://github.com/sahilahmedd/whisk-forge/releases) page.
2.  Download the latest `WhiskForge.exe`.
3.  Run the executable directly. No Python installation required!

### Option 2: Run from Source
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/sahilahmedd/whisk-forge.git
    cd whisk-forge
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the application**:
    ```bash
    python run.py
    ```

## 📖 Usage

1.  **Launch WhiskForge**.
2.  **Authenticate**: Paste your Whisk AI session cookies (JSON format from a cookie exporter extension).
3.  **Configure**: Enter your prompts, choose your aspect ratio, and set the number of images.
4.  **Generate**: Click start and watch the magic happen. Images are saved to the `output` folder by default.

## 🔮 Upcoming Features (Roadmap)

We are constantly working to improve WhiskForge. Here's what's coming next:

- [ ] **Proxy Support**: Rotate IPs to avoid rate limits and bans.
- [ ] **Multi-Account Manager**: Switch between multiple Google accounts seamlessly.
- [ ] **Advanced Prompting**: Import prompts from `.txt` or `.csv` files, and use prompt randomizers/wildcards.
- [ ] **Image Upscaling**: Integrated upscaling for high-resolution outputs.
- [ ] **Dark/Light Mode Toggle**: Customize the UI to your preference.
- [ ] **Auto-Updater**: Get the latest features automatically.

## ⚠️ Disclaimer

**WhiskForge is an unofficial tool and is not affiliated with Google or Whisk AI.**
This tool is for **educational purposes only**. Automating usage of services may violate their Terms of Service. The developers are not responsible for any account bans or issues that may arise from using this tool. Please use responsibly.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
