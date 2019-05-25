from pygame import *
font.init()

screen = display.set_mode()

# takes in rect (x,y,w,h), text (string), colour (r,g,b), font (string), font size (int), layer (int)
class Text:
    def __init__(self, rect, text, colour, fontStyle, fontSize, lineSpacing=30, wrap=False, centered=False):
        self.textColour = colour
        self.lineSpacing = lineSpacing
        self.wrap = wrap
        self.fontStyle = fontStyle
        self.fontSize = fontSize
        f = font.SysFont(fontStyle, fontSize) # initialize font
        
        if wrap: # if wrap, get a list of lines from the text wrapping function
            self.text = wrapText(text, fontStyle, fontSize, rect, lineSpacing)
        else: # otherwise put the one line in a list
            self.text = [text]
        
        # renders the list of lines
        self.textImg= [f.render (line,1, colour) for line in self.text]
            
        if centered: # centers the text in the rect
            self.rect = self.textImg[0].get_rect(center=(rect[0]+rect[2]//2, rect[1]+rect[3]//2))
        else:
            self.rect = rect
    def update (self, newText=""):
        if newText != "":
            if self.wrap:
                self.text = wrapText(newText, self.fontStyle, self.fontSize, self.rect, self.lineSpacing)
            else:
                self.text = [newText]
            
        f = font.SysFont(self.fontStyle, self.fontSize) # initialize font
        self.textImg= [f.render (line,1, self.textColour) for line in self.text]  
    def draw(self):
        x,y,w,h = self.rect
        i = 0
        for img in self.textImg: # blits every line
            screen.blit(img, (x,y+i*self.lineSpacing,w,h))
            i += 1

# faster and easier
class SimpleText:
    def __init__(self, rect, text, size=14, colour=(0,0,0)):
        self.rect = rect
        self.font = font.SysFont("lucida console", size) # initialize font
        self.text = text
        self.surf = self.font.render (text,False,colour)
        self.colour = colour
    def update (self, newText=""):
        self.text = newText
        self.surf = self.font.render (newText,False,self.colour)  
    def draw(self):
        screen.blit(self.surf, self.rect)

# Can use a colour (r,g,b) or a sprite (Surface)
class Button:
    def __init__(self, rect, function, colour=(150,150,150), hoveredColour=(100,100,100), sprite=None):
        self.rect = rect
        self.sprite = sprite
        if self.sprite == None: # must take in a sprite or colour
            self.colour = colour
            self.colourHov = hoveredColour
        else:
            self.surf = transform.scale(self.sprite, (self.rect[2], self.rect[3]))
        self.function = function
        self.hovered = False
    def pressed(self):
        self.function()
    def draw(self):
        if self.sprite == None:
            if self.hovered:
                draw.rect(screen, self.colourHov, self.rect)
            else:
                draw.rect(screen, self.colour, self.rect)
        else:
            screen.blit(self.surf, (self.rect[0], self.rect[1]))

class Image:
    def __init__(self, rect, sprite):
        self.rect = rect
        self.sprite = sprite
        self.surf = transform.scale(self.sprite, (rect[2], rect[3]))
    def resize (self, newW, newH):
        self.surf = transform.scale(self.sprite, (rect[2], rect[3]))
    def draw(self):
        screen.blit(self.surf, self.rect)

# returns list of strings
# takes in text (string), font (string), font size (int), rect (4 ints: x,y,w,h), byWord (boolean), line spacing (int)
def wrapText (text, fontStyle, fontSize, rect, byWord=True, lineSpacing=30):
    fontStyle = font.SysFont(fontStyle, fontSize)
    charW, charH = fontStyle.size("a")
    
    lines = []
    rectW, rectH = rect[2], rect[3]
    numLetters = rectW // charW # chars per line
    
    if charH*2-lineSpacing != 0:
        numLines = rectH // charH # num of lines that fit in the height
    else:
        numLines = 1
        print("division by 0")
    lastSpace = 0 # index of space closest to end
    for i in range (numLines):
        if byWord:
            line = text[0:numLetters]
            
            lastSpace = line.rfind(" ")
            if lastSpace == -1:
                lastSpace = len(line)
                
            wrapped = line[0:lastSpace+1]
            text = text[lastSpace+1:]
        else:
            wrapped = text[i*numLetters:(i+1)*numLetters]
        lines.append(wrapped)
    return lines