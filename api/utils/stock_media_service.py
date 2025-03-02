from fastapi import HTTPException
import requests, urllib.request, urllib.error, urllib.parse, json

from api.utils.settings import settings


class StockMediaService:
    
    def __init__(self, query: str, page: int, per_page: int):
        """Initializer function for the stock service

        Args:
            query (str): This is the thing to search for in the stock apis. Must not exceed 100 characters
            page (int): Page number. Defaults to one
            per_page (int): Number of media to be retrieved from the API
        """
        
        self.query = query
        self.page = page
        self.per_page = per_page
        
    
    def __build_request(self, url: str, headers={}):
        """Helper function to build the request url"""
        
        try:
            # response = requests.get(url, headers=headers, verify=False)
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise HTTPException(status_code=500, detail='Network error. Please connect to a stable network')
        
        except requests.exceptions.Timeout as e:
            raise HTTPException(status_code=500, detail='Connection timeout')
        
        except requests.exceptions.RequestException as e:
            print(response.status_code)

            # Raising a more informative error if the 403 persists
            if response.status_code == 403:
                raise HTTPException(status_code=403, detail=f'Access forbidden for {url}: Check API key or access restrictions')
            raise e
        
        except Exception as e:
            raise e   
    
    # def __build_request(self, url: str, headers={}):
    #     """Helper function to build the request url using urllib"""
        
    #     try:
    #         req = urllib.request.Request(url, headers=headers)
    #         with urllib.request.urlopen(req) as response:
    #             if response.status != 200:
    #                 raise HTTPException(status_code=response.status, detail=f"Request failed with status: {response.status}")
                
    #             data = response.read().decode('utf-8')
    #             return json.loads(data)

    #     except urllib.error.HTTPError as e:
    #         if e.code == 403:
    #             raise HTTPException(status_code=403, detail='Access forbidden: Check API key or access restrictions')
    #         elif e.code == 404:
    #             raise HTTPException(status_code=404, detail='Resource not found')
    #         else:
    #             raise HTTPException(status_code=e.code, detail=str(e))
    #     except urllib.error.URLError as e:
    #         raise HTTPException(status_code=500, detail='Network error: Unable to reach the server')
    #     except json.JSONDecodeError:
    #         raise HTTPException(status_code=500, detail='Failed to decode JSON response')
  
             

    def __unsplash(self):
        """This function retrieves images from Unaplash API

        Args:
            page (int): Page number. Defaults to one
            per_page (int): Number of media to be retrieved from the API
        """
        
        api_key = settings.UNSPLASH_ACCESS_KEY
        encoded_query = urllib.parse.quote(self.query)
        url = f"https://api.unsplash.com/search/photos?query={encoded_query}&client_id={api_key}&page={self.page}&per_page={self.per_page}"
        
        data = self.__build_request(url)
        image_data: list = data['results']
        
        final_result = [{
            'preview': image['urls']['thumb'],
            'normal': image['urls']['raw']
        } for image in image_data] if image_data else []
        
        return final_result

    
    def __pixabay(self, media_type: str):
        """This function retrieves images and videos from Pixabay API

        Args:
            page (int): Page number
            per_page (int): Number of media to be retrieved from the API
            media_type (str): Should be one of `image` or `video`
        """
        
        api_key = settings.PIXABAY_API_KEY
        final_result = []
        
        # headers = {
        #     # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        #     # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0'
        #     # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        # }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }

        if media_type == 'image':
            url = f"https://pixabay.com/api/?key={api_key}&q={self.query.replace(' ', '+')}&page={self.page}&per_page={self.per_page}&image_type=photo"
            data = self.__build_request(url, headers)
            
            image_data: list = data['hits']
            final_result = [{
                'preview': image['previewURL'],
                'normal': image['webformatURL']
            } for image in image_data] if image_data else []
                    
        elif media_type == 'video':
            url = f"https://pixabay.com/api/videos/?key={api_key}&q={self.query.replace(' ', '+')}&page={self.page}&per_page={self.per_page}"
            
            data = self.__build_request(url, headers)
            
            video_data: list = data['hits']
            final_result = [{
                'preview': video['videos']['medium']['thumbnail'],
                'normal': video['videos']['medium']['url'],
            } for video in video_data] if video_data else []
        
        return final_result
    
    
    def __pexels(self, media_type: str):
        """This function retrieves images and videos from Pexels API

        Args:
            page (int): Page number
            per_page (int): Number of media to be retrieved from the API
            media_type (str): Should be one of `image` or `video`
        """
        
        api_key = settings.PEXELS_API_KEY
        # headers = {
        #     'Authorization': api_key,
        #     # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        #     # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0'
        #     # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        # }
        
        headers = {
            'Authorization': api_key,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        final_result = []
        
        if media_type == 'image':
            url = f"https://api.pexels.com/v1/search?query={self.query}&per_page={self.per_page}&page={self.page}"
            data = self.__build_request(url, headers)
            
            image_data: list = data['photos']
            final_result = [{
                'preview': image['src']['small'],
                'normal': image['src']['original']
            } for image in image_data] if image_data else []
                    
        elif media_type == 'video':
            url = f"https://api.pexels.com/videos/search?query={self.query}&per_page={self.per_page}&page={self.page}"
            data = self.__build_request(url, headers)
            
            video_data: list = data['videos']
            final_result = [{
                'preview': video['video_pictures'][0]['picture'],
                'normal': video['video_files'][0]['link']
            } for video in video_data] if video_data else []
        
        return final_result
    
    
    def fetch_images(self):
        images = []
        
        unsplash_images = self.__unsplash()
        # pexels_images = self.__pexels('image')
        pixabay_images = self.__pixabay('image')
        
        images.extend(unsplash_images)
        # images.extend(pexels_images)
        images.extend(pixabay_images)
        
        return images
    
    
    def fetch_videos(self):
        videos = []
        
        # pexels_videos = self.__pexels('video')
        pixabay_videos = self.__pixabay('video')
        
        # videos.extend(pexels_videos)
        videos.extend(pixabay_videos)
        
        return videos
