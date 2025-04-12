import chess
import chess.engine
from display import ChessOLED
import time 
class AIChess:
    def __init__(self, engine_path=r"/usr/games/stockfish"):
        oled = ChessOLED()
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.board = None

    def set_position(self, fen):
        self.board = chess.Board(fen)

    def is_checkmate(self):
        """Check if the current board state is a checkmate."""
        return self.board.is_checkmate()

    def is_stalemate(self):
        """Check if the current board state is a stalemate."""
        return self.board.is_stalemate()

    def close_engine(self):
        self.engine.quit()
        
    def get_ai_move(self, difficulty = "medium") -> list[str]:
        oled = ChessOLED()
        """Return [from_sq, to_sq] and transparently restart Stockfish if it crashed."""
        # --- choose a time limit from the difficulty string ------------------------
        time_limit = {"easy": 0.5, "medium": 1.0, "hard": 3.0}.get(difficulty, 1.0)
        limit      = chess.engine.Limit(time=time_limit)

        for attempt in (1, 6):
            try:
                result = self.engine.play(self.board, limit)
                uci    = result.move.uci()           
                return [uci[:2], uci[2:4]]          
            except (chess.engine.EngineTerminatedError, BrokenPipeError):
                oled.display("Stockfish Failed", f"Attempt {1}")
                time.sleep(10)
                if attempt == 6:
                    oled.display("Unfortunately", "All Failed")
                    time.sleep(10)                    
                    raise RuntimeError("Stockfish crashed 6 in a row")
                # -------- restart the engine and retry  ------------------------
                try:
                    self.engine.quit()
                except Exception:
                    pass                             
                self.engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")
