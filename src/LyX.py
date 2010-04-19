class LyX:
    def __init__(self):
        self.title = "No Title"
        self.author = "No Author"
        self.chapter_names = []
        self.chapters = []
    
    def addChapter(self, title, content):
        print "Adding: " + title
        self.chapter_names.append(title)
        self.chapters.append(content)
        
        return
