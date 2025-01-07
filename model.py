import os
import signal
import sys
import shutil
import subprocess
from pathlib import Path
from threading import Event

# Configuration
DEFAULT_SRC = "https://huggingface.co/ggerganov/whisper.cpp"
DEFAULT_PFX = "resolve/main/ggml"

MODELS = """
tiny
tiny.en
tiny-q5_1
tiny.en-q5_1
tiny-q8_0
base
base.en
base-q5_1
base.en-q5_1
base-q8_0
small
small.en
small.en-tdrz
small-q5_1
small.en-q5_1
small-q8_0
medium
medium.en
medium-q5_0
medium.en-q5_0
medium-q8_0
large-v1
large-v2
large-v2-q5_0
large-v2-q8_0
large-v3
large-v3-q5_0
large-v3-turbo
large-v3-turbo-q5_0
large-v3-turbo-q8_0
""".strip().split(
    "\n"
)

BOLD = "\033[1m"
RESET = "\033[0m"

stop_event = Event()


def handle_exit(signum=None, frame=None):
    print("\nTermination signal received. Stopping download...")
    stop_event.set()


def list_models():
    print("\nAvailable models:")
    model_class = ""
    for model in MODELS:
        this_model_class = model.split("-")[0].split(".")[0]
        if this_model_class != model_class:
            print(f"\n {this_model_class.capitalize()}:")
            model_class = this_model_class
        print(f" {model}", end="")
    print("\n")


def get_script_path():
    return Path(__file__).resolve().parent


def download_model(model, models_path):
    # Adjust source and prefix for specific models
    src = DEFAULT_SRC
    pfx = DEFAULT_PFX
    process = None
    if "tdrz" in model:
        src = "https://huggingface.co/akashmjn/tinydiarize-whisper.cpp"
        pfx = "resolve/main/ggml"

    model_file = f"{models_path}/ggml-{model}.bin"
    if os.path.exists(model_file):
        print(f"Model {model} already exists. Skipping download.")
        return

    download_url = f"{src}/{pfx}-{model}.bin"
    print(f"Downloading ggml model {model} from '{src}'...")

    if shutil.which("wget2"):
        process = subprocess.Popen(
            [
                "wget2",
                "--quiet",
                "--no-config",
                "--progress",
                "bar",
                "-O",
                model_file,
                download_url,
            ],
        )
    elif shutil.which("wget"):
        process = subprocess.Popen(
            [
                "wget",
                "--no-config",
                "--quiet",
                "--show-progress",
                "-O",
                model_file,
                download_url,
            ],
        )
    elif shutil.which("curl"):
        process = subprocess.Popen(
            ["curl", "-L", "--output", model_file, download_url, "| yes"],
        )
    else:
        print("Either wget or curl is required to download models.")
        sys.exit(1)

    while process.poll() is None:
        if stop_event.is_set():
            process.terminate()  # Terminate the download process
            print(f"Download of {model_file} terminated.")
            return False
    while process.poll() is not None:
        return True
    print(f"Done! Model '{model}' saved in '{models_path}/ggml-{model}.bin'")


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: {sys.argv[0]} <model> [models_path]")
        list_models()
        print("___________________________________________________________")
        print(
            f"{BOLD}.en{RESET} = english-only {BOLD}-q5_[01]{RESET} = quantized {BOLD}-tdrz{RESET} = tinydiarize\n"
        )
        sys.exit(1)

    model = sys.argv[1]
    models_path = Path(sys.argv[2]) if len(sys.argv) > 2 else get_script_path()

    if model not in MODELS:
        print(f"Invalid model: {model}")
        list_models()
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    download_model(model, models_path)


if __name__ == "__main__":
    main()
