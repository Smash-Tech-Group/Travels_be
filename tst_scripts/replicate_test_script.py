import replicate, random, os
from api.utils.settings import settings
from api.utils.replicate_service import replicate_service


# env_copy = os.environ.copy()
# env_copy['REPLICATE_API_TOKEN'] = settings.REPLICATE_API_TOKEN

client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)

# Retrieve the model
# model = client.models.get("lucataco/animate-diff")

# # Get all versions of the model
# versions = model.versions.list()

# # Print the available versions
# for version in versions:
#     print(f"Version ID: {version.id}, Created at: {version.created_at}")

# result = client.run(
#     ref="lucataco/animate-diff:beecf59c4aee8d81bf04f0381033dfa10dc16e845b4ae00d281e2fa377e48a9f",
#     input = {
#         "path": "toonyou_beta3.safetensors",
#         "seed": random.randint(0, 2147483647),
#         "steps": 25,
#         "prompt": "A man writing code on his computer",
#         # "n_prompt": "badhandv4, easynegative, ng_deepnegative_v1_75t, verybadimagenegative_v1.3, bad-artist, bad_prompt_version2-neg, teeth",
#         "motion_module": "mm_sd_v14",
#         "guidance_scale": 7.5
#     }
# )

# output = client.run(
#     "black-forest-labs/flux-dev",
#     input={
#         "prompt": "black forest gateau cake spelling out the words \"FLUX DEV\", tasty, food photography, dynamic shot",
#         "guidance": 3.5,
#         "num_outputs": 1,
#         "aspect_ratio": "1:1",
#         "output_format": "png",
#         "output_quality": 80,
#         "prompt_strength": 0.8,
#         "num_inference_steps": 28
#     }
# )
# print(output)


# output = client.run(
#     "cjwbw/sadtalker:a519cc0cfebaaeade068b23899165a11ec76aaa1d2b313d40d214f204ec957a3",
#     input={
#         "facerender": "facevid2vid",
#         "pose_style": 0,
#         "preprocess": "crop",
#         "still_mode": True,
#         "driven_audio": "https://replicate.delivery/pbxt/IkgWA4bLoXpk5NwVsfOBzHh7MswfNLTgtf44Qr2gdOTOWvSX/japanese.wav",
#         "source_image": "https://replicate.delivery/pbxt/IkgW9tngATq608Qf6haUXDpg81s5YBJfS9GaBiCFjdKXk4F5/art_1.png",
#         "use_enhancer": True,
#         "use_eyeblink": True,
#         "size_of_image": 256,
#         "expression_scale": 1
#     }
# )
# print(output)

output = replicate_service.generate_talking_avatar(
    audio_url='https://replicate.delivery/pbxt/IkgWA4bLoXpk5NwVsfOBzHh7MswfNLTgtf44Qr2gdOTOWvSX/japanese.wav',
    image_url="https://replicate.delivery/pbxt/IkgW9tngATq608Qf6haUXDpg81s5YBJfS9GaBiCFjdKXk4F5/art_1.png"
)
print(output)

# print(result)
