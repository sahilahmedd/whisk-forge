# WhiskForge

WhiskForge is a Windows desktop automation tool for generating images using Whisk AI (Google Labs). It allows users to queue prompts, manage sessions, and download generated images automatically.

## Features

- **Automated Image Generation**: Queue multiple prompts and let the tool handle the generation process.
- **Session Management**: Uses session cookies to authenticate with Whisk AI.
- **Customizable Settings**: Configure aspect ratios, image models, and more.
- **Job Persistence**: Tracks jobs and history using a local database.
- **Gallery View**: Preview and manage downloaded images.

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    python run.py
    ```

## Usage

1.  Launch WhiskForge.
2.  Paste your Whisk AI session cookies (JSON format).
3.  Enter your prompts and configure settings.
4.  Start the generation process.

## Disclaimer

This tool is for educational purposes only. Automating usage of services may violate their Terms of Service. Use responsibly and at your own risk.
