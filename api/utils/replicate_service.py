from typing import Dict, Any
import replicate, time

from api.utils.settings import settings


inpaint_image_prompts = [
    "Photo of a person wearing a casual shirt, standing in a garden, with a friendly expression.",
    "A realistic portrait of someone wearing formal attire, sitting in an office setting.",
    "A photograph of an individual standing confidently on a city street, wearing a stylish outfit.",
    "Picture of a person relaxing in a park, wearing casual summer clothing.",
    "A full-body portrait of an individual in a studio, posing with a professional background.",
    "An image of someone seated at a café table, enjoying a cup of coffee while reading a book.",
    "Portrait of an individual in a beach setting, dressed in summer wear, with the ocean in the background.",
    "A portrait of a person standing in a sunny field, wearing a casual outfit and looking at the horizon.",
    "A close-up photo of an individual sitting on a park bench, wearing a cozy sweater and gazing thoughtfully into the distance.",
    "An image of a person standing by a lake, hands in pockets, with mountains in the background.",
    "A full-body photo of someone leaning against a brick wall, dressed casually, with a neutral expression.",
    "A person seated at a café table, with a coffee cup in front of them and a book partially open.",
    "A portrait of an individual standing near a vintage car, dressed in retro-style clothing and posing confidently.",
    "A person sitting on the edge of a wooden pier, looking out over calm water, dressed in simple attire.",
    "A static image of someone standing in a library, holding a book and looking at the camera with a soft smile.",
    "A person standing in the middle of a cobblestone street, with colorful buildings in the background, dressed casually.",
    "A photo of an individual sitting on a window sill, looking outside at the rain, dressed in warm indoor clothing.",
    "A person standing on a sandy beach, with waves gently lapping in the background, wearing comfortable vacation attire.",
    "An individual seated at an outdoor table, surrounded by greenery, with a gentle expression and relaxed posture.",
    "A person standing at the entrance of a museum, wearing a smart-casual outfit and holding a guidebook.",
    "A static image of an individual standing under a cherry blossom tree, petals falling gently around them.",
    "A photo of someone sitting cross-legged on the floor of a cozy room, surrounded by books and soft lighting.",
    "A person standing on a balcony overlooking a cityscape, dressed in modern casual wear and holding a mug.",
    "An individual standing in a modern art gallery, observing a large painting, with a contemplative look.",
    "A photo of a person standing in a rustic kitchen, wearing an apron and holding a wooden spoon.",
    "An individual seated on a stone bench in a quiet garden, with their hands resting gently on their lap.",
    "A portrait of a person standing in front of a colorful mural, wearing trendy clothing and smiling slightly.",
    "A person seated under an umbrella at the beach, holding a pair of sunglasses and looking off to the side.",
    "An individual standing in the middle of a forest path, surrounded by tall trees and dappled sunlight.",
    "A person standing in a historic town square, with a backpack on, looking at the buildings around them.",
    "An image of someone sitting on a park bench, surrounded by fallen autumn leaves, wearing a scarf and coat.",
    "A person standing in a sunlit meadow, with flowers blooming around them and a serene expression.",
    "A static photo of someone standing on a wooden bridge over a stream, dressed in outdoor clothing."
]


