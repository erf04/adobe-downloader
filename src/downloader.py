from pathlib import Path
from .config import config
import requests
import zipfile


class AdobeDownloader():

    def build_download_url(self,meeting_url:str) -> str:
        return meeting_url.rstrip('/') + f"/output/file.zip?download=zip"


    def download_meeting_zip(self,meeting_link:str,
                             temp_dir=config.get("TempDir","adobe_connect_temp"),
                             temp_zip_name="meeting.zip"):
        # Create a temporary directory for this meeting
        temp_dir = Path(temp_dir)
        temp_dir.mkdir(exist_ok=True)
        
        self.zip_path = temp_dir / temp_zip_name

        # Download the file
        zip_url = self.build_download_url(meeting_link)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': config['Cookie']  
        }
        response = requests.get(zip_url,headers=headers, stream=True)
        response.raise_for_status()  # Check if download was successful
        with open(self.zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")


    def extract_zip(self,temp_dir=config.get("TempDir","adobe_connect_temp")) -> str:
        extract_dir = temp_dir / "extracted"
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"Files extracted to {extract_dir}")
        return extract_dir
    

    def download_and_extract(self,meeting_url:str) -> str:
        self.download_meeting_zip(meeting_url)
        return self.extract_zip()

