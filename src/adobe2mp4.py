from .downloader import AdobeDownloader
from .ffmpeg import AdobeFFmpeg


def download_and_export(meeting_url:str,output_file_name:str="final_video.mp4"):
    downloader = AdobeDownloader()
    print("Downloading meeting zip file...")
    extract_url = downloader.download_and_extract(meeting_url)
    adffmpeg = AdobeFFmpeg()
    print("Finding video and audio segments...")
    adffmpeg.find_and_sort_segments(extract_url)
    print("Concatenating video and audio segments...")
    adffmpeg.concat_segments()
    print("Merging video and audio into final MP4...")
    adffmpeg.merge_videos_and_audios(output_file_name=output_file_name)
    

