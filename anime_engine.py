import requests

class AnimeMovieEngine:
    def __init__(self):
        # الرابط الأساسي للسيرفر العالمي المفتوح للمطورين
        self.base_url = "https://consumet.org"

    def search_anime(self, title):
        """البحث عن أي أنمي وجلب معلوماته وصورته والـ ID الخاص به"""
        try:
            url = f"{self.base_url}/anime/gogoanime/{title}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json().get('results', [])
            return []
        except Exception as e:
            print(f"خطأ في البحث عن الأنمي: {e}")
            return []

    def get_anime_episodes(self, anime_id):
        """جلب قائمة جميع الحلقات المتوفرة للأنمي المختار"""
        try:
            url = f"{self.base_url}/anime/gogoanime/info/{anime_id}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json().get('episodes', [])
            return []
        except Exception as e:
            print(f"خطأ في جلب الحلقات: {e}")
            return []

    def get_anime_stream_link(self, episode_id):
        """الجزء الأهم: جلب رابط تشغيل الفيديو المباشر (M3U8/MP4) للحلقة"""
        try:
            url = f"{self.base_url}/anime/gogoanime/watch/{episode_id}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                sources = response.json().get('sources', [])
                if sources:
                    # جلب الرابط الأول وعادة ما يكون الأعلى جودة تلقائياً
                    return sources[0].get('url')
            return None
        except Exception as e:
            print(f"خطأ في جلب رابط تشغيل الأنمي: {e}")
            return None

    def search_movie_or_series(self, title):
        """البحث عن الأفلام والمسلسلات العالمية المترجمة"""
        try:
            url = f"{self.base_url}/movies/flixhq/{title}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json().get('results', [])
            return []
        except Exception as e:
            print(f"خطأ في البحث عن الأفلام: {e}")
            return []

    def get_movie_stream_link(self, media_id, episode_id):
        """جلب رابط الفيديو المباشر للفيلم أو حلقة المسلسل ومعه ملف الترجمة"""
        try:
            url = f"{self.base_url}/movies/flixhq/watch"
            params = {"episodeId": episode_id, "mediaId": media_id}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                video_url = data.get('sources', [{}])[0].get('url')
                subtitles = data.get('subtitles', []) # قائمة ملفات الترجمة الجاهزة
                return video_url, subtitles
            return None, None
        except Exception as e:
            print(f"خطأ في جلب رابط تشغيل الفيلم: {e}")
            return None, None
