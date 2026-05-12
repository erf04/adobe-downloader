from .downloader import AdobeDownloader
from .ffmpeg import AdobeFFmpeg
import logging

def download_and_export(meeting_url: str, output_file_name: str = "final_video.mp4"):
    # Create logger for this function
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting download and export process")
    logger.info(f"Meeting URL: {meeting_url}")
    logger.info(f"Output file: {output_file_name}")
    
    try:
        downloader = AdobeDownloader()
        logger.info("Downloading meeting zip file...")
        extract_url = downloader.download_and_extract(meeting_url)
        logger.info(f"Extracted to: {extract_url}")
        
        adffmpeg = AdobeFFmpeg()
        
        logger.info("Finding video and audio segments...")
        adffmpeg.find_and_sort_segments(extract_url)
        
        logger.info("Concatenating video and audio segments...")
        adffmpeg.concat_segments()
        
        logger.info("Merging video and audio into final MP4...")
        adffmpeg.merge_videos_and_audios(output_file_name=output_file_name)
        
        logger.info(f"Successfully completed for {output_file_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process {meeting_url}: {e}", exc_info=True)
        raise