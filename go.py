from copy import deepcopy
    
class Group:
    def __init__(self,pos,c,libslist):
        self.stones = [pos]
        self.libs = set(libslist)
        self.c = c

class Board:
    def __init__(self):
        self.b = {}
        for i in range(19):
            for j in range(19):
                self.b[(i,j)] = 0
        self.ko = None
        self.groupsByStones = {}
        self.numCaptured = {1:0, 2:0}
        self.player = 1
        
    def isLegal(self,position,player):
        # move is illegal is the position is occupied
        if self.b[position] != 0:
            return False
            
        # move is illegal if the position is the ko point
        if position == self.ko:
            return False
            
        # move is illegal if it is suicide
        # if any neighbors are open, it's not suicide
        neighbors = neighborsOf(position)
        if any([self.b[p]==0 for p in neighbors]):
            return True
       
        # if at least one neighbor of the same color has at least one liberty other than this one it's OK
        # if any groups of the opposite color have only one remaining liberty its OK, you're capturing them
        for group in self.nbgroups(position):
            if group.c == player:
                if len(group.libs) > 1:
                    return True
            elif group.c == self.otherplayer(player):
                if len(group.libs)==1:
                    return True
        # all neighbors are occupied but don't meet the special conditions
        return False
        
    def otherplayer(self,p):
        return [0,2,1][p]
        
    def applyMove(self,position):
        # place the stone
        self.addStone(position,self.player)
        # remove all dead groups of opposite color
        captured = []
        for group in self.nbgroups(position):
            if len(group.libs)==0:
                if group.c == self.otherplayer(self.player):
                    # this group was in atari and now it's dead
                    captured.extend(group.stones)
                    self.removeGroup(group)
        # set or reset the ko point
        if len(captured)==1:
            self.ko = captured[0]
        else:
            self.ko = None
        # increment score for player
        self.numCaptured[self.player] += len(captured)
        # flip player
        self.player = self.otherplayer(self.player)
        
        
    def removeGroup(self,group):
        # removing an entire group involves:
        # 
        # 1: changing the board spaces to empty
        # 2: deleting every entry from self.groupsByStones that references it
        # 3: and adding the liberties from the newly opened spaces to any groups they are adjacent to.
        
        # steps 1 and 2 can happen in the same loop
        for stone in group.stones:
            self.b[stone] = 0
            del self.groupsByStones[stone]
        # step 3 can only happen after 1 and 2 are complete
        for stone in group.stones:
            for grp in self.nbgroups(stone):
                # make sure neighboring group has this liberty.
                grp.libs.add(stone)
    
    def addStone(self,pos,color):
        # add a stone at a position and update groups
        self.b[pos] = color
        
        # create a new group from this stone
        libs = set()
        for nb in neighborsOf(pos):
            if self.b[nb] == 0:
                libs.add(nb)
        newg = Group(pos, color, libs)
        
        for grp in self.nbgroups(pos):
            if grp.c == color:
                # merge groups that share this stone's color with the new group
                newg.stones.extend(grp.stones)
                newg.libs = newg.libs.union(grp.libs)
            else:
                # for groups of opposite color, just remove the liberty.
                grp.libs.remove(pos)
        
        try: # remove the liberty from the group we just created that corresponds to this position
            newg.libs.remove(pos)
        except KeyError: pass
        
        # key this new group into the table
        for stone in newg.stones:
            self.groupsByStones[stone] = newg
        
    
    def nbgroups(self,pos):
        result = []
        for nb in neighborsOf(pos):
            try:
                group = self.groupsByStones[nb]
                if group not in result:
                    result.append(group)
            except KeyError: pass
        return result
        
    def numberOfEyes(self,tg):
        # return the number of eyes formed by group tg
        # flood fill empty space from all of it's liberties
        # and see if any of the resulting regions are bordered entirely by this group or the wall.
        eyes = 0
        checklist = list(tg.libs)
        while len(checklist) > 0:
            pos = checklist.pop()
            region,black,white = floodFill(self.b,pos)
            # don't want to check anything twice
            for r in region:
                try: checklist.remove(r)
                except ValueError: pass
            if tg.c == 1: # if target group color is black
                if len(white) == 0: # and this empty region is not bordered by any enemy stones
                    eyes += 1
            else:
                if len(black) == 0:
                    eyes += 1
        return eyes
                
            

def floodFill(stones,pos):
    # return the region including pos which shares the color of pos
    # include the set of positions included, and the set of border positions of each of the other two colors.
    targetColor = stones[pos]
    # if you search empties, the blacks will be in whale and the whites will be in alien
    other1 = [1,2,0][targetColor]
    other2 = [2,0,1][targetColor]
    included = set()
    included.add(pos)
    whale = set()
    alien = set()
    looklist = neighborsOf(pos)
    while len(looklist)>0:
        inve = looklist.pop()
        if stones[inve] == targetColor:
            included.add(inve)
            for nb in neighborsOf(inve):
                if (nb not in looklist) and (nb not in alien) and (nb not in whale) and (nb not in included):
                    looklist.append(nb)
        elif stones[inve] == other1:
            whale.add(inve)
        elif stones[inve] == other2:
            alien.add(inve)
    return included,whale,alien

    
    
def findAllGroups(board):
    allGroups = []
    activeList = board.keys()
    activeList.remove('ko')
    while len(activeList) > 0:
        thing = activeList.pop()
        stoneKind = board[thing]
        if stoneKind != 0:
            group = [thing]
            elist = neighborsOf(thing)
            liberties = []
            while len(elist) > 0:
                pos = elist.pop()
                if board[pos] == 0:
                    liberties.append(pos)
                elif board[pos] == stoneKind:
                    if pos not in group:
                        group.append(pos)
                        activeList.remove(pos)
                        for nbpos in neighborsOf(pos):
                            if (nbpos not in group) and (nbpos not in elist):
                                elist.append(nbpos)
            allGroups.append({'group':group, 'liberties':liberties, 'stoneKind':stoneKind})
    #print '\n'.join(map(repr,allGroups))
    return allGroups
    
def countEnclosedTerritory(board):
    # return the number of empty spaces enclosed by each player
    
    ans = {1:0,2:0}
    for player in [1,2]:
        # basically we want the empty groups with liberties of all my color
        # swap my color with empty and run the groups algorithm
        bcopy = deepcopy(board)
        swapper = [player,1,2]
        swapper[player] = 0
        for pos in bcopy.keys():
            if pos != 'ko':
                bcopy[pos] = swapper[bcopy[pos]]
        # now find groups
        grps = findAllGroups(bcopy)
        # count only groups that have no neighbors of opposite color in bcopy
        count = 0
        for group in grps:
            clean = True
            for stone in group['group']:
                for nb in neighborsOf(stone):
                    if bcopy[nb] == opposite(player):
                        clean = False
            if clean:
                count += len(group['group'])
        ans[player] = count
    return ans

def neighborsOf(pos):
    nb = []
    # if the position is not on the top row
    if pos[1] != 0:
        # it has a neighbor above it
        nb.append( (pos[0], pos[1]-1) )
    # likewise...
    if pos[1] != 18:
        nb.append( (pos[0], pos[1]+1) )
    if pos[0] != 0:
        nb.append( (pos[0]-1, pos[1]) )
    if pos[0] != 18:
        nb.append( (pos[0]+1, pos[1]) )
    return nb













