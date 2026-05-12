from .downloader import AdobeDownloader
from .ffmpeg import AdobeFFmpeg
from .beautiful_logger import get_main_logger

def download_and_export(meeting_url: str, output_file_name: str = "final_video.mp4"):
    # Create logger for this function
    logger = get_main_logger()
    
    logger.rule(f"Processing: {output_file_name}")
    logger.url(f"Source URL: {meeting_url}")
    
    try:
        # Download phase
        downloader = AdobeDownloader()
        extract_url = downloader.download_and_extract(meeting_url)
        
        # FFmpeg phase
        adffmpeg = AdobeFFmpeg()
        adffmpeg.find_and_sort_segments(extract_url)
        adffmpeg.concat_segments()
        adffmpeg.merge_videos_and_audios(output_file_name=output_file_name)
        
        logger.success(f"Successfully processed: {output_file_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process {output_file_name}: {e}")
        raise