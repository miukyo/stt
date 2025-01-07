<p align="center">
  <a href="https://github.com/miukyo/stt">
    <img src="https://github.com/user-attachments/assets/99968b8a-18e2-4ca0-b8e5-34e49d57093d" alt="Logo" width="200" height="200">
  </a>

  <h1 align="center">STT (Speech-to-Text Transcriber Tool)</h3>

  <p align="center">
    STT is a tool that converts speech in audio files into text. It utilizes whisper.cpp for transcription and ffmpeg for processing various audio/video formats, making it easy to transcribe spoken content into written text.
</p>

## Quick start:
1. Download the STT from [here](https://github.com/miukyo/stt/releases/)
2. Install ffmpeg (required)
4. Run `stt.exe`
   
<p align="center">
<img src="https://github.com/user-attachments/assets/4acdbae8-d081-41cf-84e3-391219dd0c2d" alt="preview">
</p>

## Development
Follow these steps to set up STT on your local machine:
#### 1. Clone the Repository

Clone the project to your local machine:
```
git clone https://github.com/yourusername/stt.git
cd stt
```
#### 2. Install Dependencies

You’ll need ffmpeg and whisper.cpp for this tool to work properly.
- Install [ffmpeg](https://www.ffmpeg.org/download.html)
- Build [whisper.cpp](https://github.com/ggerganov/whisper.cpp) (prebuilt binary is available on [/lib](https://github.com/miukyo/stt/tree/master/lib) folder, if you prefer building yourself please follow instruction from their repo)

#### 3. Install Python Dependencies

Use pip to install required Python packages:

for running the program

```
pip install pywebview
```

for bundling the program into executable

```
pip install pyinstaller
```

#### 4. Usage

After installing the dependencies, you can start transcribing your audio/video files.

Run the tool with the following command:

```
python main.py
```

To bundle the program run the following command:

```
pyinstaller main.spec
```

then copy `lib` folder into `dist` folder

## Known Issues

- **This is the initial release. Please report any bugs or issues you encounter.**

## Contributing

Feel free to fork the repository, submit issues, or create pull requests to improve the tool. Contributions are welcome!
License

This project is licensed under the MIT License - see the LICENSE file for details.
