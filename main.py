import atexit
import re
import subprocess
import webview
from bottle import Bottle, static_file, request
import os
import shutil
import tempfile
from threading import Thread
import model
import re

file_types = [
    "Audio files (*.aac;*.ac3;*.aiff;*.alac;*.amr;*.ape;*.au;*.dts;*.flac;*.gsm;*.m4a;*.m4b;*.m4r;*.mka;*.mp2;*.mp3;*.mpc;*.oga;*.ogg;*.opus;*.ra;*.raw;*.shn;*.tak;*.tta;*.voc;*.wav;*.wma;*.wv)",
    "Video files (*.3gp;*.avi;*.flv;*.mkv;*.mov;*.mp4;*.m4v;*.mpeg;*.mpg;*.ogv;*.webm;*.wmv;*.yuv)",
]

bott = Bottle()

@bott.route("/audio", method="GET")
def serve_audio():
    filepath = request.query.filepath
    return static_file(os.path.basename(filepath), root=os.path.dirname(filepath))


def start_bottle_server():
    bott.run(host="localhost", port=9321)


server_thread = Thread(target=start_bottle_server, daemon=True)
server_thread.start()


class App:
    def __init__(self):
        self.audio_list = []
        self.ffmpeg = None
        self.whisper = None
        self.output_path = None
        self.downloadmodel = None
        self.output_format = "txt"
        self.language = "auto"
        self.model_path = ""

        def stop_sub():
            print("Terminating processes...")
            if self.ffmpeg is not None:
                self.ffmpeg.terminate()
            if self.whisper is not None:
                self.whisper.terminate()
            model.handle_exit()

        atexit.register(stop_sub)

    def log(self, message, with_newline=True):
        window = webview.windows[0]
        window.evaluate_js(
            f"const output = document.getElementById('output'); output.innerHTML += `{with_newline and '\n' or ''}{message}`; output.scrollTop = output.scrollHeight;"
        )
        print(message)

    def get_audio_url(self, filepath):
        return f"http://localhost:9321/audio?filepath={filepath}"

    def remove_audio(self, index):
        self.audio_list.pop(index)
        return self.audio_list

    def reset_audio_list(self):
        self.audio_list = []

    def set_output_format(self, format):
        self.output_format = format

    def set_language(self, language):
        self.language = language
    
    def set_model(self, model):
        if model == 'custom':
            mod = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=["Binary file (*.bin)"],
            )
            if mod[0]:
                self.model_path = mod[0]
                webview.windows[0].evaluate_js(
                    f'document.getElementById("custommodel").innerText = "Custom: {self.model_path.split("\\").pop()}"'
                )
        else:
            self.model_path = f"lib/models/ggml-{model}.bin"

    def open_audio_file(self):
        result = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=file_types,
        )
        if self.output_path is None:
            self.output_path = "/".join(result[0].split("\\")[:-1])

        webview.windows[0].evaluate_js(
            f'const output = document.getElementById("output-path");output.innerHTML = "{self.output_path}";output.style.display = "block";'
        )

        for file in result:
            self.audio_list.append(
                {
                    "name": file.split("\\").pop(),
                    "url": self.get_audio_url(file),
                    "path": file.replace("\\", "/"),
                }
            )

        return self.audio_list

    def set_output_folder(self):
        result = webview.windows[0].create_file_dialog(
            webview.FOLDER_DIALOG,
            allow_multiple=False,
        )
        self.output_path = "/".join(result[0].split("\\"))
        return result[0]

    def stop_sub(self):
        self.log("Terminating processes...")
        if self.ffmpeg is not None:
            self.ffmpeg.terminate()
        if self.whisper is not None:
            self.whisper.terminate()
        model.handle_exit()
        webview.windows[0].evaluate_js("changeState('stop')")

    def run_sub(self):
        window = webview.windows[0]
        tempdir = tempfile.gettempdir().replace("\\", "/")
        window.evaluate_js("changeState('run')")
        if self.model_path == "":
            self.log("Please select the model")
        if not os.path.exists(self.model_path):
            confirm = webview.windows[0].create_confirmation_dialog(
                "Model not found",
                "The model file is not found. Do you want to download it?",
            )
            if confirm:
                self.log("Downloading model (please wait)...")
                download = model.download_model(
                    re.search(r"(?<=ggml-)(.*?)(?=\.bin)", self.model_path).group(0), os.path.dirname(self.model_path)
                )
                if not download:
                    window.evaluate_js("changeState('stop')")
                    self.log("Model download failed.")
                    return
            else:
                window.evaluate_js("changeState('stop')")
                self.log("Model not found.")
                return

        for i, list in enumerate(self.audio_list):
            self.ffmpeg = subprocess.Popen(
                f'ffmpeg -i "{list["path"]}" -y -vn -ar 16000 -ac 1 "{tempdir}/{list["name"]}.wav"',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf8",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            while True:
                output = self.ffmpeg.stdout.readline() + self.ffmpeg.stderr.readline()
                if output:
                    self.log(output, False)
                if self.ffmpeg.poll() is not None and output == "":
                    break

            if self.ffmpeg.returncode != 0:
                self.log(f"Command failed with return code {self.whisper.returncode}")
                break

            self.log(f"language: {self.language}output format: {self.output_format}")
            self.whisper = subprocess.Popen(
                f'lib/whisper-cli.exe -sns -pp -l {self.language} -o{self.output_format} -m "{self.model_path}" "{tempdir}/{list["name"]}.wav"',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf8",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            os.set_blocking(self.whisper.stdout.fileno(), False)
            os.set_blocking(self.whisper.stderr.fileno(), False)

            while True:
                output = self.whisper.stdout.readline() + self.whisper.stderr.readline()
                if output:
                    progress = re.search(r"progress\s*=\s*(\d+)%", output)
                    if progress:
                        window.evaluate_js(
                            f'document.querySelector("#audiolist #audio{i}").style.width = "{progress.group(1)}%";'
                        )
                    self.log(output, False)
                if self.whisper.poll() is not None and output == "":
                    break

            if self.whisper.returncode == 0:
                shutil.move(
                    f"{tempdir}/{list['name']}.wav.{self.output_format}",
                    f"{self.output_path}/{list['name'].split('.')[:-1][0]}.{self.output_format}",
                )
                os.remove(f"{tempdir}/{list['name']}.wav")
                self.log(f"Finished transcription of {i + 1} files")
                window.evaluate_js("changeState('stop')")

            if self.whisper.returncode != 0:
                window.evaluate_js("changeState('stop')")
                self.log(self.whisper.stderr.read())
                self.log(self.whisper.stdout.read())
                self.log(f"Command failed with return code {self.whisper.returncode}")
                break


webview.create_window(
    "STT", "ui/index.html", js_api=App(), min_size=(800, 600), width=800, height=600
)
webview.start(icon="ui/icon.ico")
