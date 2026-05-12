from .utils import sorted_nicely
from .config import config
import ffmpeg
from pathlib import Path
import shutil
from .beautiful_logger import get_ffmpeg_logger

class AdobeFFmpeg():
    
    def __init__(self):
        # Setup beautiful logger
        self.logger = get_ffmpeg_logger()
        self.video_files = []
        self.audio_files = []
        self.temp_video_path = None
        self.temp_audio_path = None
        self.logger.debug("AdobeFFmpeg instance created")
    
    def find_and_sort_segments(self, extract_dir: str):
        self.logger.section("Finding Segments", "🔍")
        self.logger.info(f"Scanning directory: {extract_dir}")
        
        extract_dir_path = Path(extract_dir)
        video_files = sorted_nicely(extract_dir_path.glob("screenshare_*_*.flv"))
        audio_files = sorted_nicely(extract_dir_path.glob("cameraVoip_*_*.flv"))
        
        self.logger.debug(f"Found {len(video_files)} raw video files")
        self.logger.debug(f"Found {len(audio_files)} raw audio files")
        
        # Remove any potential non-segment files
        self.video_files = [f for f in video_files if 'screenshare' in f.name]
        self.audio_files = [f for f in audio_files if 'cameraVoip' in f.name]
        
        self.logger.info(f"Found [green]{len(self.video_files)}[/green] video segments")
        self.logger.info(f"Found [green]{len(self.audio_files)}[/green] audio segments")
        
        if self.video_files:
            self.logger.debug(f"Video segments: {', '.join(f.name for f in self.video_files[:3])}")
            if len(self.video_files) > 3:
                self.logger.debug(f"... and {len(self.video_files) - 3} more")
        
        if not self.video_files or not self.audio_files:
            self.logger.error("Required video or audio segments not found")
            self.clean_up()
            raise Exception("Could not find the required screenshare or cameraVoip .flv files.")
        
        self.logger.success("Segments found and sorted")
        return self
    
    def concat_segments(self, temp_dir=config.get("TempDir", "adobe_connect_temp")):
        self.logger.section("Concatenating Segments", "🔗")
        
        temp_dir_path = Path(temp_dir)
        video_list_path = temp_dir_path / "video_list.txt"
        audio_list_path = temp_dir_path / "audio_list.txt"
        
        # Write video list
        with open(video_list_path, 'w') as f:
            for video_path in self.video_files:
                f.write(f"file '{video_path.absolute()}'\n")
        self.logger.debug(f"Video list: {len(self.video_files)} files")
        
        # Write audio list
        with open(audio_list_path, 'w') as f:
            for audio_path in self.audio_files:
                f.write(f"file '{audio_path.absolute()}'\n")
        self.logger.debug(f"Audio list: {len(self.audio_files)} files")
        
        # Temporary files
        self.temp_video_path = temp_dir_path / "temp_video.flv"
        self.temp_audio_path = temp_dir_path / "temp_audio.flv"
        
        try:
            # Concat all video segments
            self.logger.status("Merging video files...", "info")
            ffmpeg.input(str(video_list_path), format='concat', safe=0).output(
                str(self.temp_video_path), c='copy'
            ).run(quiet=True, overwrite_output=True)
            
            video_size = self.temp_video_path.stat().st_size
            self.logger.success(f"Video merged: {video_size/1024/1024:.2f} MB")
            
            # Concat all audio segments
            self.logger.status("Merging audio files...", "info")
            ffmpeg.input(str(audio_list_path), format='concat', safe=0).output(
                str(self.temp_audio_path), c='copy'
            ).run(quiet=True, overwrite_output=True)
            
            audio_size = self.temp_audio_path.stat().st_size
            self.logger.success(f"Audio merged: {audio_size/1024/1024:.2f} MB")
            
        except ffmpeg.Error as e:
            self.logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise
    
    def merge_videos_and_audios(self, output_file_name="final_video.mp4"):
        self.logger.section("Merging Final Video", "🎬")
        
        output_path = Path(output_file_name)
        self.logger.info(f"Output file: [file]{output_path.name}[/file]")
        
        try:
            video_input = ffmpeg.input(str(self.temp_video_path))
            audio_input = ffmpeg.input(str(self.temp_audio_path))
            
            self.logger.status("Running FFmpeg merge...", "info")
            ffmpeg.output(
                video_input['v'], audio_input['a'],
                str(output_path),
                vcodec='libx264', acodec='aac'
            ).run(quiet=True, overwrite_output=True)
            
            file_size = output_path.stat().st_size
            self.logger.success(f"Video created successfully!")
            self.logger.file(f"Saved as: {output_path.absolute()}")
            self.logger.info(f"Final size: [green]{file_size/1024/1024:.2f} MB[/green]")
            
        except ffmpeg.Error as e:
            self.logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise
        finally:
            self.logger.process("Cleaning up temporary files...")
            self.clean_up()
    
    def clean_up(self, temp_dir=config.get("TempDir", "adobe_connect_temp")):
        try:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
                self.logger.debug("Temporary files cleaned up")
            else:
                self.logger.debug("No temporary files to clean")
        except Exception as e:
            self.logger.warning(f"Failed to clean up: {e}")