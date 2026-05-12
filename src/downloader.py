from pathlib import Path
from .config import config
import requests
import zipfile
from .beautiful_logger import get_downloader_logger

class AdobeDownloader():
    
    def __init__(self):
        # Setup beautiful logger
        self.logger = get_downloader_logger()
        self.session = None
        self.zip_path = None
        self.logger.debug("AdobeDownloader instance created")
    
    def build_download_url(self, meeting_url: str) -> str:
        download_url = meeting_url.rstrip('/') + f"/output/file.zip?download=zip"
        self.logger.debug(f"Built download URL")
        return download_url
    
    def _get_session(self):
        """Create a new session with fresh headers"""
        if self.session is None:
            self.logger.debug("Creating new requests session")
            self.session = requests.Session()
            # Set default headers for the session
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': config['Cookie'],
                'Accept': 'application/zip,application/octet-stream,*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            })
            self.logger.debug("Session headers configured")
        return self.session
    
    def close(self):
        if self.session:
            self.logger.debug("Closing session")
            self.session.close()
            self.session = None
    
    def download_meeting_zip(self, meeting_link: str,
                             temp_dir=config.get("TempDir","adobe_connect_temp"),
                             temp_zip_name=None):
        
        self.logger.download(f"Starting download from meeting URL")
        self.logger.url(meeting_link)
        
        # Generate unique filename for each download
        if temp_zip_name is None:
            import hashlib
            url_hash = hashlib.md5(meeting_link.encode()).hexdigest()[:8]
            temp_zip_name = f"meeting_{url_hash}.zip"
            self.logger.debug(f"Generated unique zip name: {temp_zip_name}")
        
        temp_dir = Path(temp_dir)
        temp_dir.mkdir(exist_ok=True)
        self.logger.debug(f"Temp directory: {temp_dir}")
        
        self.zip_path = temp_dir / temp_zip_name
        
        # Remove existing file if present
        if self.zip_path.exists():
            self.logger.warning(f"Removing existing file: {self.zip_path.name}")
            self.zip_path.unlink()
        
        zip_url = self.build_download_url(meeting_link)
        
        # Get fresh session
        session = self._get_session()
        
        try:
            self.logger.status("Connecting to server...", "info")
            response = session.get(zip_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check if we got a valid response
            content_type = response.headers.get('content-type', '')
            self.logger.debug(f"Response content-type: {content_type}")
            
            if 'html' in content_type:
                error_msg = "Server returned HTML instead of ZIP file. Authentication may have expired."
                self.logger.error(error_msg)
                raise Exception(error_msg)
            
            total_size = int(response.headers.get('content-length', 0))
            if total_size > 0:
                self.logger.info(f"File size: {total_size/1024/1024:.2f} MB")
            else:
                self.logger.warning("File size unknown")
            
            # Create progress bar
            from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TextColumn, TimeRemainingColumn
            from rich.console import Console
            
            with Progress(
                TextColumn("[bold blue]Downloading[/bold blue]"),
                BarColumn(bar_width=40),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=Console(),
                transient=False
            ) as progress:
                task = progress.add_task("", total=total_size if total_size > 0 else None)
                
                with open(self.zip_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress.update(task, advance=len(chunk))
            
            # Verify the downloaded file
            file_size = self.zip_path.stat().st_size
            self.logger.debug(f"Downloaded {file_size} bytes")
            
            if file_size == 0:
                self.logger.error("Downloaded file is empty")
                raise Exception("Downloaded file is empty")
            
            # Verify ZIP header
            with open(self.zip_path, 'rb') as f:
                header = f.read(4)
                if header != b'PK\x03\x04':
                    self.logger.error(f"Invalid ZIP header: {header}")
                    raise Exception("Downloaded file is not a valid ZIP file")
            
            self.logger.success(f"Downloaded valid ZIP file: {self.zip_path.name}")
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Request timeout: {e}")
            if self.zip_path.exists():
                self.zip_path.unlink()
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            if self.zip_path.exists():
                self.zip_path.unlink()
            raise
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            if self.zip_path.exists():
                self.zip_path.unlink()
            raise
    
    def extract_zip(self, temp_dir=config.get("TempDir","adobe_connect_temp")) -> str:
        self.logger.process("Starting ZIP extraction")
        
        if not self.zip_path or not self.zip_path.exists():
            error_msg = f"Zip file not found: {self.zip_path}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        temp_dir = Path(temp_dir)
        # Create unique extraction directory
        import time
        unique_id = int(time.time() * 1000)
        extract_dir = temp_dir / f"extracted_{unique_id}"
        self.logger.debug(f"Extraction directory: {extract_dir}")
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                self.logger.info(f"ZIP contains {len(file_list)} files")
                zip_ref.extractall(extract_dir)
            
            self.logger.success(f"Files extracted to {extract_dir.name}")
            return str(extract_dir)
            
        except zipfile.BadZipFile as e:
            file_size = self.zip_path.stat().st_size
            self.logger.error(f"BadZipFile error. File size: {file_size} bytes")
            
            # Read first few bytes to see what it is
            with open(self.zip_path, 'rb') as f:
                preview = f.read(200)
                self.logger.debug(f"File preview: {preview[:100]}")
            
            self.logger.error(f"Failed to extract ZIP: {e}")
            raise Exception(f"Failed to extract ZIP: {e}")
        
        except Exception as e:
            self.logger.error(f"Unexpected error during extraction: {e}")
            raise
    
    def download_and_extract(self, meeting_url: str) -> str:
        self.logger.section("Download & Extract", "📥")
        try:
            self.download_meeting_zip(meeting_url)
            self.logger.status("Extracting files...", "info")
            result = self.extract_zip()
            self.logger.success("Download and extraction completed")
            return result
        except Exception as e:
            self.logger.error(f"Download and extract failed: {e}")
            raise
        finally:
            self.close()