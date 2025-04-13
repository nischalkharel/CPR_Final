from speaker import play_sound
from display import ChessOLED

oled = ChessOLED()

def validate_move_input(pre_turn_board, from_move, to_move, captured = 0):
    # Check that there is a piece at the starting square.
    piece = pre_turn_board.get(from_move, "empty")
    if piece == "empty":
        return False, f"No piece found at {from_move}."

    # Build the move dictionary expected by your validate_move() function.
    move = {
        "from": from_move,
        "to": to_move,
        "piece": piece,
        "captured": pre_turn_board.get(to_move, "empty") if pre_turn_board.get(to_move, "empty") != "empty" else None
    }
    
    return validate_move(pre_turn_board, move,captured)

def validate_move(old_chessboard, move, captured):
    
    piece = move["piece"][6:]
    from_square = move["from"]
    to_square = move["to"]
    captured = move.get("captured")

    if from_square == to_square: # THIS SHOULD NOT REALLY HAPPEN BUT JUST IN CASE
        return False, "Piece did not move."

    # Piece-specific validation
    if "pawn" in piece:
        return validate_pawn_move(old_chessboard, move,captured)
    elif "rook" in piece:
        return validate_rook_move(old_chessboard, move, captured)
    elif "knight" in piece:
        return validate_knight_move(old_chessboard, move, captured)
    elif "bishop" in piece:
        return validate_bishop_move(old_chessboard, move, captured)
    elif "queen" in piece:
        return validate_queen_move(old_chessboard, move, captured)
    elif "king" in piece:
        return validate_king_move(old_chessboard, move, captured)

    return False, "Unknown piece type."

############## SPECIFIC PIECE MOVE VALIDATION FUNCTIONS ##############

def validate_pawn_move(old_chessboard, move, captured):
    from_file, from_rank = move["from"][0], int(move["from"][1])
    to_file, to_rank = move["to"][0], int(move["to"][1])
    direction = 1 if "white" in move["piece"][:5] else -1
    start_rank = 7 if "white" in move["piece"][:5] else 2
    
    # Forward move
    if from_file == to_file:
        print("same column")
        if from_rank - to_rank == direction and old_chessboard[move["to"]] == "empty":
            return True, "Valid pawn move."
        # Double move from starting position
        if from_rank == start_rank and from_rank - to_rank == 2 * direction:
            intermediate_square = f"{from_file}{from_rank - direction}"
            if old_chessboard[intermediate_square] == "empty" and old_chessboard[move["to"]] == "empty":
                return True, "Valid double pawn move."

    # Capturing move
    if abs(ord(to_file) - ord(from_file)) == 1 and from_rank - to_rank == direction and captured:
        return True, "Valid pawn capture."

            
    oled.display("Invalid","Pawn Move")
    play_sound("invalid_pawn_move.mp3", block =True)
    return False, "Invalid pawn move."

def validate_rook_move(old_chessboard, move, captured):
    if move["from"][0] == move["to"][0]:  # Moving vertically
        return validate_straight_path(old_chessboard, move, captured, axis="vertical")
    if move["from"][1] == move["to"][1]:  # Moving horizontally
        return validate_straight_path(old_chessboard, move,captured, axis="horizontal")
    
    
    oled.display("Invalid","Rook Move")
    play_sound("invalid_rook_move.mp3", block = True)  
    return False, "Invalid rook move."

def validate_knight_move(old_chessboard, move, captured):
    dx = abs(ord(move["to"][0]) - ord(move["from"][0]))
    dy = abs(int(move["to"][1]) - int(move["from"][1]))
    #L move
    if (dx, dy) in [(1, 2), (2, 1)]:
        return True, "Valid knight move."
    oled.display("Invalid","Knight Move")
    play_sound("invalid_knight_move.mp3", block = True)  
    return False, "Invalid knight move."

def validate_bishop_move(old_chessboard, move, captured):
    dx = abs(ord(move["to"][0]) - ord(move["from"][0]))
    dy = abs(int(move["to"][1]) - int(move["from"][1]))
    if dx == dy:
        return validate_diagonal_path(old_chessboard, move, captured)
    
    oled.display("Invalid","Bisop Move")
    play_sound("invalid_bishop_move.mp3", block = True)  
    return False, "Invalid bishop move."

def validate_queen_move(old_chessboard, move, captured):
    # Queen combines rook and bishop moves
    rook_valid, _ = validate_rook_move(old_chessboard, move, captured)
    bishop_valid, _ = validate_bishop_move(old_chessboard, move, captured)
    if rook_valid or bishop_valid:
        return True, "Valid queen move."

    
    oled.display("Invalid","Queen Move")
    play_sound("invalid_queen_move.mp3", block = True)  
    return False, "Invalid queen move."

def validate_king_move(old_chessboard, move, captured):
    dx = abs(ord(move["to"][0]) - ord(move["from"][0]))
    dy = abs(int(move["to"][1]) - int(move["from"][1]))
    if max(dx, dy) == 1:
        return True, "Valid king move."
    
    oled.display("Invalid","King Move")
    play_sound("invalid_king_move.mp3", block = True)  
    return False, "Invalid king move."


########## PATH VALIDATION FUNCTIONS ##########

# Path validation helpers
def validate_straight_path(old_chessboard, move, captured,axis):
    from_square, to_square = move["from"], move["to"]
    step = 1 if axis == "vertical" else ord(to_square[0]) - ord(from_square[0])

    if axis == "vertical":
        col = from_square[0]
        for row in range(min(int(from_square[1]), int(to_square[1])) + 1, max(int(from_square[1]), int(to_square[1]))):
            if old_chessboard[f"{col}{row}"] != "empty":
                oled.display("Invalid Move","Path Blocked")
                play_sound("invalid_path_blocked.mp3", block = True)  
                return False, "Path is blocked."
    else:  # Horizontal
        row = from_square[1]
        for col in range(min(ord(from_square[0]), ord(to_square[0])) + 1, max(ord(from_square[0]), ord(to_square[0]))):
            if old_chessboard[f"{chr(col)}{row}"] != "empty":
                oled.display("Invalid Move","Path Blocked")
                play_sound("invalid_path_blocked.mp3", block = True)  
                return False, "Path is blocked."

    return True, "Path is clear."

def validate_diagonal_path(old_chessboard, move, captured=0):
    from_file, from_rank = ord(move["from"][0]), int(move["from"][1])
    to_file, to_rank = ord(move["to"][0]), int(move["to"][1])

    file_step = 1 if to_file > from_file else -1
    rank_step = 1 if to_rank > from_rank else -1

    current_file = from_file + file_step
    current_rank = from_rank + rank_step

    while current_file != to_file and current_rank != to_rank:
        if old_chessboard[f"{chr(current_file)}{current_rank}"] != "empty":
            oled.display("Invalid Move","Path Blocked")
            play_sound("invalid_path_blocked.mp3", block = True)  
            return False, "Path is blocked."
        current_file += file_step
        current_rank += rank_step
    
    return True, "Path is clear."


# special moves like castling not implemented due to our board constraint