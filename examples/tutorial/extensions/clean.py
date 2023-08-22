import shutil
from palgen import Extension

class Clean(Extension):
    def run(self, *_):
        if self.out_path.exists():
            shutil.rmtree(self.out_path)
