import torch
import gc
from diffusers import LTXPipeline, LTXImageToVideoPipeline
from diffusers.utils import export_to_video
from PIL import Image

class LTXInference:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline_t2v = None
        self.pipeline_i2v = None
        self.model_id = "Lightricks/LTX-Video"

    def _load_t2v_pipeline(self):
        if self.pipeline_t2v is None:
            print("Loading T2V pipeline...")
            self.pipeline_t2v = LTXPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.bfloat16
            )
            # Memory optimization for 8GB VRAM
            self.pipeline_t2v.enable_sequential_cpu_offload()
            print("T2V pipeline loaded and optimized.")
            
    def _load_i2v_pipeline(self):
        if self.pipeline_i2v is None:
            print("Loading I2V pipeline...")
            self.pipeline_i2v = LTXImageToVideoPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.bfloat16
            )
            # Memory optimization for 8GB VRAM
            self.pipeline_i2v.enable_sequential_cpu_offload()
    def _free_memory(self):
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def generate_video(
        self, 
        prompt: str, 
        output_path: str,
        negative_prompt: str = "worst quality, inconsistent motion, blurry, jittery, distorted",
        width: int = 512,
        height: int = 320,
        num_frames: int = 49,
        num_inference_steps: int = 25
    ):
        try:
            self._load_t2v_pipeline()
            self._free_memory()
            
            print(f"Generating video for prompt: {prompt}")
            video = self.pipeline_t2v(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps
            ).frames[0]
            
            export_to_video(video, output_path, fps=24)
            print(f"Video saved to {output_path}")
            return True
        except Exception as e:
            print(f"Error during T2V generation: {e}")
            raise e
        finally:
            self.pipeline_t2v = None
            self._free_memory()

    def generate_video_from_image(
        self,
        image_path: str,
        prompt: str,
        output_path: str,
        negative_prompt: str = "worst quality, inconsistent motion, blurry, jittery, distorted",
        width: int = 512,
        height: int = 320,
        num_frames: int = 49,
        num_inference_steps: int = 25
    ):
        try:
            self._load_i2v_pipeline()
            self._free_memory()
            
            print(f"Loading image from {image_path}")
            image = Image.open(image_path).convert("RGB")
            # Resize image to match output dimensions to avoid aspect ratio errors
            image = image.resize((width, height), Image.LANCZOS)
            
            print(f"Generating I2V for prompt: {prompt}")
            video = self.pipeline_i2v(
                image=image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps
            ).frames[0]
            
            export_to_video(video, output_path, fps=24)
            print(f"Video saved to {output_path}")
            return True
        except Exception as e:
            print(f"Error during I2V generation: {e}")
            raise e
        finally:
            self.pipeline_i2v = None
            self._free_memory()
