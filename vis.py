import os, json, sys, tkinter

CELL_SIZE = 16
COLOURS = ["#666666", "cyan", "#ff9966", "red", "yellow", "#bbaaff", "#9cffcc"]

class Board(tkinter.Canvas):
    def __init__(self, owner, d, *args, **kwargs):

        tkinter.Canvas.__init__(self, owner, *args, **kwargs)

        self.owner = owner
        self.d = d
        self.turn = 0
        self.mousex = None
        self.mousey = None

        self.show_neutrals = tkinter.IntVar(value = 1)
        self.show_production = tkinter.IntVar(value = 0)
        self.screen_content = None

        # We don't directly respond to key presses. Rather, keep a dict of which keys are down.
        # This prevents a massive backlog of key events.

        self.keys = dict()

        self.rects = []

        self.bind('<Motion>', self.mouse)
        self.bind('<Leave>', self.mouse_exit)
        self.bind('<KeyPress>', self.key_down)
        self.bind('<KeyRelease>', self.key_up)

        self.print_info()
        self.draw_grid()
        self.draw()
        self.update_status()
        self.owner.wm_title(str(self.turn) + " / " + str(len(self.d["frames"]) - 1))

        self.after(50, self.act)

    def act(self):

        original_turn = self.turn

        if self.keys.get("Left"):
            self.advance(-1)
        elif self.keys.get("Right"):
            self.advance(1)
        elif self.keys.get("Up"):
            self.advance(-10)
        elif self.keys.get("Down"):
            self.advance(10)
        elif self.keys.get("z") or self.keys.get("Home"):
            self.advance(-1000)
        elif self.keys.get("x") or self.keys.get("End"):
            self.advance(1000)

        # Unset some keys. Because of auto-repeat key presses, holding a key still works.
        # But this means the initial KeyPress event only moves us one frame, which is
        # nicer for the user.
        self.keys["Left"] = False
        self.keys["Right"] = False

        did_toggle_prod = False

        if self.keys.get("p"):
            did_toggle_prod = True
            self.keys["p"] = False
            if not self.show_production.get():
                self.show_production.set(1)
            else:
                self.show_production.set(0)

        if self.turn != original_turn or did_toggle_prod:
            self.redraw()
            self.update_status()

        self.after(50, self.act)

    def key_down(self, event):
        self.keys[event.keysym] = True

    def key_up(self, event):
        self.keys[event.keysym] = False

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

    def advance(self, n):
        self.turn += n
        if self.turn < 0:
            self.turn = 0
        if self.turn >= len(self.d["frames"]):
            self.turn = len(self.d["frames"]) - 1
        self.owner.wm_title(str(self.turn) + " / " + str(len(self.d["frames"]) - 1))

    def update_status(self):
        if self.mousex == None or self.mousey == None:
            statusbar.config(text = "")
            return

        i = self.mousey * self.d["width"] + self.mousex
        owner, strength = self.d["frames"][self.turn][self.mousey][self.mousex] # Note y,x format
        prod = self.d["productions"][self.mousey][self.mousex]                  # Note y,x format

        statusbar.config(text = "i: {} [{},{}] own: {} st: {} pr: {}".format(
            i, self.mousex, self.mousey, owner if owner != 0 else " ", strength, prod))

    def draw_grid(self):
        for x in range(self.d["width"] + 1):
            self.create_line(x * CELL_SIZE, 0, x * CELL_SIZE, self.d["height"] * CELL_SIZE + CELL_SIZE, fill = "#333333")

        for y in range(self.d["height"] + 1):
            self.create_line(0, y * CELL_SIZE, self.d["width"] * CELL_SIZE + CELL_SIZE, y * CELL_SIZE, fill = "#333333")

    def redraw(self, force = False):
        if self.show_production.get():
            if self.screen_content != "production" or force:
                self.draw_production()
        else:
            if self.screen_content != self.turn or force:
                self.draw()

    def draw(self):
        for r in self.rects:
            self.delete(r)
        self.rects = []

        frame = self.d["frames"][self.turn]

        for y in range(self.d["height"]):
            for x in range(self.d["width"]):
                owner, strength = frame[y][x]               # Note y,x format
                if owner == 0 and not self.show_neutrals.get():
                    continue
                reduction = ((255 - strength) // 40) if strength else CELL_SIZE // 2 - 1
                rect_x = x * CELL_SIZE
                rect_y = y * CELL_SIZE
                r = self.create_rectangle(
                    rect_x + reduction, rect_y + reduction, rect_x + CELL_SIZE - reduction, rect_y + CELL_SIZE - reduction,
                    fill = COLOURS[owner],
                    outline = "white" if strength == 255 else "black",
                    tags = "max" if strength == 255 else "normal")

                self.rects.append(r)

        self.tag_raise("max")   # Move white-outline rects to front for aesthetic reasons

        self.screen_content = self.turn

    def draw_production(self):
        for r in self.rects:
            self.delete(r)
        self.rects = []

        for y in range(self.d["height"]):
            for x in range(self.d["width"]):
                prod = self.d["productions"][y][x]      # Note y,x format

                if prod > 16:
                    prod = 16

                rect_x = x * CELL_SIZE
                rect_y = y * CELL_SIZE

                s = hex(int(255 * prod / 16))[2:]

                if len(s) == 1:
                    s = "0" + s

                colstring = "#" + s + s + s

                r = self.create_rectangle(
                    rect_x, rect_y, rect_x + CELL_SIZE, rect_y + CELL_SIZE,
                    fill = colstring)

                self.rects.append(r)

        self.screen_content = "production"

    def print_info(self):
        print("{}x{} ({} frames)".format(self.d["width"], self.d["height"], self.d["num_frames"]))
        for i in range(self.d["num_players"]):
            print("  {} - {}".format(i + 1, self.d["player_names"][i]))   # IDs are out by 1 from their index here

class Root(tkinter.Tk):
    def __init__(self, *args, **kwargs):

        tkinter.Tk.__init__(self, *args, **kwargs)
        self.resizable(width = False, height = False)

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

        global board
        board = Board(self, d, width = width * CELL_SIZE + 1, height = height * CELL_SIZE + 1, bd = 0, bg = "black", highlightthickness = 0)

        menubar = tkinter.Menu(self)
        options_menu = tkinter.Menu(menubar, tearoff = 0)
        options_menu.add_checkbutton(label = "Show neutrals", variable = board.show_neutrals, command = lambda : board.redraw(force = True))
        options_menu.add_checkbutton(label = "Show production", variable = board.show_production, command = lambda : board.redraw(force = True))

        menubar.add_cascade(label = "Options", menu = options_menu)

        self.config(menu = menubar)

        statusbar.pack(side = tkinter.BOTTOM, fill = tkinter.X)
        board.pack()

        board.focus_set()

if __name__ == "__main__":
    app = Root()
    app.mainloop()
