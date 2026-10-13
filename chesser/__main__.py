import math
import re
import sys
import threading
import readline

import chess

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

PIECE_LOOKUP = {name.lower(): pt for pt, name in PIECE_NAMES.items()}
PIECE_LETTERS = {
    "k": chess.KING,
    "q": chess.QUEEN,
    "r": chess.ROOK,
    "n": chess.KNIGHT,
    "b": chess.BISHOP,
    "p": chess.PAWN,
}
PROMOTIONS = {
    "q": chess.QUEEN,
    "r": chess.ROOK,
    "b": chess.BISHOP,
    "n": chess.KNIGHT,
}

ANALYSIS_DEPTH = 3
AI_DEPTH = 3
ALGORITHM_NAME = "Minimax"

COMPACT_MOVE = re.compile(r"^([a-h][1-8])([a-h][1-8])([qrbn]?)$")
SQUARE = re.compile(r"^[a-h][1-8]$")


def format_move(board: chess.Board, move: chess.Move) -> str:
    piece = board.piece_at(move.from_square)
    name = PIECE_NAMES[piece.piece_type] if piece else "Piece"
    src = chess.square_name(move.from_square).upper()
    dst = chess.square_name(move.to_square).upper()
    promo = f" = {PIECE_NAMES[move.promotion]}" if move.promotion else ""
    return f"{name} -> {dst}{promo}  ({src} -> {dst})"


def format_eval(value: float) -> str:
    if math.isinf(value):
        return "Forced mate (+)" if value > 0 else "Forced mate (-)"
    return f"{value:+.1f}"


def pieces_summary(board: chess.Board) -> str:
    return "\n".join(
        f"{PIECE_NAMES[pt]}: {len(board.pieces(pt, chess.WHITE))}"
        for pt in PIECE_ORDER
    )


def side_label(board: chess.Board) -> str:
    return "White to Move" if board.turn == chess.WHITE else "Black to Move"


def game_status(board: chess.Board) -> str | None:
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        return f"Checkmate - {winner} wins"
    if board.is_game_over():
        return "Draw"
    return None


def render_board(board: chess.Board) -> str:
    rows = []
    for rank in range(7, -1, -1):
        cells = []
        for file in range(8):
            piece = board.piece_at(chess.square(file, rank))
            cells.append(piece.symbol() if piece else ".")
        rows.append(f"{rank + 1}  " + " ".join(cells))
    rows.append("")
    rows.append("   " + " ".join("abcdefgh"))
    return "\n".join(rows)


def parse_player_move(board: chess.Board, text: str):
    cleaned = text.strip().lower()
    for token in ("->", "-", ","):
        cleaned = cleaned.replace(token, " ")
    parts = [p for p in cleaned.split() if p != "to"]
    if not parts:
        return None, "Enter a move such as 'e2 e4' or 'pawn e2 e4'."

    piece_type = None
    first = parts[0]
    if first in PIECE_LOOKUP:
        piece_type = PIECE_LOOKUP[first]
        parts = parts[1:]
    elif len(first) == 1 and first in PIECE_LETTERS and len(parts) > 1:
        piece_type = PIECE_LETTERS[first]
        parts = parts[1:]

    promotion = None
    if len(parts) == 1:
        match = COMPACT_MOVE.match(parts[0])
        if not match:
            return None, "Could not read that move. Use 'e2 e4' or 'knight g1 f3'."
        src_name, dst_name, promo_letter = match.groups()
        promotion = PROMOTIONS.get(promo_letter)
    elif len(parts) in (2, 3):
        src_name, dst_name = parts[0], parts[1]
        if not (SQUARE.match(src_name) and SQUARE.match(dst_name)):
            return None, "Squares must look like e2 or f3."
        if len(parts) == 3:
            word = parts[2]
            promotion = PIECE_LOOKUP.get(word) or PROMOTIONS.get(word)
            if promotion not in PROMOTIONS.values():
                return None, "Promotion must be queen, rook, bishop or knight."
    else:
        return None, "Could not read that move. Use 'e2 e4' or 'knight g1 f3'."

    src = chess.parse_square(src_name)
    dst = chess.parse_square(dst_name)
    piece = board.piece_at(src)

    if piece is None:
        return None, f"There is no piece on {src_name.upper()}."
    if piece.color != chess.WHITE:
        return None, f"The piece on {src_name.upper()} is not yours."
    if piece_type is not None and piece.piece_type != piece_type:
        actual = PIECE_NAMES[piece.piece_type]
        wanted = PIECE_NAMES[piece_type]
        return None, f"The piece on {src_name.upper()} is a {actual}, not a {wanted}."

    for move in board.legal_moves:
        if move.from_square != src or move.to_square != dst:
            continue
        if move.promotion:
            if move.promotion != (promotion or chess.QUEEN):
                continue
        elif promotion is not None:
            continue
        return move, ""

    name = PIECE_NAMES[piece.piece_type]
    return None, f"{name} {src_name.upper()} -> {dst_name.upper()} is not a legal move."


