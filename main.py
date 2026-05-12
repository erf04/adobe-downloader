from src.adobe2mp4 import download_and_export
import csv
import time
from pathlib import Path
from src.beautiful_logger import get_main_logger

# Initialize beautiful logger
logger = get_main_logger()

def main():
    """Main entry point for the application"""
    
    # Welcome banner
    logger.rule("🎬 Adobe Connect Meeting Downloader")
    logger.section("Application Started", "🚀")
    
    csv_file = 'input.csv'
    
    # Check if CSV file exists
    if not Path(csv_file).exists():
        logger.error(f"CSV file not found: {csv_file}")
        logger.info("Please create an input.csv file with columns: meeting_url, output_file_name")
        return
    
    # Read CSV file
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            
            # Check if file has content
            try:
                header = next(csv_reader)
                logger.debug(f"CSV header: {header}")
            except StopIteration:
                logger.error("CSV file is empty")
                return
            
            # Read all rows
            rows = list(csv_reader)
            
            if not rows:
                logger.warning("No data rows found in CSV file")
                return
            
            logger.success(f"Found [bold]{len(rows)}[/bold] meetings to process")
            
            # Display processing plan
            processing_table = []
            for idx, row in enumerate(rows, 1):
                output_file = row[1].strip() if len(row) > 1 else f"meeting_{idx}.mp4"
                processing_table.append([f"#{idx}", output_file])
            
            logger.print_table(
                "📋 Processing Queue",
                ["Item", "Output File"],
                processing_table
            )
            
            # Process each meeting
            results = []
            start_time = time.time()
            
            for idx, row in enumerate(rows, 1):
                try:
                    meeting_url = row[0].strip() if len(row) > 0 else ""
                    output_file_name = row[1].strip() if len(row) > 1 else f"meeting_{idx}.mp4"
                    
                    if not meeting_url:
                        logger.warning(f"Row {idx}: Empty URL, skipping")
                        results.append({
                            'file': output_file_name,
                            'success': False,
                            'time': 0,
                            'error': "Empty URL"
                        })
                        continue
                    
                    item_start = time.time()
                    
                    logger.section(f"Processing Item {idx}/{len(rows)}", "📦")
                    logger.info(f"Output: [file]{output_file_name}[/file]")
                    
                    # Add delay between downloads to avoid rate limiting
                    if idx > 1:
                        logger.status("Waiting 5 seconds before next download...", "info")
                        time.sleep(5)
                    
                    # Process the meeting
                    download_and_export(meeting_url, output_file_name)
                    
                    item_time = time.time() - item_start
                    logger.success(f"Completed in {item_time:.2f} seconds")
                    
                    results.append({
                        'file': output_file_name,
                        'success': True,
                        'time': item_time,
                        'error': None
                    })
                    
                except Exception as e:
                    item_time = time.time() - item_start if 'item_start' in locals() else 0
                    logger.error(f"Failed: {e}")
                    results.append({
                        'file': output_file_name if 'output_file_name' in locals() else f"item_{idx}",
                        'success': False,
                        'time': item_time,
                        'error': str(e)
                    })
                    continue
            
            # Summary
            total_time = time.time() - start_time
            success_count = sum(1 for r in results if r['success'])
            failed_count = len(results) - success_count
            
            logger.rule("📊 Download Summary")
            
            # Show results table
            result_rows = []
            for r in results:
                status = "✅ Success" if r['success'] else "❌ Failed"
                status_style = "green" if r['success'] else "red"
                result_rows.append([
                    r['file'],
                    f"[{status_style}]{status}[/{status_style}]",
                    f"{r['time']:.2f}s",
                    r['error'] if r['error'] else ""
                ])
            
            logger.print_table(
                "Processing Results",
                ["File", "Status", "Time", "Error"],
                result_rows
            )
            
            # Statistics
            logger.section("Statistics", "📈")
            logger.info(f"Total items: {len(results)}")
            logger.success(f"Successful: {success_count}")
            if failed_count > 0:
                logger.error(f"Failed: {failed_count}")
            logger.info(f"Total time: {total_time:.2f} seconds")
            logger.info(f"Average time: {total_time/len(results):.2f} seconds per item")
            
            # Final message
            if success_count == len(results):
                logger.success("\n✨ All downloads completed successfully! ✨")
            elif success_count > 0:
                logger.warning(f"\n⚠️ Completed with {failed_count} failures")
            else:
                logger.error("\n💀 All downloads failed")
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.critical("Application crashed", exc_info=True)
    
    logger.rule("🏁 Application Finished")

if __name__ == "__main__":
    main()