from __future__ import division
import sys
import go
import tacticalPlayer
from math import sqrt
from copy import copy,deepcopy
from random import random,choice
from PyQt4 import Qt, QtGui, QtCore

class BoardMain(QtGui.QWidget):
    def __init__(self, parent=None):
        super(BoardMain, self).__init__(parent)
        #set some general properties of the window
        self.setWindowTitle("Go Board")
        self.setMouseTracking(True)

        vbox = QtGui.QHBoxLayout()
        conLayout = QtGui.QGridLayout()
        
        boardView = BoardView(self)
        
        vbox.addWidget(boardView)
        vbox.addLayout(conLayout)
        self.setLayout(vbox)
        
class BoardView(QtGui.QWidget):
    def __init__(self, parent=None):
        super(BoardView, self).__init__(parent)
        self.setMinimumSize(300, 300)
        self.setMouseTracking(True)
        
        self.mx = 0
        self.my = 0
        
        self.hover = None
        self.board = go.Board()
        
        self.ai = tacticalPlayer.AiPlayer(self.board,2)
        self.AIopinions = None
        
    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        #qp.setRenderHint(QtGui.QPainter.Antialiasing);
        
        font = QtGui.QFont('Serif', 7, QtGui.QFont.Light)
        qp.setFont(font)
        
        size = self.size()
        w = size.width()
        h = size.height()
        
        boardsize = min(w,h) * 0.9
        bx = (w-boardsize)/2
        by = (h-boardsize)/2
        
        # draw board shadow
        qp.setPen(QtCore.Qt.NoPen)
        qp.setBrush(QtGui.QColor(128, 128, 128))
        qp.drawRect(bx+6, by+4, boardsize, boardsize)
        
        # draw board
        qp.setPen(QtGui.QColor(123, 100, 51))
        qp.setBrush(QtGui.QColor(220, 179, 91))
        qp.drawRect(bx, by, boardsize, boardsize)
        
        # lines on board
        blackPen = QtGui.QPen(QtGui.QColor(0, 0, 0), boardsize*0.004, QtCore.Qt.SolidLine);
        qp.setPen(blackPen)
        boxs = boardsize / 19.6
        margin = (boardsize - (boxs * 18)) / 2
        btop = by + margin
        bbot = (by + boardsize) - margin
        bleft = bx + margin
        bright = (bx + boardsize) - margin
        self.boardPos = {}
        for i in range(19):
            for j in range(19):
                self.boardPos[(i,j)] = ( bleft+i*boxs, btop+j*boxs)
        for i in range(19):
            lx = self.boardPos[(i,0)][0]
            qp.drawLine(lx,btop,lx,bbot)
            ly = self.boardPos[(0,i)][1]
            qp.drawLine(bleft,ly,bright,ly)
            
        # Draw star points
        qp.setPen(QtCore.Qt.NoPen)
        qp.setBrush(QtGui.QColor(0, 0, 0))
        diameter = boardsize*0.012
        for pos in [(3,3),(3,9),(3,15),(9,3),(9,9),(9,15),(15,3),(15,9),(15,15)]:
            x,y = self.boardPos[pos]
            qp.drawEllipse( x-diameter/2, y-diameter/2, diameter, diameter )
        
        # draw stones
        qp.setPen(QtCore.Qt.NoPen)
        stoneSize = boxs * 0.91
        self.clickSize = stoneSize
        shadowOffset = stoneSize * 0.08
        for i in range(19):
            for j in range(19):
                if self.board.b[(i,j)] != 0:
                    x,y = self.boardPos[(i,j)]
                    # stone shadow
                    qp.setBrush(QtGui.QColor(80, 80, 80, 100))
                    qp.drawEllipse( x-stoneSize/2+shadowOffset, y-stoneSize/2+shadowOffset, stoneSize, stoneSize )
                    # stone
                    if self.board.b[(i,j)] == 1:
                        qp.setBrush(QtGui.QColor(20, 0, 33))
                    elif self.board.b[(i,j)] == 2:
                        qp.setBrush(QtGui.QColor(255, 250, 220))
                    qp.drawEllipse( x-stoneSize/2, y-stoneSize/2, stoneSize, stoneSize )
                    
        # draw AI opinion
        
        if self.AIopinions is not None:
            for posi,value in self.AIopinions.items():
                if value != None:
                    appsize = stoneSize * value
                    qp.setBrush(QtGui.QColor(255-int(value*255), int(value*255), 180, 100))
                    opos = self.boardPos[posi]
                    qp.drawEllipse( opos[0]-appsize/2, opos[1]-appsize/2, appsize, appsize )
        
        
        # draw hover stone
        if self.hover is not None:
            if self.board.player == 1:
                qp.setBrush(QtGui.QColor(20, 0, 33, 170))
            elif self.board.player == 2:
                qp.setBrush(QtGui.QColor(255, 250, 220, 170))
            hoverpos = self.boardPos[self.hover]
            qp.drawEllipse( hoverpos[0]-stoneSize/2, hoverpos[1]-stoneSize/2, stoneSize, stoneSize )
        
        qp.end()
        
    def mouseMoveEvent(self, event):
        self.mx = event.x()
        self.my = event.y()
        hover = None
        closest = 999
        for index,pos in self.boardPos.items():
            fardom = ((pos[0]-self.mx)**2 + (pos[1]-self.my)**2)**0.5
            if (fardom < self.clickSize) and (fardom < closest):
                if self.board.isLegal(index,self.board.player):
                    closest = fardom
                    hover = index
        oldhover = self.hover
        self.hover = hover
        if self.hover != oldhover:
            self.repaint()
    
        
    def mousePressEvent(self, event):
        if event.button() == 1:
            chosen = self.hover
            if chosen != None:
                if self.board.isLegal(chosen,self.board.player):
                    self.board.applyMove(chosen)
                    self.hover = None
                    self.ai.changeColor(self.board.player)
                    self.ai.board = self.board
                    self.AIopinions = self.ai.analyze()
                    QtCore.QTimer.singleShot(500,self.computerMove)
                    self.repaint()
        else:
            poke = None
            closest = 999
            for index,pos in self.boardPos.items():
                fardom = ((pos[0]-self.mx)**2 + (pos[1]-self.my)**2)**0.5
                if (fardom < self.clickSize) and (fardom < closest):
                    closest = fardom
                    poke = index
            if poke is not None:
                grp = self.board.groupsByStones[poke]
                self.ai.board = self.board
                self.ai.changeColor(grp.c)
                gs = self.ai.groupSafety(grp)
                #print self.board.numberOfEyes(grp)

    def computerMove(self):
        chosen = None
        highest = -999
        for pos,val in self.AIopinions.items():
            if val > highest:
                if self.board.isLegal(pos,self.board.player):
                    highest = val
                    chosen = pos
        print chosen
        if chosen != None:
            self.board.applyMove(chosen)
            self.ai.changeColor(self.board.player)
            self.ai.board = self.board
            self.AIopinions = self.ai.analyze()
            self.repaint()
            #QtCore.QTimer.singleShot(0,self.computerMove)



        
    
app = Qt.QApplication(sys.argv)
widget = BoardMain()
widget.show()

app.exec_()
