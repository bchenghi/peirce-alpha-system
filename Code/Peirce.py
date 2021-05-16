import tkinter as tk
import math
from itertools import permutations
from pyswip.prolog import Prolog

# values for horizontal and vertical padding
xpadding = 20 
ypadding = 20 

# default values for height and width if no children
xdefault = 50
ydefault = 50

# Graph that was copied or cut
copyorcutGraphs = []

# State and state pointers for non-proof mode and proof mode
proofMode = False
states = []
statesProof = []
pointer = -1
pointerProof = -1

graph = None 
topGraphId = None

distance_between = 20
winW = 500
winH = 500
boxWidth = 10

bgColor = '#fff'
selectedColor = 'Grey'
defaultColor = '#fb0'

root = tk.Tk()
canvas = tk.Canvas(root, width=winW, height=winH, borderwidth=0, highlightthickness=0, bg=bgColor)
prolog = Prolog()
prolog.consult("peirce.pl")

# Formula entry for start command
enterBtn = None
entry = None

insertionButton = None
insertionEntry = None

displayText = None
var = tk.StringVar()
var.set("Welcome! Enter a formula in 'start' to get started") 

multiSelectText = None
mSVar = tk.StringVar()

deiterationButton = None
runIteration = False
runDeiteration = False

multiSelected = []
multiSelectParent = None

firstSelected = []

def deselectMulti():
    global multiSelected
    for i in range(len(multiSelected)-1, -1, -1):
        deselectGraph(multiSelected[i])

# Methods for printing graph
def clearAndPrint():
    global graph
    global entry
    global enterBtn
    global displayText
    global multiSelectText
    global var
    canvas.delete("all")

    displayText = tk.Label(root, font=("Helvetica",12), width=100, textvariable=var, bg=bgColor)
    displayText.place(relx=0.5, rely=0.925, anchor=tk.CENTER)
    multiSelectText = tk.Label(root, font=("Helvetica",11), width=100, textvariable=mSVar, bg=bgColor)
    multiSelectText.place(relx=0.5, rely=0.97, anchor=tk.CENTER)
    if graph != None:
        graph.x1 = 2
        graph.y1 = 2
        graph.calculateCoord()
        printGraph(graph)

def printGraph(inGraph):
    printGraphRec(inGraph, True)

