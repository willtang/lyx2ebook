class Epub:
    def __init__(self):
        self.source_file = ''
        self.set_base_folder('.')

    def set_base_folder(self, folder):
        self.base_folder = folder
        self.meta_folder = self.base_folder + "/META-INF"
        self.ops_folder = self.base_folder + "/OPS"
        self.css_folder = self.ops_folder + "/css"
    
    def convertFromLyx(self, lyx):
        pass