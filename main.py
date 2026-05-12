from src.adobe2mp4 import download_and_export
import csv
import logging
import time
from pathlib import Path
from src.logger_config import get_main_logger, get_downloader_logger, get_ffmpeg_logger

# Setup all loggers
main_logger = get_main_logger()
downloader_logger = get_downloader_logger()
ffmpeg_logger = get_ffmpeg_logger()

# Assign loggers to the classes (optional, for more control)
import src.downloader
import src.ffmpeg

src.downloader.AdobeDownloader.logger = downloader_logger
src.ffmpeg.AdobeFFmpeg.logger = ffmpeg_logger

main_logger.info("=" * 60)
main_logger.info("Application started")
main_logger.info("=" * 60)

# Read and iterate through CSV file
csv_file = 'input.csv'
main_logger.info(f"Reading CSV file: {csv_file}")

try:
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row
        
        total_rows = sum(1 for _ in open(csv_file)) - 1  # Subtract header
        main_logger.info(f"Total items to process: {total_rows}")
        
        # Reset file pointer
        file.seek(0)
        next(csv_reader)  # Skip header again
        
        for idx, row in enumerate(csv_reader, 1):
            meeting_url = row[0].strip()
            output_file_name = row[1].strip()
            
            main_logger.info(f"\n{'='*60}")
            main_logger.info(f"Processing item {idx}/{total_rows}")
            main_logger.info(f"URL: {meeting_url}")
            main_logger.info(f"Output: {output_file_name}")
            main_logger.info(f"{'='*60}")
            
            # Add delay between downloads to avoid rate limiting
            if idx > 1:
                main_logger.info("Waiting 5 seconds before next download...")
                time.sleep(5)
            
            try:
                download_and_export(meeting_url, output_file_name)
                main_logger.info(f"✓ Successfully processed {output_file_name}")
            except Exception as e:
                main_logger.error(f"✗ Failed to process {output_file_name}: {e}", exc_info=True)
                main_logger.info(f"Continuing with next item...")
                continue
            
            main_logger.info(f"Completed {idx}/{total_rows}")
        
        main_logger.info("\n" + "="*60)
        main_logger.info("All downloads completed")
        main_logger.info("="*60)
        
except FileNotFoundError:
    main_logger.error(f"CSV file not found: {csv_file}")
except Exception as e:
    main_logger.error(f"Unexpected error: {e}", exc_info=True)