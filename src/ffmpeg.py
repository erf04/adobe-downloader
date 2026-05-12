from .utils import sorted_nicely
from .config import config
import ffmpeg
from pathlib import Path
import logging
import shutil

class AdobeFFmpeg():
    
    def __init__(self):
        # Setup logger for this instance
        self.logger = logging.getLogger(f"{__name__}.AdobeFFmpeg")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        self.video_files = []
        self.audio_files = []
        self.temp_video_path = None
        self.temp_audio_path = None
        self.logger.debug("AdobeFFmpeg instance created")
    
    def find_and_sort_segments(self, extract_dir: str):
        self.logger.info(f"Finding segments in: {extract_dir}")
        
        extract_dir_path = Path(extract_dir)
        video_files = sorted_nicely(extract_dir_path.glob("screenshare_*_*.flv"))
        audio_files = sorted_nicely(extract_dir_path.glob("cameraVoip_*_*.flv"))
        
        self.logger.debug(f"Found {len(video_files)} video files before filtering")
        self.logger.debug(f"Found {len(audio_files)} audio files before filtering")
        
        # Remove any potential non-segment files
        self.video_files = [f for f in video_files if 'screenshare' in f.name]
        self.audio_files = [f for f in audio_files if 'cameraVoip' in f.name]
        
        self.logger.info(f"Found video segments: {[f.name for f in self.video_files]}")
        self.logger.info(f"Found audio segments: {[f.name for f in self.audio_files]}")
        
        if not self.video_files or not self.audio_files:
            self.logger.error("Required video or audio segments not found")
            self.clean_up()
            raise Exception("Could not find the required screenshare or cameraVoip .flv files.")
        
        self.logger.info("Segments found and sorted successfully")
        return self
    
    def concat_segments(self, temp_dir=config.get("TempDir", "adobe_connect_temp")):
        self.logger.info("Starting segment concatenation")
        
        temp_dir_path = Path(temp_dir)
        video_list_path = temp_dir_path / "video_list.txt"
        audio_list_path = temp_dir_path / "audio_list.txt"
        
        self.logger.debug(f"Video list path: {video_list_path}")
        self.logger.debug(f"Audio list path: {audio_list_path}")
        
        # Write video list
        with open(video_list_path, 'w') as f:
            for video_path in self.video_files:
                f.write(f"file '{video_path.absolute()}'\n")
        self.logger.debug(f"Written {len(self.video_files)} video files to list")
        
        # Write audio list
        with open(audio_list_path, 'w') as f:
            for audio_path in self.audio_files:
                f.write(f"file '{audio_path.absolute()}'\n")
        self.logger.debug(f"Written {len(self.audio_files)} audio files to list")
        
        # Temporary files
        self.temp_video_path = temp_dir_path / "temp_video.flv"
        self.temp_audio_path = temp_dir_path / "temp_audio.flv"
        
        self.logger.info(f"Temp video path: {self.temp_video_path}")
        self.logger.info(f"Temp audio path: {self.temp_audio_path}")
        
        try:
            # Concat all video segments
            self.logger.info("Merging video files...")
            ffmpeg.input(str(video_list_path), format='concat', safe=0).output(
                str(self.temp_video_path), c='copy'
            ).run(quiet=True, overwrite_output=True)
            self.logger.info(f"Video concatenation complete: {self.temp_video_path.stat().st_size} bytes")
            
            # Concat all audio segments
            self.logger.info("Merging audio files...")
            ffmpeg.input(str(audio_list_path), format='concat', safe=0).output(
                str(self.temp_audio_path), c='copy'
            ).run(quiet=True, overwrite_output=True)
            self.logger.info(f"Audio concatenation complete: {self.temp_audio_path.stat().st_size} bytes")
            
        except ffmpeg.Error as e:
            self.logger.error(f"FFmpeg error during concatenation: {e.stderr.decode() if e.stderr else str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during concatenation: {e}", exc_info=True)
            raise
    
    def merge_videos_and_audios(self, output_file_name="final_video.mp4"):
        self.logger.info(f"Merging video and audio into final MP4: {output_file_name}")
        
        output_path = Path(output_file_name)
        
        try:
            video_input = ffmpeg.input(str(self.temp_video_path))
            audio_input = ffmpeg.input(str(self.temp_audio_path))
            
            self.logger.debug("Running ffmpeg merge command")
            ffmpeg.output(
                video_input['v'], audio_input['a'],
                str(output_path),
                vcodec='libx264', acodec='aac'
            ).run(quiet=True, overwrite_output=True)
            
            file_size = output_path.stat().st_size
            self.logger.info(f"✅ Success! Meeting saved as: {output_path.absolute()} ({file_size/1024/1024:.2f} MB)")
            
        except ffmpeg.Error as e:
            self.logger.error(f"FFmpeg error during merging: {e.stderr.decode() if e.stderr else str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during merging: {e}", exc_info=True)
            raise
        finally:
            self.logger.info("Cleaning up temporary files...")
            self.clean_up()
    
    def clean_up(self, temp_dir=config.get("TempDir", "adobe_connect_temp")):
        self.logger.info(f"Cleaning up temporary directory: {temp_dir}")
        try:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
                self.logger.debug("Temporary directory removed successfully")
            else:
                self.logger.debug("Temporary directory does not exist, nothing to clean")
        except Exception as e:
            self.logger.warning(f"Failed to clean up temporary files: {e}")