
import pandas as pd
from PIL import Image
from pypdf import PdfReader

class Resource:

    # def __init__(self):

    @property
    def raw_file(self) -> str:
        pass

    @property
    def response_header(self):
        pass

    @property
    def sreenshot_reader(self) -> PdfReader:
        pass

    @property
    def sreenshot_file(self) -> str:
        pass

    def text(self) -> str:
        pass

    def tables(self) -> list[pd.DataFrame]:
        pass

    def images(self) -> list[Image.Image]:
        pass

    def links(self) -> list[str]:
        pass