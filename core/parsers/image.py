import asyncio
from PIL import Image
import pytesseract

# Optional for Windows if Tesseract throws errors:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

async def image_parser(image_path: str, retries: int = 3) -> str:

    def tesseract_parse() -> str:
        """Fallback OCR with Tesseract."""
        try:
            image = Image.open(image_path).convert("RGB")
            return pytesseract.image_to_string(image)
        except Exception as e:
            print(f"[Tesseract] Exception: {e}")
            return ""
        
    try:
        print("processing via tesseract")
        return (await asyncio.to_thread(tesseract_parse)).strip()
    except Exception as e:
        print(f"Fatal exception: {e}")
        return ""
    
    
    
    
    # do not remove this code yet, we may use it later
    
    
    
    
#     import asyncio
# import os
# from PIL import Image
# import pytesseract

# async def image_parser(image_path: str) -> str:
#     def tesseract_parse(lang: str) -> str:
#         try:
#             os.environ["OMP_THREAD_LIMIT"] = str(os.cpu_count())
#             image = Image.open(image_path).convert("RGB")
#             return pytesseract.image_to_string(image, lang=lang).strip()
#         except Exception as e:
#             print(f"[Tesseract] Exception for lang={lang}: {e}")
#             return ""
#     try:
#         print(f"[OCR] Trying eng_best for '{image_path}'")
#         result = await asyncio.to_thread(tesseract_parse, "eng_best")
#         if result:
#             return result
#         print(f"[OCR] Fallback to eng for '{image_path}'")
#         result = await asyncio.to_thread(tesseract_parse, "eng")
#         if result:
#             return result
#     except Exception as e:
#         print(f"[OCR] Fatal exception: {e}")
#     return ""

