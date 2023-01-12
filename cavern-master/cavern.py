from random import choice, randint, random, shuffle
from enum import Enum
import pygame, pgzero, pgzrun, sys, math, time

# Check Python version number. sys.version_info gives version as a tuple, e.g. if (3,7,2,'final',0) for version 3.7.2.
# Unlike many languages, Python can compare two tuples in the same way that you can compare numbers.
if sys.version_info < (3,5):
    print("This game requires at least version 3.5 of Python. Please download it from www.python.org")
    sys.exit()

# Check Pygame Zero version. This is a bit trickier because Pygame Zero only lets us get its version number as a string.
# So we have to split the string into a list, using '.' as the character to split on. We convert each element of the
# version number into an integer - but only if the string contains numbers and nothing else, because it's possible for
# a component of the version to contain letters as well as numbers (e.g. '2.0.dev0')
# We're using a Python feature called list comprehension - this is explained in the Bubble Bobble/Cavern chapter.
pgzero_version = [int(s) if s.isnumeric() else s for s in pgzero.__version__.split('.')]
if pgzero_version < [1,2]:
    print("This game requires at least version 1.2 of Pygame Zero. You have version {0}. Please upgrade using the command 'pip3 install --upgrade pgzero'".format(pgzero.__version__))
    sys.exit()

# Set up constants
WIDTH = 800
HEIGHT = 480
TITLE = "Cavern"

NUM_ROWS = 18
NUM_COLUMNS = 28

LEVEL_X_OFFSET = 50
GRID_BLOCK_SIZE = 25

ANCHOR_CENTRE = ("center", "center")
ANCHOR_CENTRE_BOTTOM = ("center", "bottom")

#make a way to get out of a loop incase the robot camps the player under them

LEVELS = [ ["XXXXX     XXXXXXXX     XXXXX",
            "","","","",
            "   XXXXXXX        XXXXXXX   ",
            "","","",
            "   XXXXXXXXXXXXXXXXXXXXXX   ",
            "","","",
            "XXXXXXXXX          XXXXXXXXX",
            "","",""],

           ["XXXX    XXXXXXXXXXXX    XXXX",
            "","","","",
            "    XXXXXXXXXXXXXXXXXXXX    ",
            "","","",
            "XXXXXX                XXXXXX",
            "      X              X      ",
            "       X            X       ",
            "        X          X        ",
            "         X        X         ",
            "","",""],

           ["XXXX    XXXX    XXXX    XXXX",
            "","","","",
            "  XXXXXXXX        XXXXXXXX  ",
            "","","",
            "XXXX      XXXXXXXX      XXXX",
            "","","",
            "    XXXXXX        XXXXXX    ",
            "","",""]]

class MoodStates(Enum):
    FARMING = 0
    KILLING = 1

class ActionStates(Enum):
    IDLE = 0
    MOVING = 1
    SHOOTING = 2
                
class PlayerStates():
    def __init__(self):
        self.moodState = MoodStates.KILLING
        self.ActionStates = ActionStates.IDLE

    def setMood(self, state):
        self.moodState = state

    def getMood(self):
        return self.moodState

    def setAction(self,action):
        self.ActionStates = action

    def getAction(self):
        return self.ActionStates

class PlayerMoodState():
    def MoodFunction(self,player,danger):
        print("mood function parent")

class PlayerActionState():
    def ActionFunction(self,player):
        print("action function parent")
        
class KillingState(PlayerMoodState):
    def MoodFunction(self,player,danger):
        global game
        pos = danger.getPos()

        dangers = len(game.getEnemies())+len(game.getBolts()) #gets the combined length of enemies and bolts
        orbs = len(game.getOrbs()) #gets the length of orbs
        
        if pos[1] <= player.pos[1] and orbs < 5 and player.fire_timer <= 0 and orbs<dangers:
        # checks if the position of the danger is on the same height or above, there are less than 5 active orbs,
        # the fire timer is smaller than 0 and that there are less orbs than dangers
            player.shot(pos) #calls shot function of player
        
        if not player.danger: #checks if the player is not in danger.
        #This is to makes sure that the following checks dont block the player in a dangerous situation, by preventing it to drop or jump away from the danger

            if player.enemyAbove:#player.pos[1] -75> pos[1] > player.pos[1] -150 : # RULE 2 #
            # this would mean an enemy or bolt is above player
               player.cantJump = True #and prevents the player from jumping into that danger
               player.moveDown()

            elif player.enemyBelow: #checks if the danger is below the player
                player.AvoidDropping(pos)
                            
        elif not player.enemyAbove and  -125<player.pos[0]-pos[0]<125 and player.danger:#and checks if the danger is close to the player, is in danger and none is above
                player.moveUp() #call the flee function:  # RULE 1 #
                player.Jump()



class FarmingState(PlayerMoodState):
    def MoodFunction(self,player,danger):
        global game
        pos = danger.getPos()
        enemyPos = (game.getEnemies()[0].getPos()) #get the last enemy's position 
        if player.danger:
            if danger.getName() == "BOLT" and not -200<player.pos[0]  - enemyPos[0] <200 and player.vel_y ==0 and player.fire_timer <= 0: 
                #checks if the danger passed in is a bolt, if its close to the player,  if the player is not moving vertically
                #and also checks if the enemy left is not close to the player, so it wont bubble it
                #checks if fire timer is smaller than 0
                player.shot(pos) #calls shot function of player, passing in the position of the bolt
            player.moveUp()
            player.Jump()
        elif player.enemyBelow:
            player.AvoidDropping(pos)
        elif player.enemyAbove:
             player.cantJump = True
             player.moveDown()
                

