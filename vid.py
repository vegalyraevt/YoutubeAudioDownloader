import tkinter as tk
from tkinter import filedialog, Menu
from pytube import YouTube
from moviepy.editor import AudioFileClip
import os
import json
import webbrowser
from datetime import datetime

# Load or initialize configuration
config_file = 'config.json'
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
else:
    config = {'output_path': os.path.join(os.getcwd(), 'rips')}

def save_config():
    with open(config_file, 'w') as f:
        json.dump(config, f)

def log_error(video_url, total_videos, error_message):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"error_log_{timestamp}.txt"
    with open(log_filename, "a") as log_file:
        log_file.write(f"Error converting video {video_url} - Video {total_videos}\n")
        log_file.write(f"Error message: {error_message}\n\n")


def download_audio(url, output_path):
    # Check if the output folder exists, if not, create it
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    try:
        yt = YouTube(url)
        audio_stream = yt.streams.get_audio_only()
        audio_file_path = audio_stream.download(output_path)
        
        # Load the downloaded audio file
        audio_clip = AudioFileClip(audio_file_path)
        # Set the filename for the mp3 file
        audio_file_path_mp3 = audio_file_path.replace('.mp4', '.mp3')
        # Write the audio file as an mp3
        audio_clip.write_audiofile(audio_file_path_mp3)
        
        # Close the audio clip to free resources
        audio_clip.close()
        
        # Remove the original audio file
        os.remove(audio_file_path)
        
        return audio_file_path_mp3
    except Exception as e:
        return str(e)

def on_download():
    video_urls = url_entry.get().split(", ")
    total_videos = len(video_urls)
    for index, video_url in enumerate(video_urls, start=1):
        try:
            video_title = download_audio(video_url, config['output_path'])
            if video_title:
                display_message(f"Converted '{video_title}' successfully - Video {index}/{total_videos}")
            else:
                display_message(f"Failed to convert video - Video {index}/{total_videos}")
                log_error(video_url, total_videos, "Download failed")
        except Exception as e:
            display_message(f"Failed to convert video - Video {index}/{total_videos}")
            log_error(video_url, total_videos, str(e))
        finally:
            url_entry.delete(0, tk.END)  # Clear the URL entry field after processing

def open_download_location():
    os.startfile(config['output_path'])

def change_output_path():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        config['output_path'] = folder_selected
        save_config()
        message_box.insert(tk.END, f"Output path changed to {folder_selected}\n")

# Functions for opening links
def open_discord():
    webbrowser.open('https://discord.gg/GpA483cuZZ')

def open_twitter():
    webbrowser.open('https://x.com/VegaLyraeVT')

def open_kofi():
    webbrowser.open('https://ko-fi.com/vegalyrae')

def open_email():
    webbrowser.open('https://mail.google.com/mail/u/0/?fs=1&to=VegaLyraeVtuber@gmail.com&su=ERROR+IN+VMB&body=Please%20Put%20message%20description%20here%20and%20attach%20error%20log%20if%20seeking%20help&tf=cm')

def open_license_link():
    webbrowser.open('https://www.gnu.org/licenses/gpl-3.0.en.html')

def about():
    display_message("*************************")
    display_message("*** YT Downloader V1.0 ***")
    display_message("*** Made By Vega Lyrae ***")
    display_message("*** Thank you for purchasing my program. ***")
    display_message("This program is free to use under the GNU V3. It can be used for any purpose, redistributed in a changed state, or used in part or as a whole in another program. Any program using any of this program's code MUST be distributed under the GLP as well per the GPL. Click 'GPL V3' under the about dropdown to learn more.")
    display_message("! Original program is property of Constellation Virtual Media under the GNU V3 as of 2024 !")
    display_message("*************************")

def help():
    display_message("*************************")
    display_message("*** I'm sorry to hear you're having a issue! ***")
    display_message("This program can download any youtube video as a mp3, it does so as the higest quality possible for the video at teh time of running. Just simply paste the full url of the video into the url box and hit the download button to start. You can even download more than one at a time! Simply put a comma then a space between the urls like this: 'VidURL1, VidURL2'. For more help see the about section or contact Vega through the contact drop down.")
    display_message("*************************")

# Function to display messages in the message box
def display_message(message):
    message_box.insert(tk.END, message + "\n")
    message_box.see(tk.END)  # Auto-scroll to the bottom

# Set up the GUI
root = tk.Tk()
root.title("YouTube Audio Downloader")
root.geometry('450x250')  # Set the initial size of the window
root.minsize(450, 250)  # Set the minimum size of the window

# Configure the grid weight for the main window to allow dynamic resizing
root.grid_rowconfigure(0, weight=1)  # Message box row
root.grid_rowconfigure(1, weight=0)  # Label row
root.grid_rowconfigure(2, weight=0)  # Entry row
root.grid_rowconfigure(3, weight=0)  # Button frame row
root.grid_columnconfigure(0, weight=1)  # Single column configuration

# Menu bar
menu_bar = Menu(root)

# Settings menu
settings_menu = Menu(menu_bar, tearoff=0)
settings_menu.add_command(label="Change Download Location", command=change_output_path)
menu_bar.add_cascade(label="Settings", menu=settings_menu)

# Contact menu
contact_menu = Menu(menu_bar, tearoff=0)
contact_menu.add_command(label="Discord", command=open_discord)
contact_menu.add_command(label="Twitter/X", command=open_twitter)
contact_menu.add_command(label="ko-fi", command=open_kofi)
contact_menu.add_command(label="Email", command=open_email)
menu_bar.add_cascade(label="Contact", menu=contact_menu)

# Help menu
help_menu = Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Help", command=help)
menu_bar.add_cascade(label="Help", menu=help_menu)

# About menu
about_menu = Menu(menu_bar, tearoff=0)
about_menu.add_command(label="About Libraries", command=lambda: display_message("This program primarialy uses the tkinter, pytube, and moviepy librays among other more standard apis."))
about_menu.add_command(label="About License", command=lambda: display_message("This program is free to use under the GNU V3. It can be used for any purpose, redistributed in a changed state, or used in part or as a whole in another program. Any program using any of this program's code MUST be distributed under the GLP as well per the GPL. Click 'GPL V3' under the about dropdown to learn more."))
about_menu.add_command(label="About Program", command=about)
about_menu.add_command(label="GNU v3 License", command=open_license_link)
menu_bar.add_cascade(label="About", menu=about_menu)

root.config(menu=menu_bar)

# Message box at the top with dynamic resizing
message_box = tk.Text(root, wrap=tk.WORD)
message_box.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
message_box.insert(tk.END, "Program initialized, status messages will display here.\n")

# Entry for YouTube URL with dynamic resizing
url_label = tk.Label(root, text="Enter YouTube URL:")
url_label.grid(row=1, column=0, sticky='nw', padx=5, pady=5)
url_entry = tk.Entry(root)
url_entry.grid(row=2, column=0, sticky='ew', padx=5, pady=5)

# Button frame with centered buttons and dynamic resizing
button_frame = tk.Frame(root)
button_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
button_frame.grid_columnconfigure(0, weight=1)
button_frame.grid_columnconfigure(1, weight=0)
button_frame.grid_columnconfigure(2, weight=0)
button_frame.grid_columnconfigure(3, weight=1)

# Place buttons within the button frame using grid
download_button = tk.Button(button_frame, text="Download", command=on_download)
download_button.grid(row=0, column=1, sticky='ew', padx=5)

open_folder_button = tk.Button(button_frame, text="Open Download Location", command=open_download_location)
open_folder_button.grid(row=0, column=2, sticky='ew', padx=5)

root.mainloop()