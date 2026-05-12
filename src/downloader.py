from pathlib import Path
from .config import config
import requests
import zipfile
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn

class AdobeDownloader():

    def __init__(self):
        # Create a completely fresh session for each instance
        self.session = None
        self.zip_path = None

    def build_download_url(self,meeting_url:str) -> str:
        return meeting_url.rstrip('/') + f"/output/file.zip?download=zip"

    
    def _get_session(self):
        """Create a new session with fresh headers"""
        if self.session is None:
            self.session = requests.Session()
            # Set default headers for the session
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': config['Cookie'],
                'Accept': 'application/zip,application/octet-stream,*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            })
        return self.session
    
    def close(self):
        if self.session:
            self.session.close()
            self.session = None
    
    def download_meeting_zip(self, meeting_link: str,
                             temp_dir=config.get("TempDir","adobe_connect_temp"),
                             temp_zip_name=None):
        
        # Generate unique filename for each download
        if temp_zip_name is None:
            import hashlib
            url_hash = hashlib.md5(meeting_link.encode()).hexdigest()[:8]
            temp_zip_name = f"meeting_{url_hash}.zip"
        
        temp_dir = Path(temp_dir)
        temp_dir.mkdir(exist_ok=True)
        
        self.zip_path = temp_dir / temp_zip_name
        
        # Remove existing file if present
        if self.zip_path.exists():
            self.zip_path.unlink()
        
        zip_url = self.build_download_url(meeting_link)
        print("zip_rul" , zip_url)
        # Get fresh session
        session = self._get_session()
        
        try:
            response = session.get(zip_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check if we got a valid response
            content_type = response.headers.get('content-type', '')
            if 'html' in content_type:
                raise Exception("Server returned HTML instead of ZIP file. Authentication may have expired.")
            
            total_size = int(response.headers.get('content-length', 0))
            
            with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                DownloadColumn(),
                TransferSpeedColumn(),
            ) as progress:
                task = progress.add_task("Downloading...", total=total_size if total_size > 0 else None)
                
                with open(self.zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            if total_size > 0:
                                progress.update(task, advance=len(chunk))
                            else:
                                progress.update(task, advance=len(chunk))
            
            # Verify the downloaded file
            if self.zip_path.stat().st_size == 0:
                raise Exception("Downloaded file is empty")
            
            # Verify ZIP header
            with open(self.zip_path, 'rb') as f:
                if f.read(4) != b'PK\x03\x04':
                    raise Exception("Downloaded file is not a valid ZIP file")
            
            print(f"✓ Successfully downloaded valid ZIP file: {self.zip_path}")
            
        except Exception as e:
            print(f"Download failed: {e}")
            if self.zip_path.exists():
                self.zip_path.unlink()
            raise
    
    def extract_zip(self, temp_dir=config.get("TempDir","adobe_connect_temp")) -> str:
        if not self.zip_path or not self.zip_path.exists():
            raise Exception(f"Zip file not found: {self.zip_path}")
        
        temp_dir = Path(temp_dir)
        # Create unique extraction directory
        import time
        unique_id = int(time.time() * 1000)
        extract_dir = temp_dir / f"extracted_{unique_id}"
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"Files extracted to {extract_dir}")
            return extract_dir
        except zipfile.BadZipFile as e:
            # Print file info for debugging
            file_size = self.zip_path.stat().st_size
            print(f"BadZipFile error. File size: {file_size} bytes")
            
            # Read first few bytes to see what it is
            with open(self.zip_path, 'rb') as f:
                preview = f.read(500)
                print(f"File preview (first 500 bytes):\n{preview}")
            
            raise Exception(f"Failed to extract ZIP: {e}")
    
    def download_and_extract(self, meeting_url: str) -> str:
        try:
            self.download_meeting_zip(meeting_url)
            print("Extracting files...")
            return self.extract_zip()
        finally:
            self.close()  # Always clean up session

