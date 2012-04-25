from __future__ import division
from copy import copy,deepcopy
import go
from random import random
from collections import defaultdict

class AiPlayer:
    def __init__(self,board,color):
        self.board = board
        self.mycolor = color
        self.otherp = [0,2,1][color]
        
    def changeColor(self,color):
        self.mycolor = color
        self.otherp = [0,2,1][color]
        
    
    def groupSafety(self,group):
        print repr(self.board)
        safe = 0
        # estimate how safe a group is
        # returning a negative number implies that the group cannot be saved
        
        # do you have room to breath?
        # among the set of your neighbors,
        # and among the set of your liberties neighbors
        
        safecom = [0]*(6*2)
        
        for xi,positionSet in enumerate([group.stones, list(group.libs)]):
        
            nbset = set()
            for pos in positionSet:
                for nb in go.neighborsOf(pos):
                    nbset.add(nb)
                        
            # what proportion are enemy stones?
            # what proportion are other groups of your color?
            # do those other groups have one or two eyes?
            freeCount = 0
            enemyCount = 0
            ownGroup = 0
            ownNoEyes = 0
            ownOneEye = 0
            ownTwoEyes = 0
            for pos in list(nbset):
                if self.board.b[pos] == self.otherp:
                    enemyCount += 1
                elif self.board.b[pos] == self.mycolor:
                    # this is my own color, is it part of this group?
                    tg = self.board.groupsByStones[pos]
                    if tg == group:
                        ownGroup += 1
                    else:
                        # it's some other group of mine, how many eyes does it have?
                        eyes = self.board.numberOfEyes(tg)
                        if eyes == 0:
                            ownNoEyes += 1
                        elif eyes == 1:
                            ownOneEye += 1
                        else:
                            ownTwoEyes += 1
                else:
                    freeCount += 1
                
            # take all these counts and use it to estimate the safety of the position
            safecom[xi*6+0] = (enemyCount / (len(nbset)+0.1))*2-1
            safecom[xi*6+1] = (freeCount / (len(nbset)+0.1))*2-1
            safecom[xi*6+2] = (ownGroup / (len(nbset)+0.1))*2-1
            safecom[xi*6+3] = (ownNoEyes / (len(nbset)+0.1))*2-1
            safecom[xi*6+4] = (ownOneEye / (len(nbset)+0.1))*2-1
            safecom[xi*6+5] = (ownTwoEyes / (len(nbset)+0.1))*2-1
            
            
        weights = [
            -1.4,  # enemy stones next to group 
             2.5,  # free places next to group 
            -0.03, # stones from own group next to group 
             0.1,  # stones from groups with no eyes next to group 
             0.4,  # stones from groups with one eye next to group 
             0.6,  # stones from groups with two eyes next to group 
             
            -3.0,  # enemy stones next to liberties
             2.0,  # free places next to liberties
             0.0, # stones from own group next to liberties
             0.1,  # stones from groups with no eyes next to liberties
             0.4,  # stones from groups with one eye next to liberties
             0.6,  # stones from groups with two eyes next to liberties
             
        ]
        
        print "\nevaluation for",self.mycolor
        print "\n".join(map(repr,safecom))
        safe = sum(map(lambda x: x[0]*x[1], zip(weights,safecom)))
        print "weighted total",safe
        
        # do you have freedom?
        safe += (len(group.libs)*1.5-2.0)
                
        # how many eyes do you have?
        myeyes = self.board.numberOfEyes(group)
        if myeyes == 0:
            safe -= 0.3
        elif myeyes == 1:
            safe += 0.5
        elif myeyes >= 2:
            safe += 100
        
        # do you have a good chance of forming some?
        
        
        print "final total",safe
        
        return safe
        
        
    def analyze(self):
        
        moves = deepcopy(self.board.b)
        legalmoves = {}
        for pos in moves.keys():
            if self.board.isLegal(pos,self.mycolor):
                legalmoves[pos] = 0
                moves[pos] = 0
            else:
                moves[pos] = None
        
        mygroups = []
        enemygroups = []
        for grp in self.board.groupsByStones.values():
            if grp.c == self.mycolor:
                if grp not in mygroups:
                    mygroups.append(grp)
            else:
                if grp not in enemygroups:
                    enemygroups.append(grp)
            
        # it's important to protect any groups you may have in atari in proportion to how big they are
        for grp in mygroups:
            if len(grp.libs) == 1:
                px = list(grp.libs)[0]
                if legalmoves.has_key(px):
                    legalmoves[px] += 3 * len(grp.stones)
        
        # it's important to put enemy groups in atari in proportion to how big they are
        for grp in enemygroups:
            if len(grp.libs) == 1:
                px = list(grp.libs)[0]
                if legalmoves.has_key(px):
                    legalmoves[px] += 3 * len(grp.stones)
        
        # taking corners is valuable
        # taking sides is valuable
        # but not too close to the wall
        #value = [0, 1, 2, 3, 4, 5, 8, 5, 3, 1]
        #for pos in legalmoves.keys():
        #    legalmoves[pos] += (value[abs(pos[0]-9)] + value[abs(pos[1]-9)]) * 0.1
        
        # claiming places that are vacant is valuable
        for pos in legalmoves.keys():
            distance = 0 # distance to closest stone
            legalmoves[pos] += distance * 0.25
        
        # connecting groups is valuable
        # reward positions for being a liberty of more than one of my groups
        libsofgroups = defaultdict(lambda: 0)
        for grp in mygroups:
            for pos in list(grp.libs):
                libsofgroups[pos] += 1
        for pos,val in libsofgroups.items():
            if legalmoves.has_key(pos):
                legalmoves[pos] += (val**2) * 0.1
        
        # making groups harder to capture is good
            # give them two eyes
            # give them more liberties
            # judge whether a group is lost or not (negative safety?)
            
        # look for enemy groups with nearly negative safety, and threaten them.
        # don't both investing a move in threatening an already defeated group unless you have nothing better to do
        for grp in enemygroups:
            self.changeColor(self.otherp)
            safety = self.groupSafety(grp)
            self.changeColor(self.otherp)
            if -1 < safety < 2:
                for pos in list(grp.libs):
                    if legalmoves.has_key(pos):
                        legalmoves[pos] += 5
                    
            
        
        
        # cut enemy lines
        # if any positions are liberties of 2 or 3 of the enemies groups and 1 or two of mine, upvalue those
        libsofenemy = defaultdict(lambda: 0)
        for grp in enemygroups:
            for pos in list(grp.libs):
                libsofenemy[pos] += 1
        for lib,val in libsofenemy.items():
            if libsofgroups.has_key(lib):
                legalmoves[pos] = (val)**2
        
        # force the other player's hand
        
        # add noise
        for pos in legalmoves.keys():
            legalmoves[pos] += random()*0.01

        # normalize legal moves
        v0 = min(legalmoves.values())
        v1 = max(legalmoves.values())
        for pos in moves.keys():
            moves[pos] = None
        for pos in legalmoves.keys():
            moves[pos] = (legalmoves[pos] - v0) / (v1 - v0)
            
        return moves
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
