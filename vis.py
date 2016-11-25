import os, json, sys, tkinter

CELL_SIZE = 16
COLOURS = ["black", "cyan", "#ff9966", "red", "yellow", "#bbaaff", "#9cffcc"]

class Board(tkinter.Canvas):
    def __init__(self, owner, d, *args, **kwargs):

        tkinter.Canvas.__init__(self, owner, *args, **kwargs)

        self.owner = owner
        self.d = d
        self.turn = 0
        self.mousex = None
        self.mousey = None

        self.bind('<Motion>', self.mouse)
        self.bind('<Left>', self.back_one)
        self.bind('<Right>', self.advance_one)
        self.bind('<Leave>', self.mouse_exit)

        self.draw()
        self.update_status()

    def back_one(self, event):
        self.turn -= 1
        if self.turn < 0:
            self.turn = 0
        self.draw()
        self.update_status()

    def advance_one(self, event):
        self.turn += 1
        if self.turn >= len(self.d["frames"]):
            self.turn = len(self.d["frames"]) - 1
        self.draw()
        self.update_status()

    def mouse(self, event):
        self.mousex = event.x // CELL_SIZE
        self.mousey = event.y // CELL_SIZE
        if self.mousex >= self.d["width"] or self.mousex < 0:
            self.mousex = None
        if self.mousey >= self.d["height"] or self.mousey < 0:
            self.mousey = None
        self.update_status()

    def mouse_exit(self, event):
        self.mousex, self.mousey = None, None
        self.update_status()

    def update_status(self):
        if self.mousex == None or self.mousey == None:
            statusbar.config(text = "")
            return

        i = self.mousey * self.d["width"] + self.mousex
        owner, strength = self.d["frames"][self.turn][self.mousey][self.mousex] # Note y,x format
        prod = self.d["productions"][self.mousey][self.mousex]

        statusbar.config(text = " i = {} ({}, {})      owner = {}      str = {}      prod = {}".format(
            i, self.mousex, self.mousey, owner if owner != 0 else " ", strength, prod))

    def draw(self):
        self.delete(tkinter.ALL)    # DESTROY all!
        self.owner.wm_title(str(self.turn) + " / " + str(len(self.d["frames"]) - 1))

        frame = self.d["frames"][self.turn]

        for x in range(self.d["width"] + 1):
            self.create_line(x * CELL_SIZE, 0, x * CELL_SIZE, self.d["height"] * CELL_SIZE + CELL_SIZE, fill = "#333333")

        for y in range(self.d["height"] + 1):
            self.create_line(0, y * CELL_SIZE, self.d["width"] * CELL_SIZE + CELL_SIZE, y * CELL_SIZE, fill = "#333333")

        for y in range(self.d["height"]):
            for x in range(self.d["width"]):
                owner, strength = frame[y][x]               # Note y,x format
                if owner == 0:
                    continue
                reduction = (255 - strength) // 40
                rect_x = x * CELL_SIZE
                rect_y = y * CELL_SIZE
                self.create_rectangle(
                    rect_x + reduction, rect_y + reduction, rect_x + CELL_SIZE - reduction, rect_y + CELL_SIZE - reduction,
                    fill = COLOURS[owner],
                    outline = "white" if strength == 255 else "black",
                    tags = "max" if strength == 255 else "normal")

        self.tag_raise("max")   # Move white-outline rects to front for aesthetic reasons


class Root(tkinter.Tk):
    def __init__(self, *args, **kwargs):

        tkinter.Tk.__init__(self, *args, **kwargs)

        if len(sys.argv) != 2:
            print("No filename received")
            sys.exit(1)

        try:
            with open(sys.argv[1]) as infile:
                d = json.loads(infile.read())
        except:
            print("Error while loading")
            sys.exit(1)

        width = d["width"]
        height = d["height"]

        global statusbar
        statusbar = tkinter.Label(self, text="...awaiting status...", bd = 0, bg = "black", fg = "white", anchor = tkinter.W)
        statusbar.pack(side = tkinter.BOTTOM, fill = tkinter.X)

        global board
        board = Board(self, d, width = width * CELL_SIZE + 1, height = height * CELL_SIZE + 1, bd = 0, bg = "black", highlightthickness = 0)
        board.pack()
        board.focus_set()

if __name__ == "__main__":
    app = Root()
    app.mainloop()
