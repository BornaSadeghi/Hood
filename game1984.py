from pygame import *
from geometry import rectCollision, inRect
from gui import Image, SimpleText, Button
import random, math, spritesheet

mixer.quit()  # somehow, this reduces audio lag
mixer.init(44100, -16, 2, 2048)
init()

SCREEN_W, SCREEN_H = 800,600
screen = display.set_mode((SCREEN_W, SCREEN_H)) 

clock = time.Clock()
FRAMERATE = 60 # locked to this frame rate    
STATE = 1 # 0:game, 1:menu 2:death

WHITE = 255,255,255
BLACK = 0,0,0
GREY = 100,100,100
LIGHTGREY = 200,200,200
LIGHTBLUE = 150,150,255
RED = 255,0,0
DARKRED = 140,80,80
BROWN = 150,50,0
YELLOW = 255,255,0
GREEN = 0,255,0
DULLGREEN = 100,150,100
DARKDULLGREEN = 50,100,50

titleSprite = image.load("sprites\\title.png")
sprites = spritesheet.sheetToSpriteArray("sprites\\sheet1984.png", (16,16))

soundDoorClose = mixer.Sound("sounds\\door_close.wav")
soundEnemyHit = mixer.Sound("sounds\\enemy_hit.wav")
soundKeyPickup = mixer.Sound("sounds\\key_pickup.wav")
soundPlayerHit = mixer.Sound("sounds\\player_hit.wav")
soundBottle = mixer.Sound("sounds\\bottle.wav")
soundPageFlip = mixer.Sound("sounds\\page_flip.wav")

highScoreFile = "highscore.dat"

display.set_caption("Hood")
display.set_icon(sprites[4])

cellSize = 50
gridWMax = 64
gridW = 16
gridH = gridW

mapRect = 0,0,gridW*cellSize, gridH*cellSize

numOpenCells = gridW*gridH

SIN45 = 0.70710678118
level = 1

class Camera:
    def __init__(self, target):
        self.pX, self.pY = 0,0
        self.target = target
        self.dampX, self.dampY = 20,20
    def update(self):
        targetX, targetY = self.target.rect.centerx-SCREEN_W//2, self.target.rect.centery-SCREEN_H//2
        self.pX = lerp(self.pX, targetX, self.dampX)
        self.pY = lerp(self.pY, targetY, self.dampY)
    def reset(self):
        targetX = self.target.rect.centerx-SCREEN_W//2
        self.pX = targetX
        self.pY = -SCREEN_H

class Tile:
    def __init__(self, x=0, y=0, wall=True):
        self.x, self.y, self.w, self.h = x, y, SCREEN_W//gridW, SCREEN_H//gridH
        self.rect = x*cellSize, y*cellSize, cellSize, cellSize
        self.wall = wall
    def draw(self):
        rect = self.rect[0]-cam.pX, self.rect[1]-cam.pY, self.rect[2], self.rect[3]
        if cull(rect, mapRect):
            screen.blit(self.sprite, rect[:2])

# anything that lives and moves
class LivingEntity:
    def __init__(self, pos=(0,0), moveSpeed=4):
        self.x, self.y = pos # position in tiles
        self.pX, self.pY = self.x*cellSize,self.y*cellSize # position in pixels
        self.dX, self.dY = 0,0 # direction
        self.vX, self.vY = 0,0 # velocity in pixels
        self.rect = Rect(self.pX, self.pY, cellSize, cellSize)
        self.hitboxRel = 3,3,-6,-6 # dimension difference between hitbox and rect
        self.hitbox = Rect(self.pX+self.hitboxRel[0], self.pY+self.hitboxRel[1], self.rect[2]+self.hitboxRel[2], self.rect[3]+self.hitboxRel[3])
        self.speed = moveSpeed # pixels per frame
        self.damp = 4
        
        self.maxHealth = 100
        self.health = self.maxHealth
    def update(self):
        self.collisions()
        self.hitbox[0], self.hitbox[1] = self.rect[0]+self.hitboxRel[0], self.rect[1]+self.hitboxRel[1]
        
