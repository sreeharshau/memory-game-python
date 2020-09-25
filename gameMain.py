import pygame
import os, sys
import math
import random
import time
from playsound import playsound

from datetime import datetime

from pygame.locals import *

# Game Window Parameters
windowSizeX = 1200
windowSizeY = 900

gameTileSize = 120

boardColor = (222, 232, 250)
# tileBorderColor = (32, 65, 89) #Uncomment for navy blue border
tileBorderColor = (0, 0, 0)

cardBackImage = None

correctSoundFile = "correctTone.mp3"
wrongSoundFile = "wrongTone.mp3"


# Internal Game Variables

Window = None

gameSpritesDict = {}
gameSpritesToUse = []

singleTileClicked = False
lastTileClickedLabel = None
lastTileClickedIndex = None
lastTileChangedFlag = False


def loadImages():
    """
    Loads images from ImagePaths.cfg and preloads cardBackground.jpg
    """
    global gameSpritesDict, cardBackImage

    # Read and scale card background image to game size
    cardBackImage = pygame.image.load('cardBackground.jpg')
    cardBackImage = pygame.transform.scale(cardBackImage, (gameTileSize, gameTileSize))

    # Read Image Sprites from the paths listed in ImagePaths.cfg
    with open("ImagePaths.cfg", "r") as pathFile:
        for line in pathFile:
            # Ignore Headers
            if("Label,Path" in line):
                continue
            else:
                lineSplit = line.split(",")
                imgLabel = lineSplit[0].strip()
                imgPath = lineSplit[1].strip()

                imgObj = pygame.image.load(imgPath)
                imgObj = pygame.transform.scale(imgObj, (math.floor(0.8*gameTileSize), math.floor(0.8*gameTileSize)))

                gameSpritesDict[imgLabel] = imgObj

def randomizeSprites(numRowsCols):
    """
    Chooses a set of sprites to use for this game and randmizes their locations on the board
    """
    global gameSpritesDict, gameSpritesToUse

    totalTiles = numRowsCols * numRowsCols

    # If more sprites exist than needed for this game
    if(len(gameSpritesDict.keys()) > (totalTiles/2)):
        for spriteLabel in list(gameSpritesDict.keys())[:math.floor(totalTiles/2)]:
            spriteObj = {}
            
            spriteObj["Label"] = spriteLabel
            spriteObj["DisplayOnScreen"] = False
            spriteObj["Image"] = gameSpritesDict[spriteLabel]

            gameSpritesToUse.append(spriteObj)
            gameSpritesToUse.append(spriteObj.copy())
    # Reuse some sprites multiple times if there arent enough
    else:
        spriteLabels = list(gameSpritesDict.keys())
        numSpriteLabels = len(spriteLabels)
        for i in range(math.floor(totalTiles/2)):
            spriteObj = {}
            spriteLabel = spriteLabels[i % numSpriteLabels]
            
            spriteObj["Label"] = spriteLabel
            spriteObj["DisplayOnScreen"] = False
            spriteObj["Image"] = gameSpritesDict[spriteLabel]
            
            gameSpritesToUse.append(spriteObj)
            gameSpritesToUse.append(spriteObj.copy())

    random.seed(datetime.now())
    random.shuffle(gameSpritesToUse)    

def setupGameWindow():
    """
    Initialize basic game window parameters
    """
    global Window

    pygame.init()
    Window = pygame.display.set_mode((windowSizeX, windowSizeY))
    Window.fill(boardColor)
    pygame.display.set_caption("Memory Game")
    pygame.display.update()  

