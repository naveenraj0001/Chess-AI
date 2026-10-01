import threading

import chess
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

from chesser.ai import MinimaxAI
from chesser.state.board import Board


class BoardGrid(GridLayout):
    LIGHT_COLOR = (0.65, 0.65, 0.65, 1.0)
    DARK_COLOR = (0.35, 0.35, 0.35, 1.0)
    SELECTED_COLOR = (0.0, 0.8, 0.0, 1.0)
    TARGET_COLOR = (0.8, 0.8, 0.0, 1.0)
    WHITE_PIECE_COLOR = (1.0, 1.0, 1.0, 1.0)
    BLACK_PIECE_COLOR = (0.0, 0.0, 0.0, 1.0)

    def __init__(self, status: Label, **kwargs):
        super().__init__(**kwargs)
        self.cols = 8

        self._status = status
        self._board = Board()
        self._ai = MinimaxAI(depth=3)
        self._selected = None
        self._last_ai_move = None
        self._busy = False
        self._buttons: dict[int, Button] = {}

        self._build_board()
        self._refresh()

    def _build_board(self):
        for i in range(8):
            for j in range(8):
                square = chess.square(j, 7 - i)
                btr = Button(background_normal="", font_size="28sp", bold=True)
                btr.bind(on_press=lambda b, s=square: self._on_press(s))  # pyright: ignore
                self._buttons[square] = btr
                self.add_widget(btr)

    def _cell_color(self, square: int):
        if (chess.square_file(square) + chess.square_rank(square)) % 2 == 0:
            return self.DARK_COLOR
        return self.LIGHT_COLOR

    def _refresh(self):
        targets = set()
        if self._selected is not None:
            targets = {m.to_square for m in self._board.legal_moves_from(self._selected)}

        for square, btr in self._buttons.items():
            piece = self._board.piece_at(square)
            btr.text = piece.symbol() if piece else ""
            if piece:
                btr.color = (
                    self.WHITE_PIECE_COLOR
                    if piece.color == chess.WHITE
                    else self.BLACK_PIECE_COLOR
                )

            if square == self._selected:
                btr.background_color = self.SELECTED_COLOR
            elif square in targets:
                btr.background_color = self.TARGET_COLOR
            elif self._last_ai_move and square == self._last_ai_move.to_square:
                btr.background_color = self.TARGET_COLOR
                self._last_ai_move = None
            else:
                btr.background_color = self._cell_color(square)

        self._update_status()

    def _update_status(self):
        if self._board.is_checkmate():
            winner = "Black" if self._board.turn == chess.WHITE else "White"
            self._status.text = f"Checkmate - {winner} wins"
        elif self._board.is_game_over():
            self._status.text = "Draw"
        elif self._busy:
            self._status.text = "AI is thinking..."
        elif self._board.is_check():
            self._status.text = "Your move (check)"
        else:
            self._status.text = "Your move"

    def _is_own_piece(self, square: int) -> bool:
        piece = self._board.piece_at(square)
        return piece is not None and piece.color == chess.WHITE

    def _find_move(self, from_square: int, to_square: int):
        for move in self._board.legal_moves_from(from_square):
            if move.to_square != to_square:
                continue
            if move.promotion and move.promotion != chess.QUEEN:
                continue
            return move
        return None

    def _on_press(self, square: int):
        if self._busy or self._board.is_game_over():
            return

        if self._selected is None:
            if self._is_own_piece(square):
                self._selected = square
                self._refresh()
            return

        move = self._find_move(self._selected, square)
        if move is None:
            self._selected = square if self._is_own_piece(square) else None
            self._refresh()
            return

        self._board.push(move)
        self._selected = None

        if self._board.is_game_over():
            self._refresh()
            return

        self._busy = True
        self._refresh()
        threading.Thread(target=self._think, daemon=True).start()

    def _think(self):
        move = self._ai.best_move(self._board.raw)
        Clock.schedule_once(lambda dt: self._apply_ai_move(move))

    def _apply_ai_move(self, move: chess.Move | None):
        if move is not None:
            self._board.push(move)
            self._last_ai_move = move
        self._busy = False
        self._refresh()


class ChesserApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")
        status = Label(size_hint_y=0.08)
        root.add_widget(status)
        root.add_widget(BoardGrid(status))
        return root


if __name__ == "__main__":
    ChesserApp().run()