#         speed = self.speed*gridWOrig/gridW
        self.pX += self.vX
        self.pY += self.vY
        
        speed = self.speed*SIN45 if self==Player and abs(self.dX)==abs(self.dY) else self.speed 
        
        self.vX = lerp(self.vX, self.dX*speed, self.damp)
        self.vY = lerp(self.vY, self.dY*speed, self.damp)

        if self.pX < 0:
            self.pX = 0
        elif self.pX > (gridW-1)*cellSize:
            self.pX = (gridW-1)*cellSize
        if self.pY < 0:
            self.pY = 0
        elif self.pY > (gridH-1)*cellSize:
            self.pY = (gridH-1)*cellSize
        
        self.x, self.y = coordFormat(self.pX, self.pY) # convert to grid pos
        
        self.rect[0], self.rect[1] = self.pX,self.pY
    def bloodParticles (self):
        effect = ParticleEffect(self.rect.center, duration=0.15, velRange=4)
    def collisions(self):
        # fast method of collisions that does not require checking all walls
        # checks if there is a wall adjacent to the squares that the hitbox occupies
        
        hX, hY, hW, hH = self.hitbox
        hX, hY, hW, hH = hX/cellSize, hY/cellSize, hW/cellSize, hH/cellSize
        
        corners = (hX, hY), (hX+hW, hY), (hX+hW, hY+hH), (hX, hY+hH) # corners in grid coords
        for x,y in corners:
            x,y = int(x), int(y)
            
            if x > 0 and grid[x-1][y].wall and hX+self.vX/cellSize < x and self.vX < 0:
                self.vX = 0
            elif x < gridW-1 and grid[x+1][y].wall and hX+hW+self.vX/cellSize > x+0.99 and self.vX > 0:
                self.vX = 0
            
            elif y > 0 and grid[x][y-1].wall and hY+self.vY/cellSize < y and self.vY < 0:
                self.vY = 0
            elif y < gridH-1 and grid[x][y+1].wall and hY+hH+self.vY/cellSize > y+0.99 and self.vY > 0:
                self.vY = 0
            
#             if type(self) == Friend or type(self) == Enemy:
#                 draw.circle(screen, WHITE, (x*cellSize+cellSize//2-cam.pX,y*cellSize+cellSize//2-cam.pY), cellSize//2)
    