class ReplicateService:
    
    def __init__(self):
        self.client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        
    
    def __run_model(self, model_id: str, input: Dict[str, Any]):
        print(f'Running model {model_id}')
        
        # Start the prediction
        prediction = self.client.predictions.create(
            version=model_id.split(':')[-1],
            input=input
        )
        print(f"Prediction started with ID: {prediction.id}")

        # Poll the prediction status
        while prediction.status not in ["succeeded", "failed", "canceled"]:
            print(f"Status: {prediction.status}... Waiting for completion.")
            time.sleep(5)  # Wait for a few seconds before polling again
            
            # Fetch the updated status
            prediction = self.client.predictions.get(prediction.id)
            print(prediction.logs)
        
        if prediction.status == "succeeded":
            print(f"Prediction succeeded: {prediction.output}")
            return prediction.output
        
        elif prediction.status == "failed":
            print(f"Prediction failed: {prediction.error}")
            raise Exception(f"Prediction failed: {prediction.error}")
        
        else:
            print(f"Prediction was canceled or an unknown error occurred.")
            raise Exception(f"Prediction status: {prediction.status}")
    
    
    def convert_text_to_speech(
        self, 
        text: str, 
        sample_audio_file: str,
        language: str = 'en'
    ):
        """This function converts text to speech

        Args:
            text (str): Text to be converted to audio file
            sample_audio_file (str): This is a file or url that links to a sample voice that willbe used as the voice for the generated audio file
            language (str, optional): Language of the generated audio. Defaults to 'en'.

        Returns:
            str: The URL of the audio generated
        """
        
        output = self.__run_model(
            "lucataco/xtts-v2:684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e",
            input={
                "text": text,
                "speaker": sample_audio_file,
                "language": language,
                "cleanup_voice": False
            }
        )
        
        return output
    
    
    def generate_image(self, prompt: str, num_outputs: int=3, img_width: int=1024, img_height: int=1024):
        """This function uses stable diffusion to generate an image

        Args:
            prompt (str): Description of the image to be generated
            num_outputs (int): Number of images to be generated
            img_width (int): Width of image to be generated
            img_height (int): Height of image to be generated

        Returns:
            _type_: _description_
        """
        
        output = self.__run_model(
            # "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
            # input={
            #     "width": img_width,
            #     "height": img_height,
            #     "prompt": prompt,
            #     "scheduler": "K_EULER",
            #     "num_outputs": num_outputs,
            #     "guidance_scale": 7.5,
            #     "num_inference_steps": 50
            # }
            
            "bytedance/sdxl-lightning-4step:5599ed30703defd1d160a25a63321b4dec97101d98b4674bcc56e41f62f35637",
            input={
                "width": img_width,
                "height": img_height,
                "prompt": prompt,
                "scheduler": "K_EULER",
                "num_outputs": num_outputs,
                "guidance_scale": 0,
                "negative_prompt": "worst quality, low quality",
                "num_inference_steps": 4
            }
        )
        
        return output
    
    
    def generate_talking_avatar(
        self, 
        image_url: str, 
        audio_url: str,
        generate_full: bool = False
    ):
        
        # output = self.__run_model(
        #     "lucataco/sadtalker:85c698db7c0a66d5011435d0191db323034e1da04b912a6d365833141b6a285b",
        #     input={
        #         "driven_audio": audio_url,
        #         "source_image": image_url,
        #         "still": True,
        #         "enhancer": "gfpgan",
        #         "preprocess": "full"
        #     }
        # )
        
        output = self.__run_model(
            "cjwbw/sadtalker:a519cc0cfebaaeade068b23899165a11ec76aaa1d2b313d40d214f204ec957a3",
            input={
                # "facerender": "pirender",
                "facerender": "facevid2vid",
                "preprocess": "full" if generate_full else 'crop',
                "still_mode": True,
                "driven_audio": audio_url,
                "source_image": image_url,
                "use_enhancer": True,
                "use_eyeblink": True,
                "size_of_image": 256,
                "pose_style": 1,
                "expression_scale": 1
            }
        )
        
        return output
    
    
    def generate_inpaint_image(self, image_url: str, prompt: str):
        
        output = self.__run_model(
            # "lucataco/ip_adapter-face:b6618893d3d0ee4a9b3a1e990a00be6bd6c3b6fddef83e0b68efc525de54580c",
            # input={
            #     "seed": 15251,
            #     "image": image_url,
            #     "prompt": prompt,
            #     "num_outputs": 1,
            #     "num_inference_steps": 50
            # }
            "lucataco/ip_adapter-sdxl-face:226c6bf67a75a129b0f978e518fed33e1fb13956e15761c1ac53c9d2f898c9af",
            input={
                "seed": 42,
                "image": image_url,
                "scale": 0.6,
                "prompt": f'{prompt}, portrait, half picture, realistic, no facial expression, neutral facial expression',
                "num_outputs": 1,
                "negative_prompt": "",
                "num_inference_steps": 30
            }
        )
        
        return output
    
    
    def generate_video(self, prompt: str, width: int=1024, height: int=1024, num_outputs: int=3):
        
        final_output = []
        
        for _ in range(num_outputs):
            output = self.__run_model(
                "lucataco/hotshot-xl:78b3a6257e16e4b241245d65c8b2b81ea2e1ff7ed4c55306b511509ddbfd327a",
                input={
                    "mp4": True,
                    "seed": 6226,
                    "steps": 30,
                    "width": width,
                    "height": height,
                    "prompt": f'{prompt}, 5 seconds minimum, realistic',
                    "scheduler": "EulerAncestralDiscreteScheduler",
                    "negative_prompt": "blurry"
                }
            )
            
            final_output.append(output)
        return final_output


replicate_service = ReplicateService()
