from fastapi import HTTPException
from pytwitter import Api

from api.utils.settings import settings


class TweetService:
    def __init__(self):
        self.api = Api(bearer_token=settings.TWITTER_BEARER_TOKEN)
        
    def get_tweet(self, link: str):
        tweet_id = link.split('/')[-1].split('?')[0].strip()
        # self.api.get_tweet(tweet_id, expansions=["attachments.media_keys"], media_fields=["type","duration_ms"])
        response = self.api.get_tweet(tweet_id)
        print(response)
        if response.data and response.data.text:
            return response.data.text.strip()
        else:
            raise HTTPException(status_code=400, detail='Could not fetch tweet. Check that you entered a valid link')


tweet_service = TweetService()