class Player (LivingEntity):
    def __init__(self, x=0, y=0):
        super().__init__(random.choice(openCells))
        self.score = 0
        self.damage = 40
        
        self.attackRadius = 100 # pixels
        self.attackSpeed = 2 # per second
        self.knockback = 10
        self.canAttack = True # has enough time passed since last attack?
        self.hasKey = False
        self.friends = 0 
        self.hitboxRel = 16,2,-32,-4
        self.hitbox = Rect(self.pX+self.hitboxRel[0], self.pY+self.hitboxRel[1], self.rect[2]+self.hitboxRel[2], self.rect[3]+self.hitboxRel[3]) 
        
        self.sprite = transform.scale(sprites[2], (self.rect[2], self.rect[3]))
        self.frameCount = 0
    def update(self):
        global level
        super().update()
        
        healthBar[2] = int(lerp(healthBar[2],(self.health/self.maxHealth)*SCREEN_W))
        healthText.update("Health: %d / %d" % (self.health,self.maxHealth))
        scoreText.update("Score: %d, Level: %d" %(self.score,level))
        
        self.hitbox[0], self.hitbox[1] = self.rect[0]+self.hitboxRel[0], self.rect[1]+self.hitboxRel[1] 
        
        self.frameCount += 1
        if self.frameCount > 60/self.attackSpeed:
            self.canAttack = True
    def attack (self): # attack enemies
        if self.canAttack:
            self.canAttack = False
            self.frameCount = 0
            for enemy in enemies:
                if math.hypot(enemy.pX-self.pX, enemy.pY-self.pY) < self.attackRadius+cellSize:
                    enemy.health -= self.damage
                    enemy.bloodParticles()
                    soundEnemyHit.play()
                    enemy.vX = -enemy.dX*self.knockback + self.vX*self.knockback
                    enemy.vY = -enemy.dY*self.knockback + self.vY*self.knockback
                    if enemy.health <= 0:
                        enemies.remove(enemy)
                        self.score += 10
            draw.circle(screen, WHITE, (int(self.pX)+cellSize//2-int(cam.pX), int(self.pY)+cellSize//2-int(cam.pY)), self.attackRadius)
    def reset(self):
        self.vX = self.vY = 0
        self.x,self.y = random.choice(openCells)
        self.pX, self.pY = self.x*cellSize,self.y*cellSize
        self.hasKey = False
        self.friends = 0
        
        cam.reset()
    def draw(self):
        pos = int(self.rect[0]-cam.pX), int(self.rect[1]-cam.pY)
        screen.blit(self.sprite, pos)
        
        attackRadiusPos = int(self.rect.centerx-cam.pX), int(self.rect.centery-cam.pY)
        draw.circle(screen, WHITE, attackRadiusPos, self.attackRadius, 1)
        draw.rect(screen, DARKRED, maxHealthBar)
        draw.rect(screen, GREEN, healthBar)
        
class Enemy (LivingEntity):
    def __init__(self):
        super().__init__(random.choice(openCells))
        self.speed = 1
        self.damp = random.randint(2,6)
        self.damage = 15
        self.attackSpeed = 1 # per second
        self.knockback = 1
        
        self.hitbox = Rect(self.pX+self.hitboxRel[0], self.pY+self.hitboxRel[1], self.rect[2]+self.hitboxRel[2], self.rect[3]+self.hitboxRel[3])
        self.sprite = transform.scale(sprites[4], (self.rect[2], self.rect[3]))
        self.rot = 0 # rotation of sprite
        self.frameCount = 0 # limits attack rate
    def chase (self):
        global STATE
        d = math.hypot(player.x-self.x, player.y-self.y)
        if d > 0.5:
            self.dX = (player.x-self.x)/d
            self.dY = (player.y-self.y)/d
            
        # ALLOW FRIENDS TO GET HIT
        if self.frameCount > 60/self.attackSpeed:
            if rectCollision(self.hitbox, player.hitbox):
                self.frameCount = 0
                player.health -= self.damage
                player.bloodParticles()
                soundPlayerHit.play()
                player.vX += self.vX*self.knockback
                player.vY += self.vY*self.knockback
                if player.health <= 0:
                    if player.score > getHighScore():
                        setHighScore(player.score)
                    STATE = 2
                    newLevel()
                    
            for f in friends:
                if rectCollision(self.hitbox, f.hitbox):
                    self.frameCount = 0
                    f.health -= self.damage
                    f.bloodParticles()
                    f.vX += self.vX*self.knockback
                    f.vY += self.vY*self.knockback
                    if f.health <= 0:
                        friends.remove(f)
        
        if self.pY-player.pY != 0:
            self.rot = rotateTowards(self.rect.center, player.rect.center)
                
        self.frameCount += 1
    def draw(self):
        if cull(self.rect, mapRect):
            sprite = transform.rotate(self.sprite, self.rot)
            center = self.rect.center # prevent shifting when rotated
            offX, offY = sprite.get_rect(center=(center))[:2]
            pos = offX-cam.pX, offY-cam.pY
            
            screen.blit(sprite, pos)

class Friend (LivingEntity):
    def __init__(self):
        super().__init__(random.choice(openCells))
        self.speed = 2
        self.pickedUp = False # has the player got this person to follow them?
        self.sprite = transform.scale(sprites[3], (self.rect[2], self.rect[3]))
        self.hitboxRel = 16,2,-32,-4
        self.hitbox = Rect(self.pX+self.hitboxRel[0], self.pY+self.hitboxRel[1], self.rect[2]+self.hitboxRel[2], self.rect[3]+self.hitboxRel[3])
        
        self.health = 50
    def follow(self):
        d = math.hypot(player.x-self.x, player.y-self.y)
        if d > 1:
            self.dX = (player.x-self.x)/d
            self.dY = (player.y-self.y)/d
        else:
            self.dX = self.dY = 0
    def checkPickup(self):
        if rectCollision(self.rect, player.rect):
            self.pickedUp = True
            player.score += 2
            player.friends += 1
    def draw(self):
        if cull(self.rect, mapRect):
            pos = self.rect[0]-cam.pX, self.rect[1]-cam.pY
            screen.blit(self.sprite, pos)

class Exit: # door to next level
    def __init__(self, pos=(0,0)):
        self.x, self.y = pos
        self.pX, self.pY = self.x*cellSize,self.y*cellSize
        self.rect = Rect(self.pX, self.pY, cellSize, cellSize)
        
        self.sprite = transform.scale(sprites[5], (self.rect[2], self.rect[3]))
    def checkAccess(self): # check if the player is using the door
        global level
        if rectCollision(self.rect, player.rect) and player.hasKey:
            soundDoorClose.play()
            player.score += 20 + 20*player.friends
            level += 1
            newLevel()
    def draw(self):
        if cull(self.rect, mapRect):
            pos = self.rect[0]-cam.pX, self.rect[1]-cam.pY
            screen.blit(self.sprite, pos)

class Item:
    def __init__(self, pos=(0,0)):
        self.x, self.y = pos
        self.pX, self.pY = self.x*cellSize, self.y*cellSize
        self.rect = Rect(self.pX, self.pY, cellSize, cellSize)
    def checkPickup(self):
        if rectCollision(self.rect, player.rect):
            items.remove(self)
            ParticleEffect(self.rect.center, 50, YELLOW, 8, duration=0.25)
            self.pickedUp()
            player.score += 2
        
class Key (Item):
    def __init__(self, pos=(0,0)):
        super().__init__(random.choice(openCells))
        self.sprite = transform.scale(sprites[6], (self.rect[2], self.rect[3]))
    def pickedUp(self):
        player.hasKey = True
        soundKeyPickup.play()
    def draw(self):
        if cull(self.rect, mapRect):
            pos = self.rect[0]-cam.pX, self.rect[1]-cam.pY
            screen.blit(self.sprite, pos)

class Heal (Item): # victory cigarettes
    def __init__(self, pos=(0,0)):
        super().__init__(random.choice(openCells))
        self.heal = random.randint(5,15)
        self.sprite = transform.scale(sprites[7], (self.rect[2], self.rect[3]))
    def pickedUp(self):
        soundPageFlip.play()
        player.health += self.heal
        if player.health > player.maxHealth:
            player.health = player.maxHealth
    def draw(self):
        if cull(self.rect, mapRect):
            pos = self.rect[0]-cam.pX, self.rect[1]-cam.pY
            screen.blit(self.sprite, pos)

class MaxHealthIncrease (Item): # victory gin
    def __init__(self, pos=(0,0)):
        super().__init__(random.choice(openCells))
        self.healthIncrease = random.randint(4,6)
        self.sprite = transform.scale(sprites[8], (self.rect[2], self.rect[3]))
    def pickedUp(self):
        soundBottle.play()
        player.maxHealth += self.healthIncrease
        player.health += self.healthIncrease
    def draw(self):
        if cull(self.rect, mapRect):
            pos = self.rect[0]-cam.pX, self.rect[1]-cam.pY
            screen.blit(self.sprite, pos)
            
class AttackRangeIncrease(Item):
    def __init__(self):
        super().__init__(random.choice(openCells))
        self.rangeIncrease = 2 # attack radius in pixels
        self.sprite = transform.scale(sprites[9], (self.rect[2], self.rect[3]))
    def pickedUp(self):
        soundPageFlip.play()
        player.attackRadius += self.rangeIncrease
    def draw(self): 
        if cull(self.rect, mapRect):
            pos = self.rect[0]-cam.pX, self.rect[1]-cam.pY
            screen.blit(self.sprite, pos)
        
# particles are just rectangles that use physics
class Particle: # every particle from a particle effect
    def __init__(self, pos, colour=RED, particleSize=4, velRange=1, gravityMod=0.5):
        self.pX, self.pY = pos
        self.vX, self.vY = random.uniform(-velRange, velRange), random.uniform(-velRange, velRange)
        self.size = particleSize
        
        self.rect = self.pX, self.pY, self.size, self.size
        
        self.colour = colour
    def update(self):
        self.pX += self.vX
        self.pY -= self.vY
    def draw(self):
        rect = self.pX-cam.pX, self.pY-cam.pY, self.size, self.size
        draw.rect(screen, self.colour, rect)

# -1 duration is infinite
# particleRate is number of particles per second
class ParticleEffect:
    def __init__(self, pos, particleRate=200, particleColour=RED, particleSize=4, velRange=2, duration=-1):
        self.pX, self.pY = pos
        self.particleSize = particleSize
        self.colour = particleColour
        
        self.velRange = velRange # range of velocity of each particle
        self.spawnRate = particleRate
        self.particles = []
        particleEffects.append(self)
        
        self.duration = duration
        # frames until effect ends
        self.lifetimeFrames = duration * FRAMERATE
        # frames since last particle appeared
        self.framesSinceGen = 60 / self.spawnRate

    def update (self):
        if self.duration == -1:  # if the effect is infinite
            if self.framesSinceGen >= 60 / self.spawnRate:
                self.framesSinceGen = 0
                self.particles.append(Particle((self.pX, self.pY), self.colour, self.particleSize, self.velRange))
        
        else: # if effect is not infinite, eventually stop particle generation
            if self.lifetimeFrames <= 0:
                particleEffects.remove(self)
                return
            elif self.framesSinceGen >= 60 / self.spawnRate:
                self.framesSinceGen = 0
                self.particles.append(Particle((self.pX, self.pY), self.colour, self.particleSize, self.velRange))
        
        for p in self.particles:
            if cull(p.rect, mapRect):
                p.update()
            else:
                self.particles.remove(p)
        
        self.lifetimeFrames -= 1
        self.framesSinceGen += 1

    def draw(self):
        for p in self.particles:
            p.draw()

class TitleEye:
    def __init__(self, pos=(0,0)):
        self.pX, self.pY = pos
        self.rect = Rect(self.pX, self.pY, 40,40)
        
        self.sprite = transform.scale(sprites[4], (self.rect[2], self.rect[3]))
    def draw(self):
        rot = rotateTowards(self.rect.center, (mouseX, mouseY))
        
        sprite = transform.rotate(self.sprite, rot)
        center = self.rect.center # prevent shifting when rotated
        offX, offY = sprite.get_rect(center=(center))[:2]
        pos = offX, offY
            
        screen.blit(sprite, pos)

def drawAllTiles():
    for col in grid:
        for tile in col:
            tile.draw()

grid = []
openCells = []

def newGrid():
    global grid,openCells
    grid,openCells = [],[]
    for x in range (gridW):
        grid.append([])
        for y in range (gridH):
            grid[x].append(Tile(x,y))
            
    # randomly generate open spaces with a "digger" that digs out the rooms
    digX, digY = random.randrange(0,gridW), random.randrange(0,gridH)
    for _ in range (numOpenCells):
        grid[digX][digY].wall = False
        # randomly choose between x and y axis for digger movement
        dirs = []
        if digX > 0: # left
            dirs.append((-1,0))
        if digX < gridW-1: # right
            dirs.append((1,0))
        if digY > 0: # up
            dirs.append((0,-1))
        if digY < gridH-1: # down
            dirs.append((0,1))
        dir = random.choice(dirs)
        digX += dir[0]
        digY += dir[1]

    for x in range (gridW):
        for y in range (gridH):
            if grid[x][y].wall:
                grid[x][y].sprite = transform.scale(sprites[1], (cellSize, cellSize))
            else:
                openCells.append((x,y))
                grid[x][y].sprite = transform.scale(sprites[0], (cellSize, cellSize))

def newEntities():
    global player,enemies,friends,items,particleEffects,door
    door = Exit(random.choice(openCells))
    openCells.remove((door.x, door.y))
    player.reset()
    enemies = [Enemy() for _ in range (level+5)]
    friends = [Friend() for _ in range (int(level*0.25)+1)]
    items = [random.choice((Heal(), MaxHealthIncrease(), AttackRangeIncrease())) for _ in range(level//2+1)]
    items.append(Key())
    particleEffects = []

def newLevel():
    global gridW, gridH, cellSize, mapRect, numOpenCells
    gridW += 1
    gridH = gridW
    numOpenCells = gridW*gridH
    mapRect = 0,0,gridW*cellSize, gridH*cellSize
    newGrid()
    newEntities()

# linear interpolation between two values (smoothing)
def lerp (num1, num2, smooth=4):
    num1 += (num2 - num1) / smooth
    if abs(num1) < 0.05:
        num1 = 0
    return num1

def coordFormat(x,y, toGrid=True): # pixel pos to grid pos and vice versa
    if toGrid:
        return x/cellSize, y/cellSize
    else:
        return x*cellSize, y*cellSize

# returns true if a rect is inside another
# for culling out objects, not drawing them and improve performance
def cull (rect, areaRect):
    rX, rY, rW, rH = rect
    aX, aY, aW, aH = areaRect
    if aX-rW <= rX <= aX+aW and aY-rH <= rY <= rY+aH:
        return True
    return False

def start(): # when you hit play button
    global STATE,player
    STATE = 0
    player.health = 100
    player.maxHealth = 100
    player.dX, player.dY = 0,0

def returnToMenu():
    global STATE
    STATE = 1

def rotateTowards(objectPos, targetPos): # returns angle required to be pointed at an object
    oX, oY = objectPos
    tX, tY = targetPos
    
    if oY-tY != 0:
        rot = math.degrees(math.atan((oX-tX) / (oY-tY)))-90
        if oY-tY > 0:
            rot += 180
        return rot
    return 0

def getHighScore():
    highScore = int(open(highScoreFile, "r").read())
    return highScore

def setHighScore (score):
    file = open(highScoreFile, "w")
    file.write(str(score))
    file.close()
    highScoreText.update("High score: %d" % score)

newGrid()
player = Player()
cam = Camera(player)
newEntities()

# HUD
healthBar = Rect(0,SCREEN_H-5,SCREEN_W,5) # for now
maxHealthBar = Rect(0,SCREEN_H-5,SCREEN_W,5)
healthText = SimpleText((0,SCREEN_H-30,10,100), "Health", 16, colour=GREEN)
scoreText = SimpleText((0,0,100,100), "Score, Level", 18, WHITE)

# TITLE MENU
titleImage = Image((200,100,400,200), titleSprite)
menuPlayButton = Button((200,400,400,100), start, DULLGREEN, DARKDULLGREEN)
menuPlayText = SimpleText((290,430,100,100), "Play [SPACE]", 32, WHITE)
titleEyes = [TitleEye((330,230)), TitleEye((430,230))]
highScoreText = SimpleText((200,300,100,35), "High score: %d" % getHighScore(), 20, WHITE)

# DEATH SCREEN
deathText = SimpleText((200,200,400,100), "You woke up...", 48, RED)
returnToMenuButton = Button((200,400,400,100), returnToMenu, DULLGREEN, DARKDULLGREEN)
returnToMenuText = SimpleText((270,430,100,100), "Return [SPACE]", 32, WHITE)

run = True
while run:
    if STATE == 0: # GAME
        screen.fill(BLACK)
        drawAllTiles()
        
        door.checkAccess()
        door.draw()
        
        for item in items: # seperate loops to prevent flashing
            item.checkPickup()
        for item in items:
            item.draw()
        
        for enemy in enemies:
            enemy.chase()
            enemy.update()
            enemy.draw()
        
        for friend in friends:
            friend.update()
            if friend.pickedUp:
                friend.follow()
            else:
                friend.checkPickup()
            friend.draw()
        
        for p in particleEffects:
            p.update()
            p.draw()
        
        player.update()
        player.draw()
        
        cam.update()
        
        scoreText.draw()
        healthText.draw()
        
        for e in event.get():
            if e.type == KEYDOWN:
                if e.key == K_w: # up
                    player.dY -= 1
                elif e.key == K_s: # down
                    player.dY += 1
                elif e.key == K_d: # right
                    player.dX += 1
                elif e.key == K_a: # left
                    player.dX -= 1
                    
                elif e.key == K_SPACE:
                    player.attack()
            elif e.type == KEYUP:
                if e.key == K_w: # up
                    player.dY += 1
                elif e.key == K_s: # down
                    player.dY -= 1
                elif e.key == K_d: # right
                    player.dX -= 1
                elif e.key == K_a: # left
                    player.dX += 1
            elif e.type == QUIT:
                run = False
                
    elif STATE == 1: # MENU
        mouseX, mouseY = mouse.get_pos()
        screen.fill(BLACK)
        titleImage.draw()
        menuPlayButton.draw()
        menuPlayText.draw()
        highScoreText.draw()
        
        for eye in titleEyes:
            eye.draw()
        
        for e in event.get():
            if e.type == MOUSEMOTION:
                if inRect((mouseX, mouseY), menuPlayButton.rect):
                    menuPlayButton.hovered = True
                else:
                    menuPlayButton.hovered = False
            elif e.type == KEYDOWN:
                if e.key == K_SPACE:
                    start()
            elif e.type == MOUSEBUTTONUP:
                if e.button == 1: # RMB
                    if inRect((mouseX, mouseY), menuPlayButton.rect):
                        menuPlayButton.pressed()
            elif e.type == QUIT:
                run = False
    else: # DEATH
        mouseX, mouseY = mouse.get_pos()
        deathText.draw()
        returnToMenuButton.draw()
        returnToMenuText.draw()
        
        for e in event.get():
            if e.type == MOUSEMOTION:
                if inRect((mouseX, mouseY), returnToMenuButton.rect):
                    returnToMenuButton.hovered = True
                else:
                    returnToMenuButton.hovered = False
            elif e.type == KEYDOWN:
                if e.key == K_SPACE:
                    returnToMenu()
            elif e.type == MOUSEBUTTONUP:
                if e.button == 1:
                    if inRect((mouseX, mouseY), returnToMenuButton.rect):
                        returnToMenuButton.pressed()
            if e.type == QUIT:
                run = False
        
    display.update()
    clock.tick(FRAMERATE)
quit()