class MovingState(PlayerActionState):
    def ActionFunction(self,player):
        
        if -4<=player.pos[0] - player.target[0] <=4: #avoids the bug where it never reaches the target as player moves 4 each update call
            player.pos = [player.target[0],player.pos[1]] #reaches destination on the x axis
            player.targetReset()

        if player.pos[1]-50 > player.target[1] and player.enemyBelow:#else checks if the fruit is above
            if block(int(player.pos[0]),int(player.pos[1]-80)) or block(int(player.pos[0]+player.direction_x *75),int(player.pos[1]-80)):
                #checks if there is a block above the player, or if there is a block 75 pixels in the direction that its moving
                player.Jump() #and if there is calls the jump function

        if player.pos[0] > player.target[0]: #move towards the side of the targeted fruit (left)
            player.dx = -1
        elif player.pos[0] < player.target[0]: #move towards the side of the targeted fruit (right)
            player.dx = 1
            
        if player.dx != 0 and player.fire_timer<10: #checks if player hasnt recently fired a bubble and the dx is not 0
            player.direction_x = player.dx #sets the direction to be equal to the dx
            if player.move(player.dx, 0, 4) and not (player.pos[0]<75 or player.pos[0]>725):
                #calls the move function and if it returns false, it would mean the move failed as there is a block blocking the move,
                #and checks if that block is not the edges of the map.
                player.Jump() #and jumps. This is mainly for the map 2 tiles which are similar to a staircase and block the player from moving
  
    
class ShootingState(PlayerActionState):
    def ActionFunction(self,player):
        None

class IdleState(PlayerActionState):
     def ActionFunction(self,player):
         None

class RobotActionStates(Enum):
    SEARCHING = 0
    FOUND = 1

class RobotTypeStates(Enum): 
    TYPE_NORMAL = 0
    TYPE_AGGRESSIVE = 1

class RobotStates():
    def __init__(self,_type):
        self.RobotAction = RobotActionStates.SEARCHING 
        self.RobotType = _type

    def setType(self, state):
        self.RobotType = state

    def getType(self):
        return self.RobotType

    def setAction(self,action):
        self.RobotAction = action

    def getAction(self):
        return self.RobotAction

class RobotTypeState():
    def TypeFunction(self,robot):
        print("robot mood function parent")

class RobotActionState():
    def ActionFunction(self,robot):
        print("robot action function parent")

class SearchingState(RobotActionState):
    def ActionFunction(self,robot):
        if robot.target ==0 or robot.pos[0] ==robot.target: #checks if the target is equal to 0 or if the robot has reached its target,
                                                                                      #in which both cases, there needs to be a new target
            robot.MoveToSide() #and if either is true, set the target using the movetoside function
        
class FoundState(RobotActionState):
    def ActionFunction(self,robot):
        global game
        robot.target = game.player.pos[0] #when found, the robot has the player as target
        if robot.fire_timer >= robot.maxTimer: #checks if the robot fire timer is larger than or equal to thirty,
                                              #which would mean the robot can shot a bolt 
            robot.fire_timer = 0 #sets the fire timer to 0
            game.play_sound("laser", 4) #and player the laser sound

            
class NormalState(RobotTypeState):
    def TypeFunction(self,robot):
        None

class AggressiveState(RobotTypeState):
    def TypeFunction(self,robot):
        global game
        if robot.fire_timer >= 24:
            # Go through all orbs to see if any can be shot at
            for orb in game.orbs: 
                # The orb must be at our height, and within 200 pixels on the x axis
                if orb.y >= robot.top and orb.y < robot.bottom and abs(orb.x - robot.x) < 200:
                    #checks if the current orb is on the same height as the robot and is close to it 
                    robot.direction_x = sign(orb.x - robot.x) #faces the orb 
                    robot.fire_timer = 0 #and set the fire timer to 0 to fire a bolt towards it
                    break

def block(x,y):
    # Is there a level grid block at these coordinates?
    grid_x = (x - LEVEL_X_OFFSET) // GRID_BLOCK_SIZE
    grid_y = y // GRID_BLOCK_SIZE
    if grid_y > 0 and grid_y < NUM_ROWS:
        row = game.grid[grid_y]
        return grid_x >= 0 and grid_x < NUM_COLUMNS and len(row) > 0 and row[grid_x] != " "
    else:
        return False

def lineCalculator(currentPos,newPos):
    return math.sqrt(pow((currentPos[0] - newPos[0]),2)+ pow((currentPos[1] - newPos[1]),2)) #returns the distance between two given coordinates 

def sign(x):
    # Returns -1 or 1 depending on whether number is positive or negative
    return -1 if x < 0 else 1

class CollideActor(Actor):
    def __init__(self, pos, anchor=ANCHOR_CENTRE):
        super().__init__("blank", pos, anchor)
        self.pos = pos

    def getPos(self):
        return self.pos

    def getDir(self):
        return self.direction_x

    def move(self, dx, dy, speed):
        new_x, new_y = int(self.x), int(self.y)

        # Movement is done 1 pixel at a time, which ensures we don't get embedded into a wall we're moving towards
        for i in range(speed):
            new_x, new_y = new_x + dx, new_y + dy

            if new_x < 70 or new_x > 730:
                # Collided with edge of level
                return True

            # Normally you don't need brackets surrounding the condition for an if statement (unlike many other
            # languages), but in the case where the condition is split into multiple lines, using brackets removes
            # the need to use the \ symbol at the end of each line.
            # The code below checks to see if we're position we're trying to move into overlaps with a block. We only
            # need to check the direction we're actually moving in. So first, we check to see if we're moving down
            # (dy > 0). If that's the case, we then check to see if the proposed new y coordinate is a multiple of
            # GRID_BLOCK_SIZE. If it is, that means we're directly on top of a place where a block might be. If that's
            # also true, we then check to see if there is actually a block at the given position. If there's a block
            # there, we return True and don't update the object to the new position.
            # For movement to the right, it's the same except we check to ensure that the new x coordinate is a multiple
            # of GRID_BLOCK_SIZE. For moving left, we check to see if the new x coordinate is the last (right-most)
            # pixel of a grid block.
            # Note that we don't check for collisions when the player is moving up.
            if ((dy > 0 and new_y % GRID_BLOCK_SIZE == 0 or
                 dx > 0 and new_x % GRID_BLOCK_SIZE == 0 or
                 dx < 0 and new_x % GRID_BLOCK_SIZE == GRID_BLOCK_SIZE-1)
                and block(new_x, new_y)):
                    return True

            # We only update the object's position if there wasn't a block there.
            self.pos = new_x, new_y

        # Didn't collide with block or edge of level
        return False

