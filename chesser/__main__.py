import math
import threading

import chess
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.splitter import Splitter

from chesser.ai import MinimaxAI, Analysis
from chesser.state.board import Board


PIECE_IMAGES = {
    "P": "chesser/assets/white-pawn.png",
    "R": "chesser/assets/white-rook.png",
    "N": "chesser/assets/white-knight.png",
    "B": "chesser/assets/white-bishop.png",
    "Q": "chesser/assets/white-queen.png",
    "K": "chesser/assets/white-king.png",
    "p": "chesser/assets/black-pawn.png",
    "r": "chesser/assets/black-rook.png",
    "n": "chesser/assets/black-knight.png",
    "b": "chesser/assets/black-bishop.png",
    "q": "chesser/assets/black-queen.png",
    "k": "chesser/assets/black-king.png",
}

PIECE_NAMES = {
    chess.KING: "King",
    chess.QUEEN: "Queen",
    chess.ROOK: "Rook",
    chess.KNIGHT: "Knight",
    chess.BISHOP: "Bishop",
    chess.PAWN: "Pawn",
}

PIECE_ORDER = [
    chess.KING,
    chess.QUEEN,
    chess.ROOK,
    chess.KNIGHT,
    chess.BISHOP,
    chess.PAWN,
]

ANALYSIS_DEPTH = 3
ALGORITHM_NAME = "Minimax"


class ClickThroughImage(Image):
    def on_touch_down(self, touch):
        return False

    def on_touch_move(self, touch):
        return False

    def on_touch_up(self, touch):
        return False


