import requests
from api.loggers.app_logger import app_logger


class TelexIntegration:
    
    def __init__(self, webhook_id: str):
        self.webhook_id = webhook_id
        self.url = f'https://ping.telex.im/v1/webhooks/{self.webhook_id}'
        app_logger.info(f'Opening {self.url}')
        
    
    def push_message (
        self, 
        event_name: str, 
        message: str,
        status: str = 'success'
    ):
        """This finction sends a notification to telex through a webhook

        Args:
            event_name (str): Name of the event to send notification for
            message (str): Message for the enent
            status (str, optional): Status of the event. Defaults to 'success'.
        """
                
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        data ={
            "event_name": event_name,
            "message": message,
            "status": status,
            "username": "tifi.tv"
        }
        
        try:
            # response = requests.post(self.url, headers=headers, params=data)
            response = requests.get(self.url, params=data)
            
            if response.status_code == 200:
                app_logger.info('Message sent successfully to telex')
                app_logger.info(response.json())
            else:
                app_logger.info(f'Error sending message to telex: {response.status_code}')
                
        except Exception as e:
            app_logger.info(f'Exception occured while sending message to telex: {e}')
