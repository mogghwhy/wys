# put your youtube video url between single quotes
youtube_video_url = '' 


# Install packages
# puttings this in the same cell because it needs to be executed before 
# the rest of the code is executed, in case if connection to runtime is lost
# a new blank runtime gets started that does not have these pre-installed
!pip install git+https://github.com/openai/whisper.git
!pip install yt-dlp


# import python modules
import os
from datetime import timedelta
import yt_dlp
import whisper

zip_archive_filename = 'captions'
src_dir = 'input'
dst_dir = 'output'
ext = 'm4a'
src_audio_extension = f".{ext}"

# add work folders
work_folders = [src_dir, dst_dir]

for folder in work_folders:
  if not os.path.exists(folder):
    os.mkdir(folder)

class MyYdlLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_ydl_progress_hook(d):
    #print(f"status {d['status']}")
    if d['status'] == 'downloading':
        print(f"{d['downloaded_bytes']} bytes downloaded")    
    if d['status'] == 'finished':
        print('Done downloading...')


def transcribe(audio_file_list, src_dir, dst_dir):
    lang = "en"
    model = whisper.load_model("base")

    for audio_file in audio_file_list:
        name_without_extension, file_extension = os.path.splitext(audio_file)
        # Load audio file
        audio = whisper.load_audio(os.path.join(f"{src_dir}",f"{audio_file}"))

        options = {
    "language": lang, # input language, if omitted is auto detected
    "task": "transcribe" # or "transcribe" if you just want transcription
}
        result = whisper.transcribe(model, audio, **options)

        segments = result['segments']
        for segment in segments:
            startTime = str(0)+str(timedelta(seconds=int(segment['start'])))+',000'
            endTime = str(0)+str(timedelta(seconds=int(segment['end'])))+',000'
            text = segment['text']
            segmentId = segment['id']+1
            segment = f"{segmentId}\n{startTime} --> {endTime}\n{text[1:] if text[0] is ' ' else text}\n\n"
            srtFilename = os.path.join(f"{dst_dir}",f"{name_without_extension}.srt")
            with open(srtFilename, 'a', encoding='utf-8') as srtFile:
                srtFile.write(segment)


ydl_opts = {'outtmpl': '%(id)s.%(ext)s'}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    result = ydl.extract_info(
        youtube_video_url,
        download=False # We just want to extract the info
    )  

if 'entries' in result:
    # Can be a playlist or a list of videos
    video = result['entries'][0]
else:
    # Just a video
    video = result

formats = video['formats']
format_id = 0

for format in formats:
  if format['resolution'] == 'audio only':    
    if format['ext'] == ext:
      format_id = format['format_id']
      break; # find first format with specific value and exit the loop
  else:
    pass
  
print(f"found audio with format_id {format_id}")

ydl_opts = {
    'format': format_id,
    'logger': MyYdlLogger(),
    'progress_hooks': [my_ydl_progress_hook],
    'paths': {'home':src_dir}
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([youtube_video_url])

process_files = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
print(f"list of files to process: {process_files}")

transcribe(process_files, src_dir, dst_dir)

!zip -r {zip_archive_filename}.zip {dst_dir}

# we can clean up installed packages if needed
#uninstall packages
#!pip uninstall --yes youtube-dl
