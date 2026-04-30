from .utils import sorted_nicely
from .config import config
import ffmpeg
from pathlib import Path

class AdobeFFmpeg():
    def find_and_sort_segments(self,extract_dir:str):
        video_files = sorted_nicely(extract_dir.glob("screenshare_*_*.flv"))
        audio_files = sorted_nicely(extract_dir.glob("cameraVoip_*_*.flv"))

        # Remove any potential non-segment files (like 'mainstream.flv') if they got caught
        self.video_files = [f for f in video_files if 'screenshare' in f.name]
        self.audio_files = [f for f in audio_files if 'cameraVoip' in f.name]

        print(f"Found video segments: {[f.name for f in video_files]}")
        print(f"Found audio segments: {[f.name for f in audio_files]}")

        if not video_files or not audio_files:
            raise Exception("Could not find the required screenshare or cameraVoip .flv files.")
        return self
        

    def concat_segments(self,
                        temp_dir=config.get("TempDir","adobe_connect_temp"),
                        ):
        video_list_path = Path(temp_dir) / "video_list.txt"
        audio_list_path = Path(temp_dir) / "audio_list.txt"

        with open(video_list_path, 'w') as f:
            for video_path in self.video_files:
                # Use absolute path to avoid issues with the -safe 0 parameter
                f.write(f"file '{video_path.absolute()}'\n")

        with open(audio_list_path, 'w') as f:
            for audio_path in self.audio_files:
                f.write(f"file '{audio_path.absolute()}'\n")

        # 5. Use ffmpeg-python to run the concat demuxer for video and audio separately
        # This mimics the command: ffmpeg -f concat -safe 0 -i list.txt -c copy output.flv
        temp_video_path = Path(temp_dir) / "temp_video.flv"
        temp_audio_path = Path(temp_dir) / "temp_audio.flv"


        self.temp_video_path = temp_video_path
        self.temp_audio_path = temp_audio_path

        try:
            # Concat all video segments
            print("  - Merging video files...")
            ffmpeg.input(str(video_list_path), format='concat', safe=0).output(
                str(temp_video_path), c='copy'
            ).run(quiet=True, overwrite_output=True)
            
            # Concat all audio segments
            print("  - Merging audio files...")
            ffmpeg.input(str(audio_list_path), format='concat', safe=0).output(
                str(temp_audio_path), c='copy'
            ).run(quiet=True, overwrite_output=True)
            
        except ffmpeg.Error as e:
            print("An error occurred during concatenation:", e.stderr)
            return
        

    def merge_videos_and_audios(self,output_file_name="final_video.mp4"):
        output_path = Path(output_file_name)
    
        # This mimics: ffmpeg -i temp_video.flv -i temp_audio.flv -c:v libx264 -c:a aac -map 0:v:0 -map 1:a:0 output.mp4
        try:
            video_input = ffmpeg.input(str(self.temp_video_path))
            audio_input = ffmpeg.input(str(self.temp_audio_path))
            
            ffmpeg.output(
                video_input['v'], audio_input['a'],
                str(output_path),
                vcodec='libx264', acodec='aac'
            ).run(quiet=True, overwrite_output=True)
            
            print(f"\n✅ Success! Your meeting has been saved as: {output_path.absolute()}")
        except ffmpeg.Error as e:
            print("An error occurred during final merging:", e.stderr)
            return
        finally:
            # 7. Optional: Clean up temporary files
            print("Step 6: Cleaning up temporary files...")
            self.clean_up()



    def clean_up(
            self,
            temp_dir = config.get("TempDir","adobe_connect_temp")
    ):
        import shutil
        shutil.rmtree(temp_dir)