def drawGameBoard(refresh, fadeObjectIndex):
    """
    Draws the board from scratch with all visible artifacts. Fades in the object whose index
    is indicated by 'fadeObjectIndex'. If called with refresh == True, does not call randomizeSprites
    """
    global gameSpritesDict, gameSpritesToUse, Window, cardBackImage

    setupGameWindow()

    # Calculate max possible number of rows and cols
    numCols = math.floor(windowSizeX / gameTileSize)
    numRows = math.floor(windowSizeY / gameTileSize)

    # Use the minimum of both and also turn it into an even number
    minRowsCols = min(numRows, numCols)
    if(minRowsCols % 2 != 0):
        minRowsCols = minRowsCols - 1

    numRows = minRowsCols
    numCols = minRowsCols

    # Calculate margins
    xMargin = math.floor((windowSizeX - (numCols * gameTileSize))/2)
    yMargin = math.floor((windowSizeY - (numRows * gameTileSize))/2)

    # Call randomizeSprites if refresh is False i.e. the first time this is called
    if(refresh == False):
        randomizeSprites(minRowsCols)

    tilesDrawn = 0
    fadeX = None
    fadeY = None
   
    for col in range(0, numCols):
        for row in range(0, numRows):
            # Position of current rectangle for this sprite
            xPos = xMargin + (col * gameTileSize)
            yPos = yMargin + (row * gameTileSize)
            
            tile = Rect(xPos, yPos, gameTileSize, gameTileSize)
            gameSpriteObj = gameSpritesToUse[tilesDrawn]
           
            # If object is visible and not the one that needs to be faded, draw it first
            if(gameSpriteObj["DisplayOnScreen"] == True):
                if(tilesDrawn != fadeObjectIndex):
                    Window.blit(gameSpriteObj["Image"], (xPos + gameTileSize/10, yPos + gameTileSize/10))
                else:
                    # Set X and Y coords for object to be faded
                    fadeX = xPos
                    fadeY = yPos
            else:
                # If object is invisible, use the cardBackground image instead
                Window.blit(cardBackImage, (xPos, yPos))
          
            gameSpriteObj["Tile"] = tile
            
            pygame.draw.rect(Window, tileBorderColor, tile, 5)
            tilesDrawn += 1
    
    if(fadeObjectIndex != None):
        # Fade the sprite in slowly
        gameSpriteObj = gameSpritesToUse[fadeObjectIndex]
        for i in range (0, 225):
            gameSpriteObj["Image"].set_alpha(i)
            Window.blit(gameSpriteObj["Image"],(fadeX + gameTileSize/10,  fadeY + gameTileSize/10))
            pygame.display.flip()
            pygame.time.delay(1)

    
    pygame.display.update()

def getClickedSpriteIndex(mousePos):
    """
    Figure out which rectangle was clicked. Returns -1 if out of bounds or index of clicked object otherwise
    """
    global gameSpritesToUse

    for i in range(len(gameSpritesToUse)):
        if(gameSpritesToUse[i]["Tile"].collidepoint(mousePos)):
            return i
    
    return -1

def eventHandlerLoop():
    """
    This is the main listener loop to handle all pygame events. Checks for QUIT and MOUSEBUTTONUP.
    """
    global singleTileClicked, gameSpritesToUse, lastTileClickedIndex, lastTileClickedLabel
    while True:
        for event in pygame.event.get():
            # If a click is detected
            if(event.type == MOUSEBUTTONUP):
                correctTileFlag = False
                # Extract mouse position and figure out which rectangle was clicked
                mouseClickPos = pygame.mouse.get_pos()
                clickIndex = getClickedSpriteIndex(mouseClickPos)
                
                # If its a valid click and not a click of the same object twice
                if(clickIndex >= 0 and clickIndex != lastTileClickedIndex):
                    clickedTileLabel = gameSpritesToUse[clickIndex]["Label"]
                    # If its the first click out of 2 possible clicks to get a matching set
                    if(singleTileClicked == False):
                        if(gameSpritesToUse[clickIndex]["DisplayOnScreen"] == False):
                            gameSpritesToUse[clickIndex]["DisplayOnScreen"] = True
                            singleTileClicked = True
                            lastTileClickedLabel = clickedTileLabel
                            lastTileClickedIndex = clickIndex

                    # Second click in set
                    elif(singleTileClicked == True):
                        tileDisplayChanged = False
                        # If the object isnt already displayed, display it and set it up for potential re-hiding
                        if(gameSpritesToUse[clickIndex]["DisplayOnScreen"] == False):
                            gameSpritesToUse[clickIndex]["DisplayOnScreen"] = True
                            tileDisplayChanged = True
                        
                        # If the second sprite doesnt match the first, display it for a small time and then hide both this and previously clicked sprite
                        if(lastTileClickedLabel != clickedTileLabel):
                            drawGameBoard(True, clickIndex)    
                            # Play audio to indicate that the set wasnt a match
                            playsound(wrongSoundFile)
                            gameSpritesToUse[lastTileClickedIndex]["DisplayOnScreen"] = False
                            # Only revert back the object to hidden if it was changed to display on this click
                            if(tileDisplayChanged):
                                gameSpritesToUse[clickIndex]["DisplayOnScreen"] = False
                        else:
                            correctTileFlag = True                        

                        singleTileClicked = False
                        lastTileClickedIndex = None
                        lastTileClickedLabel = None

                    # Refresh the board in either case
                    drawGameBoard(True, lastTileClickedIndex)
                    if(correctTileFlag):
                        playsound(correctSoundFile)

            # Handle Window Close Event
            elif(event.type == QUIT):
                pygame.quit()
                sys.exit(0)


def mainFunc():
    # setupGameWindow()
    loadImages()
    drawGameBoard(False, None)
    eventHandlerLoop()
    

if(__name__ == "__main__"):
    mainFunc()
