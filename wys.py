
youtube_video_url = '' # put youtube video url between single quotes


# Install packages
!pip install git+https://github.com/openai/whisper.git
!pip install yt-dlp

# import python modules
import os
from datetime import timedelta
import yt_dlp
import whisper

src_dir = 'content'
dst_dir = 'download'
ext = 'm4a'
src_audio_extension = f".{ext}"

# add work folders
sourceFolderExists = os.path.exists(src_dir)
destinationFolderExists = os.path.exists(dst_dir)

if not sourceFolderExists:
  os.mkdir("content")
if not destinationFolderExists:
  os.mkdir("download")

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    #print(f"status {d['status']}")
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')


def transcribe(audio_file_list, src_dir, dst_dir):
    lang = "en"
    model = whisper.load_model("base")

    for audio_file in audio_file_list:
        name_without_extension, file_extension = os.path.splitext(audio_file)
        # Load audio file
        audio = whisper.load_audio(f"{src_dir}/{audio_file}")

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

            srtFilename = os.path.join(f"{dst_dir}",f"{filename}.srt")
            with open(srtFilename, 'a', encoding='utf-8') as srtFile:
                srtFile.write(segment)


ydl = yt_dlp.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'})

with ydl:
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
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}


with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([youtube_video_url])

files = [f for f in os.listdir('.') if os.path.isfile(f)]
for f in files:
  filename, file_extension = os.path.splitext(f)
  if file_extension == src_audio_extension:
    print(f"found file {f}, moving to {src_dir}")
    os.replace(f,os.path.join(src_dir, f))

filesToProcess = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
print(f"filesToProcess: {filesToProcess}")

transcribe(filesToProcess, src_dir, dst_dir)

!zip -r download.zip download

#uninstall packages
#!pip uninstall --yes youtube-dl