def print_analytics(board: chess.Board, analysis: Analysis | None, note: str = "-"):
    print()
    print("=" * 44)
    print("INPUT")
    print("-" * 44)
    print("Current Board Position")
    print(f"  {board.fen()}")
    print(side_label(board))
    print()
    print("Pieces")
    for line in pieces_summary(board).splitlines():
        print(f"  {line}")
    print()
    print("Possible Moves")
    print(f"  {board.legal_moves.count()}")
    print()
    print("OUTPUT")
    print("-" * 44)
    print("Best Move")
    if analysis is None:
        print(f"  {note}")
        print("Board Evaluation")
        print("  -")
        print("Search Depth")
        print(f"  {ANALYSIS_DEPTH}")
    else:
        if analysis.best_move is None:
            print("  No legal moves")
        else:
            print(f"  {format_move(board, analysis.best_move)}")
        print("Board Evaluation")
        print(f"  {format_eval(analysis.evaluation)}")
        print("Search Depth")
        print(f"  {analysis.search_depth}")
    print(f"Algorithm Used: {ALGORITHM_NAME}")
    print("=" * 44)


def print_help():
    print("Commands:")
    print("  e2 e4              move the piece on E2 to E4")
    print("  pawn e2 e4         same, checking that E2 holds a pawn")
    print("  knight g1 f3       piece name, from square, to square")
    print("  e7 e8 queen        promotion (queen is the default)")
    print("  board              show the board again")
    print("  help               show this help")
    print("  quit               leave the game")


def run_terminal():
    board = Board()
    ai = MinimaxAI(depth=AI_DEPTH)
    analyzer = MinimaxAI(depth=ANALYSIS_DEPTH)

    print("Chesser - terminal mode. You play White. Type 'help' for commands.")

    while True:
        raw = board.raw
        print()
        print(render_board(raw))

        over = game_status(raw)
        if over:
            print_analytics(raw, None, "Game over")
            print()
            print(over)
            return

        if raw.is_check():
            print("\nYou are in check.")

        print("\nAnalyzing...")
        analysis = analyzer.best_move(raw.copy())
        print_analytics(raw, analysis)

        move = None
        while move is None:
            try:
                text = input("\nYour move> ")
            except (EOFError, KeyboardInterrupt):
                print()
                return

            command = text.strip().lower()
            if command in ("quit", "exit", "q"):
                return
            if command in ("help", "?", "h"):
                print_help()
                continue
            if command in ("board", "b"):
                print()
                print(render_board(board.raw))
                continue

            move, error = parse_player_move(board.raw, text)
            if move is None:
                print(error)

        print(f"You played: {format_move(board.raw, move)}")
        board.push(move)

        over = game_status(board.raw)
        if over:
            print()
            print(render_board(board.raw))
            print()
            print(over)
            return

        print("\nAI is thinking...")
        ai_move = ai.best_move(board.raw.copy()).best_move
        if ai_move is None:
            print()
            print(render_board(board.raw))
            print(game_status(board.raw) or "Draw")
            return
        print(f"AI played: {format_move(board.raw, ai_move)}")
        board.push(ai_move)


def run_gui():
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

    class ClickThroughImage(Image):
        def on_touch_down(self, touch):
            return False

        def on_touch_move(self, touch):
            return False

        def on_touch_up(self, touch):
            return False

    class Section(BoxLayout):
        def __init__(self, title: str, **kwargs):
            super().__init__(
                orientation="vertical", size_hint_y=None, spacing=2, **kwargs
            )
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
                lbl.bind(
                    texture_size=lambda l, ts: setattr(l, "height", ts[1] + dp(2))
                )
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
                text=text,
                bold=True,
                font_size="18sp",
                size_hint_y=None,
                height=dp(30),
            )

        def show_position(self, board: chess.Board):
            self._position.set(board.fen())
            self._turn.set(side_label(board))
            self._pieces.set(pieces_summary(board))
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
                self._best.set(format_move(board, analysis.best_move))
            self._eval.set(format_eval(analysis.evaluation))
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
            self._ai = MinimaxAI(depth=AI_DEPTH)
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
            over = game_status(self._board.raw)
            if over:
                self._status.text = over
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
            Clock.schedule_once(
                lambda dt: self._apply_analysis(snapshot, analysis, job)
            )

        def _apply_analysis(
            self, snapshot: chess.Board, analysis: Analysis, job: int
        ):
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

    ChesserApp().run()


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "term":
        run_terminal()
    else:
        run_gui()


if __name__ == "__main__":
    main()
