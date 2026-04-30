# Adobe Connect Meeting Downloader

## What It Does

Downloads Adobe Connect meeting recordings and converts them into a single MP4 video file.

## The Problem It Solves

Adobe Connect stores recordings as fragmented files - audio and video are separated, and long meetings are split into multiple chunks. There's no built-in download button.

## How It Works

1. **Downloads** the complete recording package from any Adobe Connect URL
2. **Extracts** all audio, video, and screen-share fragments
3. **Reassembles** everything into one synchronized MP4 file

## Key Features

- **No screen recording** – Downloads original video directly
- **One-click operation** – Just paste the URL and go


## Quick Start
### 1. create `config.json` file manually(only for the first time)
linux terminal:
```
cp config.json.example config.json
```
windows cmd:
```
copy config.json.example config.json
```
windows powershell:
```
Copy-Item config.json.example config.json
```
### 2. setup venv(recommended)
**first create the virtual environment**
```shell
python -m venv venv
```
**then activate it**
linux:
```bash
source venv/bin/activate
```
windows cmd:
```cmd
.\venv\Scripts\acivate.bat
```

### 3. install requirements
```bash
pip install -r requirements.txt
```

### 4. configuring 
open the meeting link you want to export and then do these instructions :
 - press `F12` (or inspect the page)
 - go to the `network` tab
 - refresh the page
 - in the network tab go to the `Doc` sub tab
 - find the doc that its `request url` is the same with your `meeting link` and click on it
 - in the new tab appears , scroll and find the key `Cookie` then copy its value
 - go to the `config.json` in the project and paste the value you just copied for `Cookie` key in the json file
 - now you are ready to run
   
### 5. Run
```
python main.py
```
it will want your `meeting url` and  `output file name`(default is final_video.mp4) and after a while, your mp4 file is ready .
