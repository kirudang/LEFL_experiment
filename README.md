# AI-Generated Audiovisual Content to Foster Civic Literacy 

This project converts structured educational text into narrated videos with synchronized captions and a static background image. It is designed for creating short explainer videos for topics like finance, law, and education.

## Pipeline Overview

1. **Setup and Library Import**  
   Load required libraries (MoviePy, Coqui TTS, etc.) and configure logging.

2. **Text Processing**  
   - Reads structured `.txt` files (bullet points, numbered items).
   - Splits content into narration-ready sentences.

3. **Text-to-Speech Conversion**  
   - Converts each sentence into audio using [Coqui TTS](https://github.com/coqui-ai/TTS).
   - Saves outputs as `.wav` files.

4. **Video Creation with Image Background**  
   - Pairs each audio file with a background image.
   - Creates short video segments for each sentence.

5. **Caption Synchronization**  
   - Adds on-screen text for each sentence.
   - Highlights current sentence in blue while keeping prior ones in black.

6. **Final Video Assembly**  
   - Concatenates all video segments with optional pause intervals.
   - Optionally creates a single continuous video with layered captions.

## Requirements

Please install all packages in the `requirements.txt` file.

- Python 3.7+
- [MoviePy](https://github.com/Zulko/moviepy)
- [Coqui TTS](https://github.com/coqui-ai/TTS)
- ImageMagick (required by MoviePy for text rendering)

### Installation

```bash
pip install moviepy TTS
```

Make sure to configure the ImageMagick path if needed:

```bash
export IMAGEMAGICK_BINARY=/opt/homebrew/bin/magick  # Adjust to your system
```

## How to Run
1. Place your structured text file (e.g., `finance.txt`) and background image (e.g., `background_female.png`) in the `data/` directory.
2. Update the `main.py` script to point to your text file and image file if necessary.
3. Run the script:

```bash
python pipeline.py
```
### Output
The script will generate a final video file named `xxx.mp4` in the project root directory.
   
