import shutil
from palgen import Extension, max_jobs

class Clean(Extension):

    @max_jobs(1)
    def run(self, *_):
        if self.out_path.exists():
            shutil.rmtree(self.out_path)