def printGraphRec(inGraph, firstRun):
    global canvas
    if (type(inGraph) == Box):
        id = canvas.create_rectangle(inGraph.x1, inGraph.y1, inGraph.x2, inGraph.y2, width=boxWidth, outline=defaultColor)
        inGraph.id = id
    elif type(inGraph) == Atom:
        id = canvas.create_text((inGraph.x1 + inGraph.x2)//2, (inGraph.y1 + inGraph.y2)//2, font=('Helvetica', 20), fill=defaultColor, text=inGraph.char)
        inGraph.id = id
    elif type(inGraph) == Graph:
        id = canvas.create_rectangle(inGraph.x1, inGraph.y1, inGraph.x2, inGraph.y2, fill=bgColor, outline=bgColor)
        canvas.lift(id)
        inGraph.id = id
        if firstRun:
            global topGraphId
            topGraphId = id

    for g in inGraph.children:
        printGraphRec(g, False)


# Assigns global selected variable with selected graph, updates color of selected/deselected graphs
def select(*args):
    global multiSelected
    global graph
    ids = canvas.find_overlapping(args[0].x, args[0].y, args[0].x+1, args[0].y+1)
    selectedGraph = None

    if len(ids) > 0:
        selectedGraph = find(ids[len(ids)-1], graph)

    if len(ids) == 0:
        selectedGraph = graph


    if runIteration:
        multiSelected = [selectedGraph]
        iterationSecond()
        deselectMulti()
        return

    # deselect previously selected graph
    if selectedGraph in multiSelected:
        deselectGraph(selectedGraph)
        return

    global multiSelectParent
    if multiSelectParent == None:
        parents = findParents(selectedGraph.id, graph, None)
        if len(parents) > 0:
            multiSelectParent = parents[len(parents)-1]
        else:
            # selectedGraph was top level graph, with no parent, give it a place holder multiSelectParent
            if type(selectedGraph) == Graph:
                multiSelectParent = Graph(1)
    else:
        if len(multiSelected) == 1 and type(multiSelected[0]) == Graph and selectedGraph in multiSelected[0].children:
            var.set("Graph already selected by region")
            return
        if not selectedGraph in multiSelectParent.children:
            var.set("You can only multi-select graphs in the same depth")
            return

    if selectedGraph == None:
        selectedGraph = graph
    if type(selectedGraph) == Box:
        canvas.itemconfig(selectedGraph.id, outline=selectedColor)
    elif type(selectedGraph) == Atom:
        canvas.itemconfig(selectedGraph.id, fill=selectedColor)
    elif type(selectedGraph) == Graph:
        canvas.itemconfig(selectedGraph.id, fill=selectedColor, outline=selectedColor)
        if selectedGraph.id == topGraphId:
            canvas.config(bg=selectedColor)
            displayText.config(bg=selectedColor)
            multiSelectText.config(bg=selectedColor)

    multiSelected.append(selectedGraph)


def deselectGraph(inGraph):
    resetGraphColor(inGraph)
    multiSelected.remove(inGraph)
    if len(multiSelected) == 0:
        global multiSelectParent
        multiSelectParent = None

def resetGraphColor(inGraph):
    if inGraph != None:
        if type(inGraph) == Box:
            canvas.itemconfig(inGraph.id, outline=defaultColor)
        elif type(inGraph) == Atom:
            canvas.itemconfig(inGraph.id, fill=defaultColor)
        elif type(inGraph) == Graph:
            canvas.itemconfig(inGraph.id, fill=bgColor, outline=bgColor)
            canvas.configure(bg=bgColor)
            displayText.config(bg=bgColor)
            multiSelectText.config(bg=bgColor)

# returns graph with given id
def find(id, current):
    if id == current.id:
        return current
    else:
        for child in current.children:
            foundGraph = find(id, child)
            if foundGraph != None:
                return foundGraph
        return None

# Returns list of parents
def findParents(id, current, parent):
    if current == None:
        return []
    if id == current.id:
        if parent == None:
            return []

        return [parent]

    for child in current.children:
        parents = findParents(id, child, current)
        if len(parents) > 0:
            if parent == None:
                return parents

            result = [parent]
            result.extend(parents)
            return result
    return []


# Removes graph of given id, returns removed graph 
def cut(id, current, parent):
    if current == None:
        return None

    if id == current.id:
        # If current is entire graph, i.e. no parent
        if parent == None:
            global graph
            graph = Graph(0)
            var.set("Cut successful!")
            return current


        parent.removeChild(current)
        var.set("Cut successful!")
        return current 
    else:
        for child in current.children:
            removed = cut(id, child, current)
            if removed != None:
                return removed
        return None

# Copies the graph and sets the same ids.
# Printing the graph with clearAndPrint, will set the ids to be unique from the original graph
def copy(inGraph):
    copyGraph = None
    if type(inGraph) == Box:
        copyGraph = Box(inGraph.id)

    elif type(inGraph) == Atom:
        copyGraph = Atom(inGraph.char, inGraph.id)
    else:
        copyGraph = Graph(inGraph.id)

    if type(inGraph) != Box:
        for g in inGraph.children:
            childCopy = copy(g)
            copyGraph.addChild(childCopy)
    else:
        childCopy = copy(inGraph.children[0])
        copyGraph.children[0] = childCopy
    return copyGraph

def paste(inGraph, toPaste):
    if type(inGraph) == Atom:
        return False

    # Should not happen, handled in pasteCommand
    if inGraph == None:
        return False

    inGraph.addChild(toPaste)
    return True

# Cuts selected graph and assigns it to copyorcutGraph, and reprints the graph
def cutCommand():
    resetStart()
    global graph
    global copyorcutGraphs
    if len(multiSelected) == 0:
        var.set("No graph selected yet")
        return
    copyorcutGraphs = []
    copyGraph = copy(graph)
    for g in multiSelected:
        cutGraph = cut(g.id, copyGraph, None)
        copyorcutGraphs.append(cutGraph)
    graph = copyGraph
    clearAndPrint()
    var.set("Cut successful!")
    addState()
    deselectMulti()

# Returns a copy of graph with given id
def copyCommand():
    resetStart()
    global copyorcutGraphs
    global multiSelected
    if len(multiSelected) == 0:
        var.set("No graph selected yet")
        return
    copyorcutGraphs = []
    for g in multiSelected:
        newCopy = copy(g)
        copyorcutGraphs.append(newCopy) 
    var.set("Copy successful!")
    deselectMulti()

# Creates a copy of the copyorcutGraph, and pastes into selected, then reprints the graph
def pasteCommand():
    resetStart()
    global multiSelected
    global copyorcutGraphs
    global graph
    if len(copyorcutGraphs) == 0:
        var.set("No graph copied/cut yet")
        return
    if len(multiSelected) == 0:
        var.set("No graph selected yet")
        return
    if len(multiSelected) != 1:
        var.set("Only select one graph to paste into")
        return

    pasteGraph = copy(copyorcutGraphs[0])
    copyGraph = copy(graph)
    toPasteInto = find(multiSelected[0].id, copyGraph)

    if len(copyorcutGraphs) > 1:
        pasteGraph = Graph(1)
        for g in copyorcutGraphs:
            copyOfG = copy(g)
            pasteGraph.addChild(copyOfG)
    pasteSuccessful = paste(toPasteInto, pasteGraph)
    if pasteSuccessful:
        var.set("Paste successful!")
    else:
        var.set("Not allowed to paste into atom")
    graph = copyGraph
    addState()
    clearAndPrint()
    deselectMulti()

def clearEntry(*args):
    global entry
    global insertionEntry
    if entry != None:
        entry.delete(0,'end')
    if insertionEntry != None:
        insertionEntry.delete(0, 'end')

# Parses user input, then generates and prints graph
def parsePrintClearEntry(*args):
    entryInput = repr(entry.get())[1:-1]
    entryInput = entryInput.lower()
    global var
    global prolog
    global graph
    global states
    global pointer
    try:
        solns = list(prolog.query('input("%s", O).'%(entryInput)))
        if len(solns) == 0:
            var.set("Issue with input") 
            return
        graph = formGraph(solns[0]['O'])
        clearEntry(args)
        var.set("Input accepted and transformed into graph!")
        addState()
        # convert soln into graph, and print
    except Exception as err:
        var.set("Issue with input") 
    finally:
        resetEnd()

# Forms graph from DCG parse tree, and returns graph
def formGraph(input):
    if len(input) == 0:
        return Graph(1)
    resultGraph = Graph(0)
    formGraphRec(input, resultGraph)  
    return resultGraph

def formGraphRec(input, parent):
    if input == 'true':
        parent.addChild(Graph(1))
    elif input == 'false':
        parent.addChild(Box())
    elif len(input) == 1:
        parent.addChild(Atom(input.upper()))

    elif input[:3] == 'and':
        terms = split(input)
        newGraph = Graph(1)
        formGraphRec(terms[0], newGraph)
        formGraphRec(terms[1], newGraph)
        parent.addChild(newGraph)

    elif input[:3] == 'neg':
        term = input[4:-1]
        box = Box()
        formGraphRec(term, box)
        parent.addChild(box)


# Splits conjunction and returns a list of two terms
def split(input):
    solns = list(prolog.query('split("%s", O, O1).'%(input)))
    result = []
    for soln in solns:
        result.append(soln['O'])
        result.append(soln['O1'])
    return result

def ins_double_cut():
    resetStart()
    global multiSelected
    global graph
    if len(multiSelected) == 0:
        var.set("No graph selected yet")
        return
    box1 = Box()
    for g in multiSelected:
        box1.addChild(copy(g))
    box2 = Box()
    box2.addChild(box1)
    copyGraph = copy(graph)
    parentGraphs = findParents(multiSelected[0].id, copyGraph, None)
    parentGraph = None
    if len(parentGraphs) > 0:
        parentGraph = parentGraphs[len(parentGraphs) - 1]
        if len(multiSelected) == 1:
            parentGraph.replaceChild(multiSelected[0].id, box2)
        else:
            for g in multiSelected:
                parentGraph.removeChild(g)
            parentGraph.addChild(box2)
        graph = copyGraph
    else:
        # parentGraph is None, just set new graph as graph
        finalGraph = Graph(0)
        finalGraph.addChild(box2)
        graph = finalGraph
    addState()
    clearAndPrint()
    deselectMulti()

def rem_double_cut():
    resetStart()
    global multiSelected
    global graph
    if len(multiSelected) == 0:
        var.set("No graph selected yet")
        deselectMulti()
        return
    if len(multiSelected) != 1:
        var.set("Only select a single outer cut to remove double cut")
        deselectMulti()
        return
    if type(multiSelected[0]) != Box:
        var.set("Select an outer cut to remove a double cut!")
        deselectMulti()
        return
    # childrenInChildGraph should be a single box to do removal of double cut
    childrenInChildGraph = multiSelected[0].getChildren()[0].getChildren()
    if len(childrenInChildGraph) != 1 or type(childrenInChildGraph[0]) != Box:
        var.set("No double cut found")
        deselectMulti()
        return
    # innerBoxGraphChildren is the children in inner box's graph
    copyGraph = copy(graph)
    innerBoxGraphChildren = childrenInChildGraph[0].getChildren()[0].getChildren()
    selectedsParents = findParents(multiSelected[0].id, copyGraph, None)
    # If selected is a cut, will always have parent
    # selectedsParent is from the copied graph
    selectedsParent = selectedsParents[len(selectedsParents) - 1]
    selectedsParent.removeChild(multiSelected[0])
    for g in innerBoxGraphChildren:
        selectedsParent.addChild(copy(g))
    graph = copyGraph
    addState()
    clearAndPrint()
    deselectMulti()

def iteration():
    resetStart()
    global runIteration
    global firstSelected
    global multiSelectParent
    if len(multiSelected) == 0:
        var.set('Outer graph not selected yet')
        return
    firstSelected = multiSelected
    multiSelectParent = None
    resetFlags()
    runIteration = True
    var.set("Select inner region or cut to iterate graph into")

def iterationSecond():
    global firstSelected
    global runIteration
    global graph
    runIteration = False
    secondSelected = multiSelected[0]

    if len(multiSelected) == 0:
        var.set('Inner graph not selected yet')
        return

    if type(secondSelected) != Box and type(secondSelected) != Graph:
        var.set('Region or cut was not selected')
        for g in firstSelected:
            resetGraphColor(g)
        
        firstSelected = []
        return

    isNested = True
    for g in firstSelected:
        if not nested(g, secondSelected):
            isNested = False
            break

    

    if not isNested: 
        var.set("Second graph is not nested in first graph")
        
        for g in firstSelected:
            resetGraphColor(g)
        
        firstSelected = []
        return
    toCopyGraph = None
    if type(firstSelected[0]) != Graph:
        newFirstSelected = Graph(1)
        for g in firstSelected:
            newFirstSelected.addChild(g)
        toCopyGraph = newFirstSelected
    else:
        toCopyGraph = firstSelected[0]
    copiedGraph = copy(graph)
    copySecondSelected = find(secondSelected.id, copiedGraph)
    copyOfFirst = copy(toCopyGraph)
    addSuccess = copySecondSelected.addChild(copyOfFirst)
    if addSuccess:
        var.set('Iteration successful!')
    graph = copiedGraph
    addState()
    resetEnd()
    firstSelected = []

def deiteration():
    resetStart()
    global firstSelected
    global runDeiteration
    global deiterationButton
    global multiSelectParent
    if len(multiSelected) == 0:
        var.set('Outer graph not selected yet')
        return
    firstSelected = []
    for i in multiSelected:
        firstSelected.append(i)

    deselectMulti()
    setupDeiteration()
    multiSelectParent = None
    resetFlags()
    runDeiteration = True

def deiterationSecond():
    global firstSelected
    global runDeiteration
    global deiterationButton
    global graph
    runDeiteration = False

    if len(multiSelected) == 0:
        var.set('Inner graph not selected yet')
        resetEnd()
        return    
    secondSelected = multiSelected

    # Only used for checking nesting, no need for copy
    graphFirstSelected = firstSelected[0]


    graphSecondSelected = secondSelected[0]

        
    isNested = nested(graphFirstSelected, graphSecondSelected)
    if not isNested:
        var.set("Second graph is not nested in first graph")
        firstSelected = []
        resetEnd()
        return

    # No need for copy as used only for checking equivalence
    if type(firstSelected[0]) != Graph:
        aFirstSelected = Graph(1)
        for g in firstSelected:
            aFirstSelected.addChild(g)
        newFirstSelected = aFirstSelected
    else:
        newFirstSelected = firstSelected[0]


    if type(secondSelected[0]) != Graph:
        aSecondSelected = Graph(1)
        for g in secondSelected:
            aSecondSelected.addChild(g)
        newSecondSelected = aSecondSelected
    else:
        newSecondSelected = secondSelected[0]

    # newFirstSelected and newSecondSelected do not need to be copies of first and second selected as only check for equivalence
    isEquivalent = equivalent(newFirstSelected, newSecondSelected)
    if not isEquivalent:
        var.set("Second graph is not equivalent to first graph")
        firstSelected = []
        resetEnd()
        return
    copiedGraph = copy(graph)
    secondParents = None
    secondParents = findParents(secondSelected[0].id, copiedGraph, None)
    secondParent = None
    if len(secondParents) > 0:
        secondParent = secondParents[len(secondParents) - 1]
    for c in secondSelected:
        secondParent.removeChild(c)
    var.set('Deiteration successful!')
    graph = copiedGraph
    resetEnd()
    addState()
    firstSelected = []

def deiterationButtonCommand():
    deiterationSecond()
    deselectMulti()
    return

def setupDeiteration():
    global deiterationButton
    deiterationButton = tk.Button(root, text="Run deiteration", font=("Helvetica", 10), width=15, command=deiterationButtonCommand)
    deiterationButton.place(relx=0.5, rely=0.85, anchor=tk.CENTER)
    var.set("Select nested graph to deiterate")

def collapseDeiteration():
    global deiterationButton
    if deiterationButton != None:
        deiterationButton.destroy()
        deiterationButton = None

def erasure():
    resetStart()
    global multiSelected
    global graph
    if len(multiSelected) == 0:
        var.set("No graph selected yet")
        return
    g = copy(multiSelected[0])
    copyGraph = copy(graph)
    ancestors = findParents(g.id, copyGraph, None)
    numOfCuts = 0

    for a in ancestors:
        if type(a) == Box:
            numOfCuts += 1

    if numOfCuts % 2 != 0:
        var.set("Graph is not evenly-enclosed")
        deselectMulti()
        return
    else:
        parent = None
        if len(ancestors) == 0:
            # remove entire graph if graph has no ancestors, then return
            graph = Graph(0)
            addState()
            clearAndPrint()
            deselectMulti()
            return
            
        parent = ancestors[len(ancestors) - 1]
        for c in multiSelected:
            parent.removeChild(c)
        var.set('Erasure successful!')
        graph = copyGraph
        addState()
        clearAndPrint()
        deselectMulti()

            
        
        

def insertion():
    resetStart()
    global multiSelected
    if len(multiSelected) == 0:
        var.set("No graph selected yet")
        return
    if len(multiSelected) > 1:
        var.set("Only select a single region or cut to insert into")
        deselectMulti()
        return
    if type(multiSelected[0]) != Box and type(multiSelected[0]) != Graph:
        var.set("Only select region or cut to insert into")
        deselectMulti()
        return
    parents = findParents(multiSelected[0].id, graph, None)
    num_cuts = 0
    for p in parents:
        if type(p) == Box:
            num_cuts += 1
    if num_cuts % 2 == 0:
        var.set("Graph is not oddly-enclosed!")
        deselectMulti()
        return
    setupInsertion()
    
def runInsertion(*args):
    entryInput = repr(insertionEntry.get())[1:-1]
    entryInput = entryInput.lower()
    global var
    global prolog
    global graph
    try:
        solns = list(prolog.query('input("%s", O).'%(entryInput)))
        if len(solns) == 0:
            var.set("Issue with input") 
            return
        newGraph = formGraph(solns[0]['O'])
        copiedGraph = copy(graph)
        toAddTo = find(multiSelected[0].id, copiedGraph)
        toAddTo.addChild(newGraph)
        graph = copiedGraph
        var.set("Input accepted and inserted into graph!")
        addState()
        # convert soln into graph, and print
    except Exception as err:
        print(err)
        var.set("Issue with input")
    finally:
        resetEnd()
    
def startCommand():
    resetStart()
    setupStart()

def setupInsertion():
    global insertionEntry
    global insertionButton 
    insertionEntry = tk.Entry(root, font=("Helvetica",10), text="Formula", width=20)
    insertionEntry.place(relx=0.5, rely=0.775, anchor=tk.CENTER)
    insertionButton = tk.Button(root, text="Run insertion", font=("Helvetica", 10), width=15, command=runInsertion)
    insertionButton.place(relx=0.5, rely=0.85, anchor=tk.CENTER)
    var.set("Type formula of graph to insert")

def collapseInsertion():
    global insertionEntry
    global insertionButton
    if insertionEntry != None:
        insertionEntry.destroy()
        insertionEntry = None
    if insertionButton != None:
        insertionButton.destroy()
        insertionButton = None

def setupStart():
    global entry
    global enterBtn
    entry = tk.Entry(root, font=("Helvetica",10), text="Formula", width=20)
    entry.place(relx=0.5, rely=0.775, anchor=tk.CENTER)
    enterBtn = tk.Button(root, text="Enter formula", font=("Helvetica", 10), width=15, command=parsePrintClearEntry)
    enterBtn.place(relx=0.5, rely=0.85, anchor=tk.CENTER)
    var.set("Insert formula to initialise graph")

def collapseStart():
    global entry
    global enterBtn
    if entry != None:
        entry.destroy()
        entry = None
    if enterBtn != None:
        enterBtn.destroy()
        enterBtn = None

def resetEnd():
    resetFlags()
    collapseInsertion()
    collapseDeiteration()
    collapseStart()
    clearAndPrint()
    deselectMulti()

def resetStart():
    resetFlags()
    collapseInsertion()
    collapseDeiteration()
    collapseStart()

    



def nested(outerGraph, innerGraph):
    isNested = False
    outerParents = findParents(outerGraph.id, graph, None)
    outerParent = None
    if len(outerParents) > 0:
        outerParent = outerParents[len(outerParents) - 1]
    if outerParent == None:
        return False
    # Check if outer's parent is inner graph
    if outerParent.id == innerGraph.id:
        isNested = True

    if not isNested:
        for child in outerParent.children:
            if child.id != outerGraph.id:
                found = find(innerGraph.id, child)
                if found:
                    isNested = True
                    break
    return isNested

def equivalent(firstGraph, secondGraph):
    if type(firstGraph) == Atom and type(secondGraph) == Atom and firstGraph.char != secondGraph.char:
       return False 
    if type(firstGraph) != type(secondGraph):
        return False
    if len(firstGraph.getChildren()) != len(secondGraph.getChildren()):
        return False
    firstGChildrenP = permutations(firstGraph.getChildren())
    numOfChildren = len(firstGraph.getChildren())
    result = False
    for p in firstGChildrenP:
        breakEarly = False
        for i in range(numOfChildren):
            if not equivalent(p[i], secondGraph.getChildren()[i]):
                breakEarly = True
                break
        if not breakEarly:
            result = True
            break
    return result

def resetFlags():
    global runIteration
    global runDeiteration
    runIteration = False
    runDeiteration = False

def addState():
    if not proofMode:
        global states
        global pointer
        if len(states) > 0:
            states = states[0:pointer+1]
        states.append(graph)
        pointer += 1
    else:
        global statesProof
        global pointerProof
        if len(statesProof) > 0:
            statesProof = statesProof[0:pointerProof+1]
        statesProof.append(graph)
        pointerProof += 1
        

def undoCommand():
    global graph
    if not proofMode:
        global pointer
        if pointer == 0:
            var.set('No more undo available')
        else:
            pointer -= 1
            graph = states[pointer]
            resetEnd()
            var.set("Undo successful!")
    else:
        global pointerProof
        if pointerProof == 0:
            var.set('No more undo available')
        else:
            pointerProof -= 1
            graph = statesProof[pointerProof]
            resetEnd()
            var.set("Undo successful!")

def redoCommand():
    global graph
    if not proofMode:
        global pointer
        if pointer == len(states) - 1:
            var.set('No more redo available')
        else:
            pointer += 1
            graph = states[pointer]
            resetEnd()
            var.set("Redo successful!")
    else:
        global pointerProof
        if pointerProof == len(statesProof) - 1:
            var.set('No more redo available')
        else:
            pointerProof += 1
            graph = statesProof[pointerProof]
            resetEnd()
            var.set("Redo successful!")

class Graph:
    def __init__(self, id):
        if id == 0:
            self.id = 0 
            self.children = []
            self.x1 = 2
            self.y1 = 2
            self.x2 = None
            self.y2 = None
        else:
            self.id = id
            self.children = []
            # Will be set once graph is complete and calculatecoord is called
            self.x1 = None
            self.y1 = None
            self.x2 = None
            self.y2 = None

    def addChild(self, graphToAdd):
        if type(graphToAdd) == Graph:
            for child in graphToAdd.children:
                self.children.append(child)
            return True

        self.children.append(graphToAdd)
        return True

    def getChildren(self):
        return self.children

    def replaceChild(self, toReplaceId, newGraph):
        children = self.getChildren()
        for i in range(len(children)): 
            if children[i].id == toReplaceId:
                children.remove(children[i])
                if type(newGraph) == Graph:
                    for g in newGraph.getChildren():
                        children.insert(i,g)
                        i += 1
                    return True    
                children.insert(i,newGraph) 
                return True
        return False


    def removeChild(self, graphToCut):
        for i in range(len(self.children)):
            if self.children[i].id == graphToCut.id:
                del self.children[i]
                return

    def calculateCoord(self, parentGraph = None, childNum = 0):
        if self == None:
            return

        if parentGraph != None:
            if type(parentGraph) == Box:
                self.x1 = parentGraph.x1 
                self.y1 = parentGraph.y1 
            else:
                if childNum == 0:
                    self.x1 = parentGraph.x1 + xpadding
                    self.y1 = parentGraph.y1 + ypadding
                else:
                    self.x1 = parentGraph.children[childNum - 1].x2 + xpadding
                    self.y1 = parentGraph.y1 + ypadding

        # If current type is box, only one Graph child, set coord according to Graph child
        if type(self) == Box:
            self.children[0].calculateCoord(self, 0)
            self.x2 = self.children[0].x2 
            self.y2 = self.children[0].y2 
            return


        furthestChildx2 = 0
        largestChildy2 = 0

        for i in range(len(self.children)):
            self.children[i].calculateCoord(self, i)
            if i == len(self.children) - 1:
                furthestChildx2 = self.children[i].x2
            if largestChildy2 < self.children[i].y2:
                largestChildy2 = self.children[i].y2

        # self has child
        if furthestChildx2 != 0:
            self.x2 = furthestChildx2 + xpadding
            self.y2 = largestChildy2 + ypadding
        else:
            self.x2 = self.x1 + xdefault
            self.y2 = self.y1 + ydefault



class Atom(Graph):
    def __init__(self,  char, id = 1):
        super().__init__(id)
        self.char = char
    def addChild(self, graphToAdd):
        return False


class Box(Graph):
    def __init__(self, id = 1, childBoxId = 1):
        super().__init__(id)
        self.children = [Graph(childBoxId)]

    def addChild(self, graphToAdd):
        self.children[0].addChild(graphToAdd)
        return True

    # Only for cutting the single Graph child a Box has
    def removeChild(self, graphToRemove):
        self.children = [Graph(1)]

    def replaceChild(self, toReplaceId, newGraph):
        if self.children[0].id == toReplaceId:
            finalGraph = Graph(1)
            finalGraph.addChild(newGraph)
            self.children[0] = finalGraph
        else:
            print("Box's child graph does not match toReplaceId")


def printGraphId(inGraph):
    if inGraph == None:
        return
    print(inGraph.id)
    for c in inGraph.children:
        printGraphId(c)


graph = Graph(0)
addState()

# ===================== Tkinter setup =======================
root.title("Peirce Alpha System")

menuBar = tk.Menu(root)

def proveCommand():
    global statesProof
    global pointerProof
    global graph
    global proofMode
    resetStart()
    root.config(menu=rulesMenuBar)
    var.set("Proof started")
    proofMode = True
    statesProof = []
    pointerProof = -1
    addState() # adds state in proofMode


commandMenu = tk.Menu(menuBar, tearoff=0)
commandMenu.add_command(label="Undo", command=undoCommand)
commandMenu.add_command(label="Redo", command=redoCommand)
commandMenu.add_separator()
commandMenu.add_command(label="Start", command=startCommand)
commandMenu.add_command(label="Cut",command=cutCommand)
commandMenu.add_command(label="Copy", command=copyCommand)
commandMenu.add_command(label="Paste",command=pasteCommand)
commandMenu.add_separator()
commandMenu.add_command(label="Start Proof",command=proveCommand)
commandMenu.add_separator()
commandMenu.add_command(label="Quit", command=root.destroy)
menuBar.add_cascade(label="Commands", menu=commandMenu)
root.config(menu=menuBar)

rulesMenuBar = tk.Menu(root)

# Sets menu bar to edit mode, sets graph as where the proof started
def stopProveCommand():
    global graph
    global proofMode
    resetStart()
    root.config(menu=menuBar)
    var.set("Proof stopped")
    proofMode = False
    graph = states[pointer]
    resetEnd()

rulesMenu = tk.Menu(rulesMenuBar, tearoff=0)
rulesMenu.add_command(label="Undo Rule", command=undoCommand)
rulesMenu.add_command(label="Redo Rule", command=redoCommand)
rulesMenu.add_separator()
rulesMenu.add_command(label="Erase", command=erasure)
rulesMenu.add_command(label="Insert", command=insertion)
rulesMenu.add_command(label="Iterate", command=iteration)
rulesMenu.add_command(label="Deiterate", command=deiteration)
rulesMenu.add_command(label="Insert double cut", command=ins_double_cut)
rulesMenu.add_command(label="Remove double cut", command=rem_double_cut)
rulesMenu.add_separator()
rulesMenu.add_command(label="Stop Proof", command=stopProveCommand)
rulesMenuBar.add_cascade(label="Rules", menu=rulesMenu)

clearAndPrint()
canvas.bind("<Button-1>", select)
canvas.pack(fill="both",expand=True)
root.mainloop()

