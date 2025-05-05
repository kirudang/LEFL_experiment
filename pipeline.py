# #Pipeline Overview
# 0. Setup and Import Libraries
# 1. Text Processing
# 2. Text-to-Speech Conversion
# 3. Video Creation with Image Background
# 4. Caption Synchronization
# 5. Final Video Assembly


import os
os.environ["IMAGEMAGICK_BINARY"] = "/opt/homebrew/bin/magick"  # Adjust this if needed

import re
import logging
from TTS.api import TTS
from moviepy.editor import (
    ImageClip, concatenate_videoclips, AudioFileClip,
    TextClip, CompositeVideoClip, VideoFileClip, ColorClip, concatenate_audioclips
)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize TTS
tts = TTS(model_name="tts_models/en/ljspeech/vits", progress_bar=True)


# -------------------- 1. Text Processing --------------------
def process_text(document_path):
    try:
        with open(document_path, 'r') as file:
            lines = [line.strip() for line in file if line.strip()]

        sentences = []
        buffer = ""

        for line in lines:
            if line.startswith("-"):
                if buffer:
                    sentences.append(buffer.strip())  # Flush title like "Key terms include:"
                    buffer = ""
                sentences.append(line)
            elif re.match(r"^\d+\.\s", line):
                if buffer:
                    sentences.extend(split_sentences(buffer.strip()))
                    buffer = ""
                sentences.append(line)
            else:
                buffer += " " + line if buffer else line

        if buffer:
            sentences.extend(split_sentences(buffer.strip()))

        logging.info(f"Processed text into {len(sentences)} sentences.")
        return sentences

    except Exception as e:
        logging.error(f"Error processing text: {e}")
        raise

def split_sentences(text):
    bullet_matches = re.findall(r'-\s?.+?:\s?.+?\.', text)
    if bullet_matches and len(bullet_matches) >= 2:
        return bullet_matches
    return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)

# -------------------- 2. Text-to-Speech Conversion --------------------
def text_to_speech(sentences, output_dir="audio"):
    os.makedirs(output_dir, exist_ok=True)
    audio_files = []
    for i, sentence in enumerate(sentences):
        try:
            output_path = f"{output_dir}/sentence_{i}.wav"
            tts.tts_to_file(text=sentence, file_path=output_path)
            audio_files.append(output_path)
        except Exception as e:
            logging.error(f"Error generating audio for sentence {i}: {e}")
            raise
    logging.info(f"Generated {len(audio_files)} audio files.")
    return audio_files

# -------------------- 3. Create Video Segments --------------------
def create_video_segments(image_path, audio_files, output_dir="video_segments"):
    os.makedirs(output_dir, exist_ok=True)
    video_segments = []
    try:
        image_clip = ImageClip(image_path)
        for i, audio_file in enumerate(audio_files):
            audio = AudioFileClip(audio_file)
            segment = image_clip.set_duration(audio.duration).set_audio(audio)
            output_path = f"{output_dir}/segment_{i}.mp4"
            segment.write_videofile(output_path, fps=24, codec='libx264', verbose=False, logger=None)
            video_segments.append(output_path)
        logging.info(f"Created {len(video_segments)} video segments.")
    except Exception as e:
        logging.error(f"Error creating video segments: {e}")
        raise
    return video_segments

# -------------------- 4. Add Captions with Progressive Highlighting --------------------
def add_captions(sentences, video_segments, fontsize=40, position=(50, 50),
                 wrap_width_ratio=0.85, line_spacing=10, align='West',
                 output_dir="final_segments", background_image_path=None):
    os.makedirs(output_dir, exist_ok=True)
    final_segments = []
    cumulative_sentences = []

    try:
        for i, (video_path, sentence) in enumerate(zip(video_segments, sentences)):
            cumulative_sentences.append(sentence)
            video = VideoFileClip(video_path)

            # Load persistent background once for each segment
            if background_image_path:
                base = (ImageClip(background_image_path)
                        .set_duration(video.duration)
                        .resize(video.size)
                        .set_fps(video.fps)
                        .set_audio(video.audio))  # Reuse the audio from the original segment
            else:
                base = video  # fallback if no image passed

            text_layers = []
            y_offset = position[1]
            max_width = int(video.w * wrap_width_ratio)

            for j, s in enumerate(cumulative_sentences):
                try:
                    txt = TextClip(
                        s,
                        fontsize=fontsize,
                        color='blue' if j == i else 'black',
                        font="DejaVu-Sans",
                        method='caption',
                        size=(max_width, None),
                        align=align
                    ).set_position((position[0], y_offset)).set_duration(video.duration)
                    text_layers.append(txt)
                    y_offset += txt.size[1] + line_spacing
                except Exception as e:
                    logging.warning(f"Failed to render sentence {j}: {s} — {e}")

            final_clip = CompositeVideoClip([base] + text_layers)
            output_path = f"{output_dir}/final_segment_{i}.mp4"
            final_clip.write_videofile(output_path, fps=24, codec='libx264', verbose=False, logger=None)
            final_segments.append(output_path)

        logging.info(f"✅ Added progressive captions to {len(final_segments)} segments.")
        return final_segments

    except Exception as e:
        logging.error(f"Error adding captions: {e}")
        raise

