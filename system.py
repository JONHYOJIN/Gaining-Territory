from tkinter import *
from tkinter import ttk
from itertools import product, chain, combinations
import random
import os
import pandas as pd
from shapely.geometry import LineString, Point, Polygon

from machine import MACHINE
from options import PLAYERS, BACKGROUND, RADIUS, LINE_WIDTH, LINE_COLOR, CIRCLE_WIDTH, CIRCLE_COLOR, \
                    USER_COLOR, MACHINE_COLOR, PROGRAM_SIZE, CANVAS_SIZE, GRID_COLOR

class SYSTEM():
    def __init__(self):
        """
            [ SYSTEM ]
            게임 설정, 진행, 점수 계산 등을 수행하는 시스템.

            - score: USER와 MACHINE의 획득 점수 ([USER, MACHINE])
            - drawn_lines: 그려진 Line들의 집합
               * Line: [(x1, y1), (x2, y2)]
                    -> x값이 작은 점이 항상 왼쪽에 위치 (x값이 같을 경우, y값을 기준으로 함; organize_points 함수를 통해 적용)
            - whole_points: 전체 점(Point) 좌표의 집합
            - triangles: 점령된 Triagnle 집합 (점수 계산 및 취소에 사용 됨)
               * Triagnle: [Point, Point, Point] 
                    -> x값이 작은 점이 항상 왼쪽에 위치 (x값이 같을 경우, y값을 기준으로 함; organize_points 함수를 통해 적용)
            - turn: 선을 그어야 하는 Player

            - interval / offset: Line, Circle 등을 Canvas에 그리기 위한 "Canvas 상 좌표 값" 계산을 위해 사용
            - location: Canvas 상의 좌표 값
            - board_size: Board 판의 크기 (각 축이 갖는 상자의 수; 7로 고정)
            - machine: MACHINE 객체 ( USER는 별도의 객체를 사용하지 않음)
        
        """
        # Initialization
        self.score = [0, 0] # USER, MACHINE
        self.drawn_lines = [] # Drawn Lines
        self.board_size = 7 # 7 x 7 Matrix
        self.num_dots = 0
        self.whole_points = []
        self.location = []
        self.triangles = [] # [(a, b), (c, d), (e, f)]

        self.turn = None
        self.interval = None
        self.offset = None
        self.machine = MACHINE()

        self.get_score = False

        # GUI
        self.root = Tk()

        # GUI Interface Settings
        self.root.configure(background=BACKGROUND)  # Background
        self.root.title("Gaining Territoy")
        self.root.geometry(PROGRAM_SIZE)
        self.root.resizable(True, True)

        """
            [ ComboBox Style (Line 58~68) ]
            Reference: https://stackoverflow.com/questions/27912250/how-to-set-the-background-color-of-a-ttk-combobox
        """
        self.combostyle = ttk.Style()
        self.combostyle.theme_create('combostyle', parent='alt',
                                settings = {'TCombobox':
                                            {'configure':
                                            {'selectbackground': 'white',
                                            'fieldbackground': 'white',
                                            'background': "gray"
                                            }}}
                                )
        # ATTENTION: this applies the new style 'combostyle' to all ttk.Combobox
        self.combostyle.theme_use('combostyle') 

        # Board
        self.label_options = Label(self.root, text="Select Map:", background=BACKGROUND)
        self.label_options.place(x=10, y=10)

        board_list = ["Random 5", "Random 10", "Random 15", "Random 20"]
        board_list.extend(os.listdir("./board_library"))
        self.combobox_board = ttk.Combobox(self.root, textvariable=StringVar(), width=20, background=BACKGROUND)
        self.combobox_board['value'] = board_list
        self.combobox_board.set("Random 10")
        self.combobox_board.place(x=90, y=12)

        # Turn
        self.label_firstturn = Label(self.root, text="First Turn:", background=BACKGROUND)
        self.label_firstturn.place(x=300, y=10)

        self.combobox_firstturn = ttk.Combobox(self.root, textvariable=StringVar(), width=8, background=BACKGROUND)
        self.combobox_firstturn['value'] = PLAYERS
        self.combobox_firstturn.set("USER")
        self.combobox_firstturn.place(x=368, y=12)

        # Start Game
        self.button_startgame = Button(self.root, text="Start Game!", width=10, fg="grey20", highlightbackground=BACKGROUND, command=self.set_new_board)
        self.button_startgame.place(x=480, y=8)

        # Canvas
        self.board = Canvas(self.root, width=CANVAS_SIZE, height=CANVAS_SIZE, background="white")
        self.board.place(x=200, y=50)

        # Turn
        turn_x, turn_y = 10, 60
        self.label_turn = Label(self.root, text="[ TURN ]", background=BACKGROUND)
        self.label_turn.place(x=turn_x, y=turn_y)
        self.label_currentturn = Label(self.root, text=self.turn, background=BACKGROUND)
        self.label_currentturn.place(x=turn_x, y=turn_y+25)

        # Score
        score_x, score_y = 10, 120
        self.label_score = Label(self.root, text="[ SCORE ]", background=BACKGROUND)
        self.label_score.place(x=score_x, y=score_y)

        self.label_userscore1 = Label(self.root, text="USER:", background=BACKGROUND)
        self.label_userscore1.place(x=score_x, y=score_y+30)
        self.label_userscore2 = Label(self.root, text=self.score[0], background=BACKGROUND)
        self.label_userscore2.place(x=score_x+45, y=score_y+30)

        self.label_machinescore1 = Label(self.root, text="MACHINE:", background=BACKGROUND)
        self.label_machinescore1.place(x=score_x, y=score_y+55)
        self.label_machinescore2 = Label(self.root, text=self.score[1], background=BACKGROUND)
        self.label_machinescore2.place(x=score_x+70, y=score_y+55)

        # Cancel
        cancel_x, cancel_y = 10, 200
        self.button_cancel = Button(self.root, text="Cancel", width=10, fg="grey20", highlightbackground=BACKGROUND, command=self.cancel)
        self.button_cancel.place(x=cancel_x, y=cancel_y)

        # User
        user_x, user_y = 10, 250
        self.label_user = Label(self.root, text="[ USER ]", background=BACKGROUND, fg=USER_COLOR)
        self.label_user.place(x=user_x, y=user_y)

        self.label_x = Label(self.root, text="X", background=BACKGROUND)
        self.label_x.place(x=user_x+60, y=user_y+25)
        self.label_y = Label(self.root, text="Y", background=BACKGROUND)
        self.label_y.place(x=user_x+100, y=user_y+25)

        self.label_userstart = Label(self.root, text="From:", background=BACKGROUND)
        self.label_userstart.place(x=user_x, y=user_y+50)
        self.start_x = Entry(self.root, textvariable=IntVar(), width=3, highlightbackground=BACKGROUND)
        self.start_x.place(x=user_x+40, y=user_y+50)
        self.start_y = Entry(self.root, textvariable=IntVar(), width=3, highlightbackground=BACKGROUND)
        self.start_y.place(x=user_x+80, y=user_y+50)

        self.label_userend = Label(self.root, text="    To:", background=BACKGROUND)
        self.label_userend.place(x=user_x, y=user_y+80)
        self.end_x = Entry(self.root, textvariable=IntVar(), width=3, highlightbackground=BACKGROUND)
        self.end_x.place(x=user_x+40, y=user_y+80)
        self.end_y = Entry(self.root, textvariable=IntVar(), width=3, highlightbackground=BACKGROUND)
        self.end_y.place(x=user_x+80, y=user_y+80)

        self.button_usergo = Button(self.root, text="Go!", width=10, fg="grey20", highlightbackground=BACKGROUND, command=self.user_go)
        self.button_usergo.place(x=user_x, y=user_y+105)

        # Machine
        machine_x, machine_y = 10, 405
        self.label_machine = Label(self.root, text="[ MACHINE ]", background=BACKGROUND, fg=MACHINE_COLOR)
        self.label_machine.place(x=machine_x, y=machine_y)

        self.button_machinego = Button(self.root, text="Go!", width=10, fg="grey20", highlightbackground=BACKGROUND, command=self.machine_go)
        self.button_machinego.place(x=machine_x, y=machine_y+25)

        # Warning
        warning_x, warning_y = 10, 460
        self.label_warning = Label(self.root, text="", background=BACKGROUND)
        self.label_warning.place(x=warning_x, y=warning_y)

        # Result
        result_x, result_y = 10, 510
        self.label_result = Label(self.root, text="The game is ongoing!!", background=BACKGROUND)
        self.label_result.place(x=result_x, y=result_y)

        self.root.mainloop()
    
    # Canvas(Board)-related Functions
    def set_new_board(self):
        """
            초기 Board 설정
        """
        # The number of Dots
        map_info = self.combobox_board.get()
        if "Random" in map_info:
            self.num_dots = int(map_info.split(" ")[-1])
            random_selection = True
        else:
            random_selection = False

        # Initialization
        self.score = [0, 0] # USER, MACHINE
        self.drawn_lines = [] # Drawn Lines
        self.whole_points = []
        self.location = []
        self.triangles = []
        self.turn = None
        self.board.delete(ALL)

        self.initialize_turn()

        self.interval = CANVAS_SIZE // (self.board_size+1)
        self.offset = (CANVAS_SIZE % (self.board_size+1)) // 2
        self.location = [x*self.interval+self.offset for x in range(1, (self.board_size+1))]
        idx_offset = 200 // self.board_size

        # Background Grid
        for loc in self.location:
            self.line((loc, self.offset+self.interval), (loc, 500-self.interval), color=GRID_COLOR)
            self.line((self.offset+self.interval, loc), (500-self.interval, loc), color=GRID_COLOR)

        for idx_x, _ in enumerate(self.location):
            self.board.create_text((self.location[0]+idx_x*self.interval, self.location[0]-idx_offset), text=idx_x, width=5, fill="gray", font=("Arial", 16))
            self.board.create_text((self.location[0]-idx_offset, self.location[0]+idx_x*self.interval), text=idx_x, width=5, fill="gray", font=("Arial", 16))
            for idx_y, _ in enumerate(self.location):
                self.whole_points.append((idx_x, idx_y))

        if random_selection:
            self.whole_points = random.sample(self.whole_points, self.num_dots)
        else:
            map = pd.read_csv(os.path.join("./board_library", map_info), index_col="Unnamed: 0")
            self.whole_points = [point for point in self.whole_points if map.loc[point[1]][point[0]]]
            self.num_dots = len(self.whole_points)

        for idx_x, idx_y in self.whole_points:
            self.circle(self.location[idx_x], self.location[idx_y], CIRCLE_COLOR)

    def circle(self, cx, cy, color):
        self.board.create_oval(cx-RADIUS, cy-RADIUS, cx+RADIUS, cy+RADIUS, fill=color, width=CIRCLE_WIDTH)
    
    def line(self, start, end, color):
        self.last_line = self.board.create_line(start[0], start[1], end[0], end[1], fill=color, width=LINE_WIDTH)
    
    def occupy_triangle(self, triangle, color=USER_COLOR):
        if self.turn == "USER":
            self.last_triangle = self.board.create_polygon([self.offset+self.interval*(x+1) for x in list(chain(*triangle))], fill=color, outline=LINE_COLOR, width=2)
        elif self.turn == "MACHINE":
            self.last_triangle = self.board.create_polygon([self.offset+self.interval*(x+1) for x in list(chain(*triangle))], fill=color, outline=LINE_COLOR, width=2)

    def user_go(self):
        start_x = int(self.start_x.get())
        start_y = int(self.start_y.get())
        end_x = int(self.end_x.get())
        end_y = int(self.end_y.get())

        line = self.organize_points([(start_x, start_y), (end_x, end_y)])

        if self.check_availability("USER", line):
            self.label_warning.config(text="")
            self.drawn_lines.append(line)

            draw = [(self.location[point[0]], self.location[point[1]]) for point in line]
            self.line(draw[0], draw[1], color=LINE_COLOR)

            self.check_triangle(line)
            self.change_turn() 

            self.label_userscore2.config(text=self.score[0])

            if self.check_endgame():
                if self.score[0]==self.score[1]:
                    self.label_result.config(text="The game ended in a tie...")
                else:
                    f = lambda i: self.score[i]
                    winner = PLAYERS[max(range(len(self.score)), key=f)]
                    self.label_result.config(text=f"The Winner is the {winner}!!")

        else:
            self.label_warning.config(text="Check the turn or the input!")
    
    def machine_go(self):
        self.machine.score = self.score
        self.machine.drawn_lines = self.drawn_lines
        self.machine.whole_points = self.whole_points
        self.machine.location = self.location
        self.machine.triangles = self.triangles

        line = self.machine.find_best_selection()
        line = self.organize_points(line)

        if self.check_availability("MACHINE", line ):
            self.label_warning.config(text="")
            self.drawn_lines.append(line)

            draw = [(self.location[point[0]], self.location[point[1]]) for point in line]
            self.line(draw[0], draw[1], color=LINE_COLOR)

            self.check_triangle(line)
            self.change_turn() 

            self.label_machinescore2.config(text=self.score[1])

            if self.check_endgame():
                if self.score[0]==self.score[1]:
                    self.label_result.config(text="The game ended in a tie...")
                else:
                    f = lambda i: self.score[i]
                    winner = PLAYERS[max(range(len(self.score)), key=f)]
                    self.label_result.config(text=f"The Winner is the {winner}!!")

        else:
            self.label_warning.config(text="Check the turn \nor the machine error!")

    def check_availability(self, turn, line):
        line_string = LineString(line)

        # Must be one of the whole points
        condition1 = (line[0] in self.whole_points) and (line[1] in self.whole_points)
        
        # Must not skip a dot
        condition2 = True
        for point in self.whole_points:
            if point==line[0] or point==line[1]:
                continue
            else:
                if bool(line_string.intersection(Point(point))):
                    condition2 = False

        # Must not cross another line
        condition3 = True
        for l in self.drawn_lines:
            if len(list(set([line[0], line[1], l[0], l[1]]))) == 3:
                continue
            elif bool(line_string.intersection(LineString(l))):
                condition3 = False

        # Must be a new line
        condition4 = (line not in self.drawn_lines)

        # Must be own turn
        condition5 = (self.turn==turn)

        if condition1 and condition2 and condition3 and condition4 and condition5:
            return True
        else:
            return False    
    
    def check_endgame(self):
        remain_to_draw = [[point1, point2] for (point1, point2) in list(combinations(self.whole_points, 2)) if self.check_availability(self.turn, [point1, point2])]
        return False if remain_to_draw else True

    # Score Checking Functions
    def check_triangle(self, line):
        self.get_score = False

        point1 = line[0]
        point2 = line[1]

        point1_connected = []
        point2_connected = []

        for l in self.drawn_lines:
            if l==line: # 자기 자신 제외
                continue
            if point1 in l:
                point1_connected.append(l)
            if point2 in l:
                point2_connected.append(l)

        if point1_connected and point2_connected: # 최소한 2점 모두 다른 선분과 연결되어 있어야 함
            for line1, line2 in product(point1_connected, point2_connected):
                
                # Check if it is a triangle & Skip the triangle has occupied
                triangle = self.organize_points(list(set(chain(*[line, line1, line2]))))
                if len(triangle) != 3 or triangle in self.triangles:
                    continue

                empty = True
                for point in self.whole_points:
                    if point in triangle:
                        continue
                    if bool(Polygon(triangle).intersection(Point(point))):
                        empty = False

                if empty:
                    self.triangles.append(triangle)
                    self.score[PLAYERS.index(self.turn)]+=1

                    color = USER_COLOR if self.turn=="USER" else MACHINE_COLOR
                    self.occupy_triangle(triangle, color=color)
                    self.get_score = True
                
    # Organization Functions
    def organize_points(self, point_list):
        point_list.sort(key=lambda x: (x[0], x[1]))
        return point_list
    
    # Go back to prior
    def cancel(self):
        if self.drawn_lines:
            recent = self.drawn_lines[-1]
            self.drawn_lines.remove(recent)
            self.board.delete(self.last_line)
            self.change_turn()
            
            if self.get_score and self.triangles:
                recent_triangle = self.triangles[-1]
                self.triangles.remove(recent_triangle)
                self.board.delete(self.last_triangle)
                if self.turn=="USER":
                    self.score[0] -= 1
                    self.label_userscore2.config(text=self.score[0])
                elif self.turn=="MACHINE":
                    self.score[1] -= 1
                    self.label_machinescore2.config(text=self.score[1])

    # Turn-related Functions
    def check_turn(self):
        if self.turn:
            return self.turn
        else:
            return self.combobox_firstturn.get()
    
    def initialize_turn(self):
        turn = self.check_turn()
        if turn == "USER":
            self.turn = turn
            self.label_currentturn.config(text=turn, fg=USER_COLOR)

        elif turn == "MACHINE":
            self.turn = turn
            self.label_currentturn.config(text=turn, fg=MACHINE_COLOR)
        
    def change_turn(self):
        turn = self.check_turn()
        if turn == "USER":
            self.turn = "MACHINE"
            self.label_currentturn.config(text=self.turn, fg=MACHINE_COLOR)

        elif turn == "MACHINE":
            self.turn = "USER"
            self.label_currentturn.config(text=self.turn, fg=USER_COLOR)
    