class Orb(CollideActor):
    MAX_TIMER = 250

    def __init__(self, pos, dir_x):
        super().__init__(pos)

        # Orbs are initially blown horizontally, then start floating upwards
        self.direction_x = dir_x
        self.floating = False
        self.trapped_enemy_type = None      # Number representing which type of enemy is trapped in this bubble
        self.timer = -1
        self.blown_frames = 6  # Number of frames during which we will be pushed horizontally

    def hit_test(self, bolt):
        # Check for collision with a bolt
        collided = self.collidepoint(bolt.pos)
        if collided:
            self.timer = Orb.MAX_TIMER - 1
        return collided

    def update(self):
        self.timer += 1

        if self.floating:
            # Float upwards
            self.move(0, -1, randint(1, 2))
        else:
            # Move horizontally
            if self.move(self.direction_x, 0, 4):
                # If we hit a block, start floating
                self.floating = True

        if self.timer >= self.blown_frames and not self.floating:
            self.floating = True
        elif self.timer >= Orb.MAX_TIMER or self.y <= -40:
            # Pop if our lifetime has run out or if we have gone off the top of the screen
            game.pops.append(Pop(self.pos, 1))
            if self.trapped_enemy_type != None:
                # trapped_enemy_type is either zero or one. A value of one means there's a chance of creating a
                # powerup such as an extra life or extra health
               
                game.fruits.append(Fruit(self.pos, self.trapped_enemy_type))
            game.play_sound("pop", 4)

        if self.timer < 9:
            # Orb grows to full size over the course of 9 frames - the animation frame updating every 3 frames
            self.image = "orb" + str(self.timer // 3)
        else:
            if self.trapped_enemy_type != None:
                self.image = "trap" + str(self.trapped_enemy_type) + str((self.timer // 4) % 8)
            else:
                self.image = "orb" + str(3 + (((self.timer - 9) // 8) % 4))

class Bolt(CollideActor):
    SPEED = 7

    def __init__(self, pos, dir_x):
        super().__init__(pos)
        self.pos = pos
        self.direction_x = dir_x
        self.active = True
        self.name = "BOLT"

    def getName(self):
        return self.name
    
    def update(self):
        # Move horizontally and check to see if we've collided with a block
        if self.move(self.direction_x, 0, Bolt.SPEED):
            # Collided
            self.active = False
        else:
            # We didn't collide with a block - check to see if we collided with an orb or the player
            for obj in game.orbs + [game.player]:
                if obj and obj.hit_test(self):
                    self.active = False
                    break

        direction_idx = "1" if self.direction_x > 0 else "0"
        anim_frame = str((game.timer // 4) % 2)
        self.image = "bolt" + direction_idx + anim_frame

class Pop(Actor):
    def __init__(self, pos, type):
        super().__init__("blank", pos)

        self.type = type
        self.timer = -1

    def update(self):
        self.timer += 1
        self.image = "pop" + str(self.type) + str(self.timer // 2)

class GravityActor(CollideActor):
    MAX_FALL_SPEED = 10

    def __init__(self, pos):
        super().__init__(pos, ANCHOR_CENTRE_BOTTOM)

        self.vel_y = 0
        self.landed = False

    def update(self, detect=True):
        # Apply gravity, without going over the maximum fall speed
        self.vel_y = min(self.vel_y + 1, GravityActor.MAX_FALL_SPEED)

        # The detect parameter indicates whether we should check for collisions with blocks as we fall. Normally we
        # want this to be the case - hence why this parameter is optional, and is True by default. If the player is
        # in the process of losing a life, however, we want them to just fall out of the level, so False is passed
        # in this case.
        if detect:
            # Move vertically in the appropriate direction, at the appropriate speed
            if self.move(0, sign(self.vel_y), abs(self.vel_y)):
                # If move returned True, we must have landed on a block.
                # Note that move doesn't apply any collision detection when the player is moving up - only down
                self.vel_y = 0
                self.landed = True

            if self.top >= HEIGHT:
                # Fallen off bottom - reappear at top
                self.y = 1
        else:
            # Collision detection disabled - just update the Y coordinate without any further checks
            self.y += self.vel_y

# Class for pickups including fruit, extra health and extra life
class Fruit(GravityActor):
    APPLE = 0
    RASPBERRY = 1
    LEMON = 2
    EXTRA_HEALTH = 3
    EXTRA_LIFE = 4

    def __init__(self, pos, trapped_enemy_type=0):
        super().__init__(pos)
        self.pos = pos
        # Choose which type of fruit we're going to be.
        if trapped_enemy_type == RobotTypeStates.TYPE_NORMAL.value:
            self.type = choice([Fruit.APPLE, Fruit.RASPBERRY, Fruit.LEMON])
        else:
            # If trapped_enemy_type is 1, it means this fruit came from bursting an orb containing the more dangerous type
            # of enemy. In this case there is a chance of getting an extra help or extra life power up
            # We create a list containing the possible types of fruit, in proportions based on the probability we want
            # each type of fruit to be chosen
            types = 10 * [Fruit.APPLE, Fruit.RASPBERRY, Fruit.LEMON]    # Each of these appear in the list 10 times
            types += 9 * [Fruit.EXTRA_HEALTH]                           # This appears 9 times
            types += [Fruit.EXTRA_LIFE]                                 # This only appears once
            self.type = choice(types)                                   # Randomly choose one from the list

        self.time_to_live = 500 # Counts down to zero

    def getType(self):
        return self.type
    
    def update(self):
        super().update()
        # Does the player exist, and are they colliding with us?
        if game.player and game.player.collidepoint(self.center):
           # game.player.targetReset()
            if self.type == Fruit.EXTRA_HEALTH:
                game.player.health = min(3, game.player.health + 1)
                game.play_sound("bonus")
            elif self.type == Fruit.EXTRA_LIFE:
                game.player.lives += 1
                game.play_sound("bonus")
            else:
                game.player.score += (self.type + 1) * 100
                game.play_sound("score")

            self.time_to_live = 0   # Disappear
        else:
            self.time_to_live -= 1

        if self.time_to_live <= 0:
            # Create 'pop' animation
            game.fruits.remove(self)
            game.pops.append(Pop((self.x, self.y - 27), 0))
            #game.player.targetReset()

        anim_frame = str([0, 1, 2, 1][(game.timer // 6) % 4])
        self.image = "fruit" + str(self.type) + anim_frame

class Player(GravityActor,PlayerStates):
    def __init__(self):
        # Call constructor of parent class. Initial pos is 0,0 but reset is always called straight afterwards which
        # will set the actual starting position.
        GravityActor.__init__(self,(0, 0)) 
        PlayerStates.__init__(self)
        self.target = [0,0] #a list which will store the location which the player will be heading towards. Initially set to 0,0 but will immediately
        self.fleePos = [0,0] #a list that will hold the flee position that the flee function will generate. 
        self.dx=0 #an integer variable that will store the direction the player will be heading towards, with 1 being right and -1 being left
        self.disTarget = 9999 #an integer variable that stores the distance between the player and the target that is heading towards
        self.lives = 2 #an integer variable that stores the number of lives the player has
        self.score = 0 #an integer variable that stores the score the player has
        self.sidePos = 0 # variable that stores the position which the previous side call was made which will be used to prevent looping between pos and side
        self.higherSide = False # a boolean variable that indicates that the player will be moving to a side and that the target is above them but cant reach it
        self.lowerSide = False # a boolean variable that indicates that the player will be moving to a side and that the target is beneath but cant reach it
        self.enemyAbove = False
        self.enemyBelow = False
        self.cantJump = False # a boolean variable which prevents the player from jumping when there is an enemy above
        self.danger = False #a boolean variable that is true if the player is in danger, meaning there is an enemy or bolt on the same height as it
        self.availableMoodStates = [] #creates an empty list that will hold all available mood states of the player
        self.availableActionStates = [] #creates an empty list that will hold all available action states of the player 
        self.availableMoodStates= (FarmingState() , KillingState()) #populates the list with the mood behaviour classes
        self.availableActionStates =(IdleState(),MovingState(),ShootingState()) #populates the list with the action behaviour classes
   
        
    def reset(self):
        self.pos = [WIDTH / 2, 100]
        self.vel_y = 0
        self.direction_x = 1            # -1 = left, 1 = right
        self.fire_timer = 0
        self.hurt_timer = 100   # Invulnerable for this many frames
        self.health = 3
        self.blowing_orb = None
        

    def targetReset(self):
        self.target =self.fleePos=[0,0]
        self.disTarget = 9999
        self.lowerSide = False
        self.higherSide = False
        self.enemyAbove = False
        self.enemyBelow = False

    def moveDown(self):
        found = False
        right =True
        left = True
        for i in range (1,NUM_COLUMNS):
            if right:
                if self.pos[0]+i*GRID_BLOCK_SIZE>730:
                    right = False
                elif not block(int(self.pos[0]+i*GRID_BLOCK_SIZE),int(self.pos[1]+5)): #checks if there is no block on the right side
                    if self.pos[1]+100 >400:
                        i=i+2
                    self.fleePos=list((self.pos[0]+i*GRID_BLOCK_SIZE+1,self.pos[1]+100)) #if there is not, set the fleepos variable to point under that position
                    found = True #set found to true
            elif left:
                if self.pos[0]-i*GRID_BLOCK_SIZE<70:
                    left = False
                elif not block(int(self.pos[0]-i*GRID_BLOCK_SIZE),int(self.pos[1]+5)): #checks if there is no block on the left  side
                    if self.pos[1]+100>400:
                        i=i+2
                    self.fleePos=list((self.pos[0]-i*GRID_BLOCK_SIZE+1,self.pos[1]+100)) #if there is not, set the fleepos variable to point under that position
                    found = True #set found to true
            
            if found: 
                if self.fleePos[1] ==424:
                     i=i+2
                self.target =self.fleePos #set the target to be equal to the flee pos

                return True #and return true, as a position was found
        print("notfound")
        return False

    def moveUp(self):
        found = False
        right =True
        left = True
        for i in range (1,NUM_COLUMNS):
            if right:
                if self.pos[0]+i*GRID_BLOCK_SIZE>730:
                    right = False
                elif block(int(self.pos[0]+i*GRID_BLOCK_SIZE),int(self.pos[1]-80)): #checks if there is a block above the player to the right side
                    self.fleePos =list((self.pos[0]+(i+1)*GRID_BLOCK_SIZE,self.pos[1]-100)) #if there is, set the fleepos variable to be point above that block
                    found = True #set found to true
                    
            elif left:
                if self.pos[0]-i*GRID_BLOCK_SIZE<70:
                    left = False
                elif block(int(self.pos[0]-i*GRID_BLOCK_SIZE),int(self.pos[1]-80)): #checks if there is a block above the player to the left side
                    self.fleePos =list((self.pos[0]-(i+1)*GRID_BLOCK_SIZE,self.pos[1]-100)) #if there is, set the fleepos variable to be point above that block
                    found = True #set found to true
                
            if found and self.fleePos[1]>50: #in case found is true and the flee position is bigger than 50, which would mean the position found is not above the map
                if self.fleePos[0]>680: #checks if the flee pos's x is not outside the map limits
                    self.fleePos[0] = 680 #if it is, set it to map limit instead
                elif self.fleePos[0]<120: 
                    self.fleePos[0] = 120
                self.target =self.fleePos #set the target to be equal to the flee pos
                return True #and return true, as a position was found 
            else: #if the flee pos is above the map
                found = False #set found to false, so it keeps looking for a new position
                
        self.fleePos = [0,0] #if the function went through all options and found none, reset the flee pos to 0,0 
        return False #and return false, as no position was found

    def AvoidDropping(self,pos):
         if self.pos[1] +20< pos[1]<self.pos[1] +125 or (self.pos[1] +120< pos[1]<self.pos[1] +225 and not block(int(self.pos[0]+(30 *self.direction_x)),int(self.pos[1]+105))):  # RULE 3 #
            # checks if the danger is on the platform below the player, or if its two platforms below and there isnt a block on the platform below the player
            # if the above is true, the player needs to not drop from the platform it is on
            # so it checks if the player is on a platform and is not midair
            #and if there is no block in front of it.

            if not block(int(self.pos[0]+(30 *self.direction_x)),int(self.pos[1]+5)) and block(int(self.pos[0]),int(self.pos[1]+1)) and self.vel_y ==0 and self.fleePos ==[0,0]:
                #in case  that the above is true, the player need to change direction from where its moving to avoid dropping
                self.targetReset() #so reset the target so it can be overriden with a new target
                self.lowerSide = True #setting the lower side to true, so it can generate a new target below and not override it in the fruit search

                if self.direction_x >0: #checks the direction the player is heading, and send them the other way. 
                    self.target=[120,self.pos[1]]
                    self.direction_x=1
                else:
                    self.target = [680, self.pos[1]]
                    self.direction_x=-1

    def checkDanger(self,danger): #checks if the danger passed it is on the same height as the player and sets the danger to true
        global game
        pos = danger.getPos()

        if self.top<pos[1]<=self.bottom: #and -200<pos[0]-self.pos[0]<200: #checks if the danger is on the same height as the player and close to it on the x axis
            self.danger =True #set the danger to true
            
        else:
            posDif = self.pos[1] - pos[1]
            if posDif <0: #danger lower than player
                if posDif >= -100 or (posDif>=-200 and not block(int(self.pos[0]+30*self.direction_x),int(self.pos[1]-5))): #robot on the platform below player
                    self.enemyBelow= True
                elif posDif < -275: #robot is on the last platform while player is on the top platform, so the robot will be dropping on it
                    self.moveDown()
                    self.enemyAbove =True

            else: #danger above player
                if posDif>299: #the enemy is on the top of the map and the player is on the bottom, so dropping will put the player with the robot
                    self.enemyBelow= True

                elif posDif<=200:
                    self.enemyAbove =True
                      
     
    def shot(self,posx):
      # x position will be 38 pixels in front of the player position, while ensuring it is within the
      # bounds of the level
      #posx is the danger's position
        if self.pos[0]>posx[0]: #checks where the danger is located at and sets the direction of the player to face the danger
            self.direction_x = -1
        else: 
            self.direction_x = +1
        self.setAction(ActionStates.SHOOTING) #sets the state to shooting
        
        x = min(730, max(70, self.x + self.direction_x  * 38)) 
        y = self.y - 35
        self.blowing_orb = Orb((x,y), self.direction_x ) 
        game.orbs.append(self.blowing_orb)
        game.play_sound("blow", 4)
        self.fire_timer = 20
        btime = abs(abs(posx[0])-abs(self.pos[0]))/4 #calculates the btime variable using the position between the player and the danger, dividing it by 4
                                                                          #( the number came up through lots of play testing and its an approximation)
        if btime>120: #checks if the btime is over 120
            btime=120 #and sets it to 120 instead
        self.blowing_orb.blown_frames = btime
        self.blowing_orb = None

    def hit_test(self, other):
        # Check for collision between player and bolt - called from Bolt.update. Also check hurt_timer - after being hurt,
        # there is a period during which the player cannot be hurt again
        if self.collidepoint(other.pos) and self.hurt_timer < 0:
            # Player loses 1 health, is knocked in the direction the bolt had been moving, and can't be hurt again
            # for a while
            self.hurt_timer = 200
            self.health -= 1
            f = open("hit positions.txt","a") 
            f.write(str(game.player.target))
            f.write('\n')
            f.close()
            self.vel_y = -12
            self.landed = False
            self.direction_x = other.direction_x
            if self.health > 0:
                game.play_sound("ouch", 4)
            else:
                game.play_sound("die")
            return True
        else:
            return False

    def Jump(self):
        if not self.cantJump: #checks if the cant jump variable is not true
            global game
            bolts = game.getBolts()
            boltAbove = False
            for b in bolts:
                pos =  b.getPos()
                if  self.pos[1] -75 > pos[1]>self.pos[1] -150 and -125<self.pos[0]-pos[0]<125:
                    boltAbove= True
            if self.vel_y == 0 and self.landed and not boltAbove: #checks if the player is not moving on the y axis and if its landed
                self.vel_y = -16 
                self.landed = False
                game.play_sound("jump")

##    def moveToAside(self): # a function that sets the x of target to a side of the map
##        global WIDTH
##
##        if self.sidePos == self.pos[0]: #checks if the side pos is equal to the position,
##            #which would mean that the player has looped and returned to the position that was before and called the function again.
##            if self.sidePos< WIDTH/2: #so send the player to the opposite direciton instead to break the loop. 
##                return WIDTH - 120 
##            return 120
##        
##        elif self.pos[0]< WIDTH/2: #else, send the player to the side that is closer to them
##            self.sidePos = self.pos[0]
##            return 120
##        self.sidePos = self.pos[0]
##        return WIDTH - 120

    def findPickup(self):
        fruits = game.getFruits()
        #if self.higherSide and self.pos[1]<self.sidePos:
        # stops the player from keep moving to the side of the map in case it  has climbed to the height of the pickup that is targeting
          #  self.targetReset()
            
        for f in fruits: #loops through all pickups
            tempPos = f.getPos() #gets their position
            if f.getType()>2: #gets the type of the fruit and if its more than two, which would mean that its either an extra health/life
                tempDis =0 #sets the tempdis to 0, so its chosen as the target
            else: #otherwise
                tempDis = lineCalculator(self.pos,tempPos) #generates the distance between player and that pickup

            if not (self.enemyAbove and self.danger):
                if (self.top<=tempPos[1]<=self.bottom) or (self.enemyBelow and self.pos[1]-100<tempPos[1]<self.top): #and self.top<=tempPos[1]<=self.bottom:
                    #checks if the lowerside is true and if the fruit is below the player, and if both are true, prevent the assignment of this fruit.
                    #also checks if the safe spot is not 0,0, which would mean the player is fleeing from a danger, so dont override the target
                    
                    if (tempDis < self.disTarget and not (self.target[0] == 680 or self.target[0] ==120) and self.vel_y == 0 and
                        not ((0<tempPos[0]<180 or tempPos[0]>570) and tempPos[1]==424 and game.getLevel() % 3==0)):
                        #checks if the distance of the current fruit being checks if lower than the current distance.
                        #In addition, checks if the fruit is in the corner of the first map, which can't be collected and is ignored
                        found = True
                        self.disTarget = tempDis #sets the distance of the target to the distance between the player and the current pickup       
                        self.target = list(tempPos) #and sets the target to the position of the current pickup

                    
            elif not self.enemyBelow: #and self.bottom<tempPos[1]<=self.bottom+100:
                self.moveDown()

            

    def update(self):
        # Call GravityActor.update - parameter is whether we want to perform collision detection as we fall. If health
        # is zero, we want the player to just fall out of the level
        super().update(self.health > 0)
        self.dx =0
        self.fire_timer -= 1
        self.hurt_timer -= 1
        
        if self.landed:
            # Hurt timer starts at 200, but drops to 100 once the player has landed
            self.hurt_timer = min(self.hurt_timer, 100)

        if self.hurt_timer > 100:
            # We've just been hurt. Either carry out the sideways motion from being knocked by a bolt, or if health is
            # zero, we're dropping out of the level, so check for our sprite reaching a certain Y coordinate before
            # reducing our lives count and responding the player. We check for the Y coordinate being the screen height
            # plus 50%, rather than simply the screen height, because the former effectively gives us a short delay
            # before the player respawns.
            if self.health > 0:
                self.move(self.direction_x, 0, 4)
            else:
                if self.top >= HEIGHT*1.5:
                    self.lives -= 1
                    self.reset()
        else:
            # We're not hurt
            global game
            dx = 0
            enemies = []
            bolts = []

            #gets the lists for  enemeis and bolts
            enemies = game.getEnemies()
            bolts = game.getBolts()

            if self.vel_y ==0:
                self.findPickup()

            if len(game.enemies) == 1 :
            #checks if there is exactly one enemy on screen(not considering the ones that might be getting spawned after, as a normal player wouldn't have access to that)
                self.setMood(MoodStates.FARMING)
            else:
                self.setMood(MoodStates.KILLING)

            if self.target == [0,0] and not self.danger:#if the player is not in danger, and that the target is 0,0 which means there isnt any available fruit to go get  
                 self.setAction(ActionStates.IDLE)
                 self.direction_x =0
            else:
                self.setAction(ActionStates.MOVING)
                
        
            self.cantJump = self.danger = self.enemyAbove = self.enemyBelow = False
            for e in enemies: #loops through the enemies 
                self.checkDanger(e) #and calls the check tanger function, passing in their possition
            for b in bolts: #same as above but for bolts
                self.checkDanger(b)
                
            for e in enemies: #loops through the enemies
                 self.availableMoodStates[self.getMood().value].MoodFunction(self,e) #calls the mood function of the current mood, passing in it self and the danger that is facing
            for b in bolts: #same as above but for bolts
                 self.availableMoodStates[self.getMood().value].MoodFunction(self,b) #calls the mood function of the current mood, passing in it self and the danger that is facing

            self.availableActionStates[self.getAction().value].ActionFunction(self)
            
        # Set sprite image. If we're currently hurt, the sprite will flash on and off on alternate frames.
        self.image = "blank"
        if self.hurt_timer <= 0 or self.hurt_timer % 2 == 1:
            dir_index = "1" if self.direction_x > 0 else "0"
            if self.hurt_timer > 100:
                if self.health > 0:
                    self.image = "recoil" + dir_index
                else:
                    self.image = "fall" + str((game.timer // 4) % 2)
            elif self.fire_timer > 0:
                self.image = "blow" + dir_index
            elif self.dx == 0:
                self.image = "still"
            else:
                self.image = "run" + dir_index + str((game.timer // 8) % 4)

class Robot(GravityActor,RobotStates):
    def __init__(self, pos, _type):
         #calls the constructors/init functions of the super class and the robotStates class
        super().__init__(pos)
        RobotStates.__init__(self,_type)
        self.change_dir_timer = 0
        self.target = 0 #an integer variable that is the target the robot will move towards on the x axis
        self.maxSpeed=4 #an integer variable that is the max speed a robot can have
        self.pos = pos #an integer variable that stores the position of the robot
        self.speed = randint(1 , 2 + game.getLevel()) #an integer variable that stores the speed of the robot,
        #the speed is set to a random number between 1 and 2 plus the game level
        if self.speed>self.maxSpeed: #checks if the speed if over the max speed 
            self.speed = self.maxSpeed #sets the speed to the max allowed speed
        self.direction_x = 1 #the direction that the robot will be facing on the x axis
        self.alive = True #a boolean variable which is true if the robot is alive
        self.name = "ROBOT" #a string variable that has the name of the robot
        self.availableTypeStates = [] #create two empty lists for each FSM
        self.availableActionStates = []
        self.availableTypeStates = (NormalState(),AggressiveState()) #populate the lists with the appropriate behaviour classes
        self.availableActionStates = (SearchingState(),FoundState())
        self.fire_timer = 0 #a integer variable that controls the time between each shot to avoid spamming
        self.maxTimer =30

    def getDir(self): #getter function for direction
        return self.direction_x

    def getName(self): #getter function for name
        return self.name

    def resetTarget(self): #resets the target to 0
        self.target = [0,0]
        
    def MoveToSide(self): #randomly selects a side of the map and returns it
        i =randint(0,2)
        if i ==1 and not self.target ==70:
            self.target =  70
        else:
            self.target =  WIDTH - 70
    
    def update(self):
        super().update()
        global game
        self.fire_timer += 1
        self.change_dir_timer -= 1 

        if self.change_dir_timer <= 0:
            # Randomly choose a direction to move in
            # If there's a player, there's a two thirds chance that we'll move towards them
            self.MoveToSide()
            self.change_dir_timer = randint(100, 250)
            
        if not self.speed == self.maxSpeed: 
            if len(game.getPendingEnemies())==0 and len(game.getEnemies())==1: #makes farming tactics more challenging to pull off #enabling god mode
                self.speed = self.maxSpeed #by setting the speed to the max allowed speed
                self.maxTimer = 5 

        if -4<=self.pos[0] - self.target <=4: #avoids the bug where it never reaches the target
            self.pos = [self.target,self.pos[1]] #reaches destination on the x axis
            self.direction_x = self.direction_x *-1
            
        #call the type function of the type state 
        self.availableTypeStates[self.getType()].TypeFunction(self)
    
        # Check to see if we can fire at player
        #checks if player exist,  if the player is on the same height as the robot and if the velocity of y is 0 
        if game.player and self.top < game.player.bottom and self.bottom > game.player.top and self.vel_y ==0:
            #if above is true, the robot has found the player and sets the action state to found
            self.setAction(RobotActionStates.FOUND)
        else:
            self.setAction(RobotActionStates.SEARCHING)

        #call the action function of the current action state
        self.availableActionStates[self.getAction().value].ActionFunction(self)

        if self.pos[0]>self.target: #checks where the target is and switches the direction of the robot to face the target
            self.direction_x =-1
        else:
            self.direction_x =1

        if self.fire_timer == 8:
            #  Once the fire timer has been set to 0, it will count up - frame 8 of the animation is when the actual bolt is fired
            game.bolts.append(Bolt((self.x + self.direction_x * 20, self.y - 38), self.direction_x))
            
        # Move in current direction - turn around if we hit a wall
        self.move(self.direction_x, 0, self.speed)


        # Am I colliding with an orb? If so, become trapped by it
        for orb in game.orbs:
            if orb.trapped_enemy_type == None and self.collidepoint(orb.center):
                self.alive = False
                orb.floating = True
                orb.trapped_enemy_type = self.getType()
                game.play_sound("trap", 4)
                game.enemies.remove(self)
                break

        # Choose and set sprite image
        direction_idx = "1" if self.direction_x > 0 else "0"
        image = "robot" + str(self.getType()) + direction_idx
        if self.fire_timer < 12:
            image += str(5 + (self.fire_timer // 4))
        else:
            image += str(1 + ((game.timer // 4) % 4))
        self.image = image


class Game:
    def __init__(self, player=None):
        self.player = player
        self.level_colour = -1
        self.level = -1

        self.next_level()

    def fire_probability(self):
        # Likelihood per frame of each robot firing a bolt - they fire more often on higher levels
        return 0.001 + (0.0001 * min(100, self.level))

    def max_enemies(self):
        # Maximum number of enemies on-screen at once – increases as you progress through the levels
        return min((self.level + 6) // 2, 8)

    def next_level(self):
        self.level_colour = (self.level_colour + 1) % 4
        self.level += 1

        # Set up grid
        self.grid = LEVELS[self.level % len(LEVELS)]

        # The last row is a copy of the first row
        # Note that we don't do 'self.grid.append(self.grid[0])'. That would alter the original data in the LEVELS list
        # Instead, what this line does is create a brand new list, which is distinct from the list in LEVELS, and
        # consists of the level data plus the first row of the level. It's also interesting to note that you can't
        # do 'self.grid += [self.grid[0]]', because that's equivalent to using append.
        # As an alternative, we could have copied the list on the line below '# Set up grid', by writing
        # 'self.grid = list(LEVELS...', then used append or += on the line below.
        self.grid = self.grid + [self.grid[0]]

        self.timer = -1

        if self.player:
            self.player.reset()

        self.fruits = []
        self.bolts = []
        self.enemies = []
        self.pops = []
        self.orbs = []

        # At the start of each level we create a list of pending enemies - enemies to be created as the level plays out.
        # When this list is empty, we have no more enemies left to create, and the level will end once we have destroyed
        # all enemies currently on-screen. Each element of the list will be either 0 or 1, where 0 corresponds to
        # a standard enemy, and 1 is a more powerful enemy.
        # First we work out how many total enemies and how many of each type to create
        num_enemies = 10 + self.level
        num_strong_enemies = 1 + int(self.level / 1.5)
        num_weak_enemies = num_enemies - num_strong_enemies

        # Then we create the list of pending enemies, using Python's ability to create a list by multiplying a list
        # by a number, and by adding two lists together. The resulting list will consist of a series of copies of
        # the number 1 (the number depending on the value of num_strong_enemies), followed by a series of copies of
        # the number zero, based on num_weak_enemies.

        self.pending_enemies = num_strong_enemies * [RobotTypeStates.TYPE_AGGRESSIVE.value] + num_weak_enemies * [RobotTypeStates.TYPE_NORMAL.value]

        # Finally we shuffle the list so that the order is randomised (using Python's random.shuffle function)
        shuffle(self.pending_enemies)

        self.play_sound("level", 1)

    def getEnemies(self):
        return self.enemies

    def getBolts(self):
        return self.bolts

    def getFruits(self):
        return self.fruits

    def getLevel(self):
        return self.level

    def getOrbs(self):
        return self.orbs

    def getPendingEnemies(self):
        return self.pending_enemies

    def get_robot_spawn_x(self):
        # Find a spawn location for a robot, by checking the top row of the grid for empty spots
        # Start by choosing a random grid column
        r = randint(0, NUM_COLUMNS-1)

        for i in range(NUM_COLUMNS):
            # Keep looking at successive columns (wrapping round if we go off the right-hand side) until
            # we find one where the top grid column is unoccupied
            grid_x = (r+i) % NUM_COLUMNS
            if self.grid[0][grid_x] == ' ':
                return GRID_BLOCK_SIZE * grid_x + LEVEL_X_OFFSET + 12

        # If we failed to find an opening in the top grid row (shouldn't ever happen), just spawn the enemy
        # in the centre of the screen
        return WIDTH/2

    def update(self):
        self.timer += 1

        # Update all objects
        for obj in self.fruits + self.bolts + self.enemies + self.pops + [self.player] + self.orbs:
            if obj:
                obj.update()

        # Use list comprehensions to remove objects which are no longer wanted from the lists. For example, we recreate
        # self.fruits such that it contains all existing fruits except those whose time_to_live counter has reached zero
        self.fruits = [f for f in self.fruits if f.time_to_live > 0]
        self.bolts = [b for b in self.bolts if b.active]
        self.enemies = [e for e in self.enemies if e.alive]
        self.pops = [p for p in self.pops if p.timer < 12]
        self.orbs = [o for o in self.orbs if o.timer < 250 and o.y > -40]

        # Every 100 frames, create a random fruit (unless there are no remaining enemies on this level)
        if self.timer % 100 == 0 and len(self.pending_enemies + self.enemies) > 0:
            # Create fruit at random position
            self.fruits.append(Fruit((randint(70, 730), randint(75, 400))))

        # Every 81 frames, if there is at least 1 pending enemy, and the number of active enemies is below the current
        # level's maximum enemies, create a robot
        if self.timer % 81 == 0 and len(self.pending_enemies) > 0 and len(self.enemies) < self.max_enemies():
            # Retrieve and remove the last element from the pending enemies list
            robot_type = self.pending_enemies.pop()
            pos = (self.get_robot_spawn_x(), -30)
            self.enemies.append(Robot(pos, robot_type))

        # End level if there are no enemies remaining to be created, no existing enemies, no fruit, no popping orbs,
        # and no orbs containing trapped enemies. (We don't want to include orbs which don't contain trapped enemies,
        # as the level would never end if the player kept firing new orbs)
        if len(self.pending_enemies + self.fruits + self.enemies + self.pops) == 0:
            if len([orb for orb in self.orbs if orb.trapped_enemy_type != None]) == 0:
                self.next_level()

    def draw(self):
        # Draw appropriate background for this level
        screen.blit("bg%d" % self.level_colour, (0, 0))

        block_sprite = "block" + str(self.level % 4)

        # Display blocks
        for row_y in range(NUM_ROWS):
            row = self.grid[row_y]

            if len(row) > 0:
                # Initial offset - large blocks at edge of level are 50 pixels wide
                x = LEVEL_X_OFFSET
                for block in row:
                    if block != ' ':
                        screen.blit(block_sprite, (x, row_y * GRID_BLOCK_SIZE))
                    x += GRID_BLOCK_SIZE

        # Draw all objects
        all_objs = self.fruits + self.bolts + self.enemies + self.pops + self.orbs
        all_objs.append(self.player)
        for obj in all_objs:
            if obj:
                obj.draw()

    def play_sound(self, name, count=1):
        # Some sounds have multiple varieties. If count > 1, we'll randomly choose one from those
        # We don't play any sounds if there is no player (e.g. if we're on the menu)
        if self.player:
            try:
                # Pygame Zero allows you to write things like 'sounds.explosion.play()'
                # This automatically loads and plays a file named 'explosion.wav' (or .ogg) from the sounds folder (if
                # such a file exists)
                # But what if you have files named 'explosion0.ogg' to 'explosion5.ogg' and want to randomly choose
                # one of them to play? You can generate a string such as 'explosion3', but to use such a string
                # to access an attribute of Pygame Zero's sounds object, we must use Python's built-in function getattr
                sound = getattr(sounds, name + str(randint(0, count - 1)))
                sound.play()
            except Exception as e:
                # If no such sound file exists, print the name
                print(e)

# Widths of the letters A to Z in the font images
CHAR_WIDTH = [27, 26, 25, 26, 25, 25, 26, 25, 12, 26, 26, 25, 33, 25, 26,
              25, 27, 26, 26, 25, 26, 26, 38, 25, 25, 25]

def char_width(char):
    # Return width of given character. For characters other than the letters A to Z (i.e. space, and the digits 0 to 9),
    # the width of the letter A is returned. ord gives the ASCII/Unicode code for the given character.
    index = max(0, ord(char) - 65)
    return CHAR_WIDTH[index]

def draw_text(text, y, x=None):
    if x == None:
        # If no X pos specified, draw text in centre of the screen - must first work out total width of text
        x = (WIDTH - sum([char_width(c) for c in text])) // 2

    for char in text:
        screen.blit("font0"+str(ord(char)), (x, y))
        x += char_width(char)

IMAGE_WIDTH = {"life":44, "plus":40, "health":40}

def draw_status():
    # Display score, right-justified at edge of screen
    number_width = CHAR_WIDTH[0]
    s = str(game.player.score)
    draw_text(s, 451, WIDTH - 2 - (number_width * len(s)))

    # Display level number
    draw_text("LEVEL " + str(game.level + 1), 451)

    # Display lives and health
    # We only display a maximum of two lives - if there are more than two, a plus symbol is displayed
    lives_health = ["life"] * min(2, game.player.lives)
    if game.player.lives > 2:
        lives_health.append("plus")
    if game.player.lives >= 0:
        lives_health += ["health"] * game.player.health

    x = 0
    for image in lives_health:
        screen.blit(image, (x, 450))
        x += IMAGE_WIDTH[image]

# Is the space bar currently being pressed down?
space_down = False

# Has the space bar just been pressed? i.e. gone from not being pressed, to being pressed
def space_pressed():
    global space_down
    if keyboard.space:
        if space_down:
            # Space was down previous frame, and is still down
            return False
        else:
            # Space wasn't down previous frame, but now is
            space_down = True
            return True
    else:
        space_down = False
        return False

# Pygame Zero calls the update and draw functions each frame

class State(Enum):
    MENU = 1
    PLAY = 2
    GAME_OVER = 3

def update():
    global state, game

    if state == State.MENU:
        if space_pressed():
            # Switch to play state, and create a new Game object, passing it a new Player object to use
            state = State.PLAY
            game = Game(Player())
        else:
            game.update()

    elif state == State.PLAY:
        if game.player.lives < 0:
            game.play_sound("over")
            
            f = open("results.txt","a") 
            f.write(str(game.player.score))
            f.write('\n')
            f.close()
            
            state = State.GAME_OVER
        else:
            game.update()

    elif state == State.GAME_OVER:
        if space_pressed():
            # Switch to menu state, and create a new game object without a player
            state = State.MENU
            game = Game()

def draw():
    game.draw()

    if state == State.MENU:
        # Draw title screen
        screen.blit("title", (0, 0))

        # Draw "Press SPACE" animation, which has 10 frames numbered 0 to 9
        # The first part gives us a number between 0 and 159, based on the game timer
        # Dividing by 4 means we go to a new animation frame every 4 frames
        # We enclose this calculation in the min function, with the other argument being 9, which results in the
        # animation staying on frame 9 for three quarters of the time. Adding 40 to the game timer is done to alter
        # which stage the animation is at when the game first starts
        anim_frame = min(((game.timer + 40) % 160) // 4, 9)
        screen.blit("space" + str(anim_frame), (130, 280))

    elif state == State.PLAY:
        draw_status()

    elif state == State.GAME_OVER:
        draw_status()
        # Display "Game Over" image
        screen.blit("over", (0, 0))


# Set up sound system and start music
try:
    pygame.mixer.quit()
    pygame.mixer.init(44100, -16, 2, 1024)

    music.play("theme")
    music.set_volume(0.3)
except:
    # If an error occurs, just ignore it
    pass



# Set the initial game state
state = State.MENU

# Create a new Game object, without a Player object
game = Game()

pgzrun.go()
