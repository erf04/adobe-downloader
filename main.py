from src.adobe2mp4 import download_and_export


meeting_url = input("Enter meeting url: ")
output_file_name = input("Enter output file name [final_video.mp4]: ") or "final_video.mp4"

download_and_export(meeting_url,output_file_name)