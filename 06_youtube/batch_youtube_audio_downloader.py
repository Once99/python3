import os
import sys
import time
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

RETRY_LIMIT = 3

def show_progress(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        eta = d.get('eta', 0)
        print(f"⬇️ {percent} | 速度: {speed} | 剩餘時間: {eta}s", end='\r')
    elif d['status'] == 'finished':
        print(f"\n✅ 完成：{d['filename']}")

def download_audio_with_retry(url, output_dir):
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    },
                    {
                        'key': 'FFmpegMetadata',
                    },
                ],
                'quiet': False,
                'noplaylist': False,
                'progress_hooks': [show_progress],
                'no_warnings': True
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
        except DownloadError as e:
            print(f"\n❌ 第 {attempt} 次下載失敗：{e}")
            time.sleep(2)
    print(f"🚫 無法下載：{url}")
    return False

def download_audios(url_list, output_dir="downloads"):
    os.makedirs(output_dir, exist_ok=True)
    for url in url_list:
        print(f"\n🎵 處理：{url}")
        download_audio_with_retry(url, output_dir)

def load_urls_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("✅ 用法：")
        print("  python batch_youtube_audio_downloader.py https://www.youtube.com/watch?v=xxx")
        print("  python batch_youtube_audio_downloader.py urls.txt")
        sys.exit(1)

    arg = sys.argv[1]
    if arg.endswith(".txt") and os.path.exists(arg):
        urls = load_urls_from_file(arg)
    else:
        urls = [arg]

    download_audios(urls)