# -------------------- 5. Combine Video Segments --------------------
def combine_segments(final_segments, image_path, output_file="final_video.mp4", pause_duration=0.3):
    try:
        clips = []
        for segment in final_segments:
            clip = VideoFileClip(segment)
            clips.append(clip)

            # Add pause using the same background image
            pause = (ImageClip(image_path)
                     .set_duration(pause_duration)
                     .resize(clip.size)
                     .set_fps(clip.fps)
                     .set_audio(None))  # No sound
            clips.append(pause)

        final_clip = concatenate_videoclips(clips[:-1])  # remove final trailing pause
        final_clip.write_videofile(output_file, fps=24, codec='libx264', verbose=False, logger=None)
        logging.info(f"Final video created: {output_file}")
        return final_clip
    except Exception as e:
        logging.error(f"Error combining video segments: {e}")
        raise
# -------------------- Main Pipeline --------------------
def text_image_to_video(text_path, image_path, final_output="educational_video.mp4",
                        fontsize=40, text_position=(50, 50),
                        wrap_width_ratio=0.85, line_spacing=10, align='West'):
    try:
        sentences = process_text(text_path)
        audio_files = text_to_speech(sentences)

        # Get total audio duration
        audio_clips = [AudioFileClip(f) for f in audio_files]
        total_duration = sum([clip.duration for clip in audio_clips])
        full_audio = concatenate_audioclips(audio_clips)

        # Use 1 persistent background
        background = (ImageClip(image_path)
              .set_duration(total_duration)
              .set_fps(24))
        background = background.set_audio(full_audio)

        # Add cumulative captions at correct timestamps
        clips = []
        current_time = 0
        text_layers = []
        y_offset = text_position[1]
        cumulative_sentences = []

        for i, (sentence, audio_path) in enumerate(zip(sentences, audio_files)):
            duration = AudioFileClip(audio_path).duration
            cumulative_sentences.append(sentence)

            y = y_offset
            for j, s in enumerate(cumulative_sentences):
                color = 'blue' if j == i else 'black'
                txt = TextClip(
                    s,
                    fontsize=fontsize,
                    color=color,
                    font="DejaVu-Sans",
                    method='caption',
                    size=(int(background.w * wrap_width_ratio), None),
                    align=align
                ).set_position((text_position[0], y)).set_start(current_time).set_duration(duration)
                text_layers.append(txt)
                y += txt.size[1] + line_spacing

            current_time += duration

        final = CompositeVideoClip([background] + text_layers)
        final.write_videofile(final_output, fps=24, codec='libx264', verbose=False, logger=None)
        logging.info(f"✅ Video created successfully: {final_output}")
        return final_output

    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        raise

# -------------------- Run --------------------
if __name__ == "__main__":
    text_path = "data/finance.txt"
    image_path = "data/background_female.png"
    final_output = "02.Finance.mp4"

    try:
        logging.info("Starting the video creation pipeline...")
        text_image_to_video(
            text_path,
            image_path,
            final_output,
            fontsize=28,
            text_position=(570, 170),
            wrap_width_ratio=0.6,
            line_spacing=12,
            align='West'  # Options: 'West' (left), 'Center', 'East' (right)
        )
        logging.info(f"Video created successfully: {final_output}")
    except Exception as e:
        logging.error(f"Pipeline execution failed: {e}")