class Section(BoxLayout):
    def __init__(self, title: str, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, spacing=2, **kwargs)
        self._title = Label(
            text=title,
            bold=True,
            font_size="13sp",
            color=(0.55, 0.78, 1.0, 1.0),
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        self._value = Label(
            text="-",
            font_size="16sp",
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        for lbl in (self._title, self._value):
            lbl.bind(width=lambda l, w: setattr(l, "text_size", (w, None)))
            lbl.bind(texture_size=lambda l, ts: setattr(l, "height", ts[1] + dp(2)))
            self.add_widget(lbl)
        self.bind(minimum_height=self.setter("height"))

    def set(self, text: str):
        self._value.text = text


class AnalyticsPanel(ScrollView):
    def __init__(self, algorithm: str = ALGORITHM_NAME, **kwargs):
        super().__init__(**kwargs)
        self._algorithm = algorithm

        box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(10),
            spacing=dp(8),
        )
        box.bind(minimum_height=box.setter("height"))
        self.add_widget(box)

        self._position = Section("Current Board Position")
        self._turn = Section("Side to Move")
        self._pieces = Section("Pieces")
        self._moves = Section("Possible Moves")
        self._best = Section("Best Move")
        self._eval = Section("Board Evaluation")
        self._depth = Section("Search Depth")
        self._algo = Section("Algorithm Used")

        box.add_widget(self._heading("INPUT"))
        for s in (self._position, self._turn, self._pieces, self._moves):
            box.add_widget(s)
        box.add_widget(self._heading("OUTPUT"))
        for s in (self._best, self._eval, self._depth, self._algo):
            box.add_widget(s)

        self._algo.set(self._algorithm)

    @staticmethod
    def _heading(text: str) -> Label:
        return Label(
            text=text, bold=True, font_size="18sp", size_hint_y=None, height=dp(30)
        )

    @staticmethod
    def _format_move(board: chess.Board, move: chess.Move) -> str:
        piece = board.piece_at(move.from_square)
        name = PIECE_NAMES[piece.piece_type] if piece else "Piece"
        src = chess.square_name(move.from_square).upper()
        dst = chess.square_name(move.to_square).upper()
        promo = f" = {PIECE_NAMES[move.promotion]}" if move.promotion else ""
        return f"{name} -> {dst}{promo}  ({src} -> {dst})"

    @staticmethod
    def _format_eval(value: float) -> str:
        if math.isinf(value):
            return "Forced mate (+)" if value > 0 else "Forced mate (-)"
        return f"{value:+.1f}"

    def show_position(self, board: chess.Board):
        side = "White" if board.turn == chess.WHITE else "Black"
        self._position.set(board.fen())
        self._turn.set(f"{side} to Move")
        self._pieces.set(
            "\n".join(
                f"{PIECE_NAMES[pt]}: {len(board.pieces(pt, chess.WHITE))}"
                for pt in PIECE_ORDER
            )
        )
        self._moves.set(str(board.legal_moves.count()))

    def show_thinking(self):
        self._best.set("Analyzing...")
        self._eval.set("Analyzing...")
        self._depth.set(str(ANALYSIS_DEPTH))

    def show_waiting(self):
        self._turn.set("Black to Move (AI)")
        self._best.set("-")
        self._eval.set("-")

    def show_game_over(self):
        self._best.set("Game over")
        self._eval.set("-")

    def show_analysis(self, board: chess.Board, analysis: Analysis):
        if analysis.best_move is None:
            self._best.set("No legal moves")
        else:
            self._best.set(self._format_move(board, analysis.best_move))
        self._eval.set(self._format_eval(analysis.evaluation))
        self._moves.set(str(analysis.possible_moves))
        self._depth.set(str(analysis.search_depth))
        self._algo.set(self._algorithm)


class BoardGrid(GridLayout):
    LIGHT_COLOR = (0.65, 0.65, 0.65, 1.0)
    DARK_COLOR = (0.35, 0.35, 0.35, 1.0)
    SELECTED_COLOR = (0.0, 0.8, 0.0, 1.0)
    TARGET_COLOR = (0.8, 0.8, 0.0, 1.0)
    CHECK_COLOR = (1.0, 0.0, 0.0, 1.0)

    def __init__(self, status: Label, panel: AnalyticsPanel, **kwargs):
        super().__init__(**kwargs)
        self.cols = 8
        self.rows = 8

        self._status = status
        self._panel = panel
        self._board = Board()
        self._ai = MinimaxAI(depth=3)
        self._analyzer = MinimaxAI(depth=ANALYSIS_DEPTH)
        self._analysis_id = 0
        self._selected = None
        self._last_ai_move = None
        self._busy = False
        self._buttons: dict[int, Button] = {}
        self._images: dict[int, Image] = {}

        self._build_board()
        self._refresh()
        self._request_analysis()

    def _build_board(self):
        for i in range(8):
            for j in range(8):
                square = chess.square(j, 7 - i)

                cell = RelativeLayout()

                btr = Button(
                    background_normal="",
                    background_down="",
                    background_color=self._cell_color(square),
                )
                btr.bind(on_press=lambda b, s=square: self._on_press(s))

                img = ClickThroughImage(
                    source="",
                    fit_mode="contain",
                    size_hint=(0.85, 0.85),
                    pos_hint={"center_x": 0.5, "center_y": 0.5},
                    opacity=0,
                )

                cell.add_widget(btr)
                cell.add_widget(img)

                self._buttons[square] = btr
                self._images[square] = img
                self.add_widget(cell)

    def _cell_color(self, square: int):
        if (chess.square_file(square) + chess.square_rank(square)) % 2 == 0:
            return self.DARK_COLOR
        return self.LIGHT_COLOR

    def _refresh(self):
        targets = set()
        if self._selected is not None:
            targets = {
                m.to_square for m in self._board.legal_moves_from(self._selected)
            }

        for square, btr in self._buttons.items():
            piece = self._board.piece_at(square)
            img = self._images[square]

            if piece:
                img.source = PIECE_IMAGES[piece.symbol()]
                img.opacity = 1
            else:
                img.source = ""
                img.opacity = 0

            if square == self._selected:
                btr.background_color = self.SELECTED_COLOR
            elif (
                piece
                and piece.piece_type == chess.KING
                and self._board.is_check()
                and self._board.turn == piece.color
            ):
                btr.background_color = self.CHECK_COLOR
            elif square in targets:
                btr.background_color = self.TARGET_COLOR
            elif self._last_ai_move and square == self._last_ai_move.to_square:
                btr.background_color = self.TARGET_COLOR
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

    def _request_analysis(self):
        snapshot = self._board.raw.copy()
        self._analysis_id += 1
        job = self._analysis_id

        self._panel.show_position(snapshot)
        if snapshot.is_game_over():
            self._panel.show_game_over()
            return

        self._panel.show_thinking()
        threading.Thread(
            target=self._analyze, args=(snapshot, job), daemon=True
        ).start()

    def _analyze(self, snapshot: chess.Board, job: int):
        analysis = self._analyzer.best_move(snapshot)
        Clock.schedule_once(lambda dt: self._apply_analysis(snapshot, analysis, job))

    def _apply_analysis(self, snapshot: chess.Board, analysis: Analysis, job: int):
        if job != self._analysis_id:
            return
        self._panel.show_analysis(snapshot, analysis)

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
        self._last_ai_move = None
        self._analysis_id += 1

        if self._board.is_game_over():
            self._refresh()
            self._request_analysis()
            return

        self._busy = True
        self._panel.show_waiting()
        self._refresh()
        threading.Thread(target=self._think, daemon=True).start()

    def _think(self):
        move = self._ai.best_move(self._board.raw).best_move
        Clock.schedule_once(lambda dt: self._apply_ai_move(move))

    def _apply_ai_move(self, move: chess.Move | None):
        if move is not None:
            self._board.push(move)
            self._last_ai_move = move
        self._busy = False
        self._refresh()
        self._request_analysis()


class ChesserApp(App):
    def build(self):
        root = BoxLayout(orientation="horizontal")

        left = BoxLayout(orientation="vertical")
        status = Label(size_hint_y=0.08)
        panel = AnalyticsPanel()
        left.add_widget(status)
        left.add_widget(BoardGrid(status, panel))

        splitter = Splitter(
            sizable_from="left",
            size_hint_x=None,
            width=dp(320),
            min_size=dp(200),
            max_size=dp(700),
        )
        splitter.add_widget(panel)

        root.add_widget(left)
        root.add_widget(splitter)
        return root


if __name__ == "__main__":
    ChesserApp().run()

