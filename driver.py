import time
import win32api

import numpy as np
import win32con
from PIL import Image
from PIL import ImageGrab

import move_maker
from cell_decoder import CellRecognizer
from utils import *


class Driver:
    def __init__(self, board_coords):
        self.ref_img = None
        self.board_box = board_coords
        self.img_size = (board_coords[2] - board_coords[0], board_coords[3] - board_coords[1])
        self.cell_size = (self.img_size[0] / 9, self.img_size[1] / 9)
        self.game_board = np.zeros((board_size, board_size), dtype=np.int32)
        self.cell_recognizer = CellRecognizer()
        self.cell_recognizer.train()

        self.background_img = Image.open('background.bmp')
        self.background_img = self.background_img.resize(
            (self.background_img.size[0] / 4, self.background_img.size[1] / 4), Image.NEAREST)
        self.mover = move_maker.MoveMaker()
        self.img_end_game = Image.open('end_screen.bmp')
        self.img_end_game = self.img_end_game.resize((self.img_end_game.size[0] / 4, self.img_end_game.size[1] / 4),
                                                     Image.NEAREST)

    def play(self):
        while True:
            if not self.board_is_moving():
                board_img = self.grab_board()
                if self.compare_images(board_img, self.img_end_game, 10) < 3000:
                    break
                score, move = self.mover.solve_board(self.game_board)
                self.do_move(move)
            time.sleep(0.4)  # wait for the cells to finish moving

    # It takes the screenshot of the board and then crops each cell using a nested loop
    def grab_board(self):
        global game_board
        img = ImageGrab.grab()

        img = img.crop(self.board_box)
        for y in range(0, 9):
            for x in range(0, 9):
                cell_box = (
                    x * self.cell_size[0], y * self.cell_size[1], (x + 1) * self.cell_size[0],
                    (y + 1) * self.cell_size[1])
                cell = img.crop(cell_box)
                self.game_board[y][x] = self.cell_recognizer.predict(cell)
        img = img.resize((img.size[0] / 4, img.size[1] / 4), Image.NEAREST)
        return img

    # checks if the board is in moving state (It is in moving state after the candies have been exploded)
    def board_is_moving(self):
        img = ImageGrab.grab()
        img = img.crop(self.board_box)
        img = img.resize((img.size[0] / 4, img.size[1] / 4), Image.NEAREST)

        has_movement = True
        if self.ref_img:
            has_movement = self.compare_images(img, self.ref_img, threshold=100) > 100

        self.ref_img = img
        return has_movement

    # for comparing the pixels of the cell board
    @staticmethod
    def are_pixels_equal(p1, p2, threshold):
        diff = 0
        for i in range(3):
            diff += abs(p1[i] - p2[i])
        return diff < threshold

    def compare_images(self, current, reference, threshold):
        current_data = np.array(current.getdata())
        ref_data = np.array(reference.getdata())

        diff_pixels = 0
        total_size = current.size[0] * current.size[1]
        for i in range(0, total_size - 3, 3):
            if not self.are_pixels_equal(current_data[i], ref_data[i], threshold):
                diff_pixels += 1

        print diff_pixels
        return diff_pixels

    #  for imitating the clicks on the board
    def win32_click(self, x, y):
        win32api.SetCursorPos((x, y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

    # it gets the coords of the central part of the cell
    def get_desktop_coords(self, cell):
        x = self.board_box[0] + cell[1] * self.cell_size[0] + self.cell_size[0] / 2
        y = self.board_box[1] + cell[0] * self.cell_size[1] + self.cell_size[1] / 2
        return x, y

    # sort of main function for win32 api
    def do_move(self, move):
        start = move[0]
        end = move[1]

        start_w = self.get_desktop_coords(start)
        end_w = self.get_desktop_coords(end)

        win32api.SetCursorPos(start_w)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, start_w[0], start_w[1], 0, 0)
        time.sleep(0.3)  # for waiting the board to settle down after explosions
        win32api.SetCursorPos(end_w)
        time.sleep(0.3)  # for waiting the board to settle down after explosions
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, end_w[0], end_w[1], 0, 0)
        win32api.SetCursorPos((1100, 1100))