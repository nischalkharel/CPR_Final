import json
from ai_chess import AIChess
from chessboard import ChessSetupChecker
import busio
import board
import os
import lgpio
import time
import shutil
from arm import pick_place_from_to, open_gripper, go_rest
from speaker import play_sound
from display import ChessOLED 
from move_logic import validate_move_input
import sys

i2c = busio.I2C(board.SCL, board.SDA)
setup_checker = ChessSetupChecker(i2c)
WHITE_BUTTON_PIN = 17
BLACK_BUTTON_PIN = 27

# Open GPIO chip (chip 4 is standard for Raspberry Pi 5)
h = lgpio.gpiochip_open(4)



# Set pins as input with pull-up resistors
lgpio.gpio_claim_input(h, WHITE_BUTTON_PIN, lgpio.SET_PULL_UP)
lgpio.gpio_claim_input(h, BLACK_BUTTON_PIN, lgpio.SET_PULL_UP)

oled = ChessOLED()


def wait_buttons(position_to_check = "", turn = 0, hold = False):
    prev_state = ""
    hold_timer_start = None

    while True:
        white_state = lgpio.gpio_read(h, WHITE_BUTTON_PIN)
        black_state = lgpio.gpio_read(h, BLACK_BUTTON_PIN)

        # -- Position check for OLED --
        if position_to_check != "":
            current_state = setup_checker.check(position_to_check)
            if prev_state != current_state:
                oled.display(f"{position_to_check} is", f"{current_state}")
                prev_state = current_state

        # -- Display board state if it's the player's turn --
        if turn:
            changed_squares = setup_checker.currentVSprevious_board_states()
            line1, line2 = "", ""
            for i, (position, piece) in enumerate(changed_squares.items()):
                if i >= 2:
                    break
                if piece == "empty":
                    line1 = f"{position}: empty"
                else:
                    line2 = f"{position}: piece"
            oled.display(line1 or "Your Turn", line2 or "Make a move")

        # -- Check if both buttons are pressed --
        if white_state == 0 and black_state == 0:
            print("HOLDING")
            if hold:
                while white_state == 0 or black_state == 0:
                    white_state = lgpio.gpio_read(h, WHITE_BUTTON_PIN)
                    black_state = lgpio.gpio_read(h, WHITE_BUTTON_PIN)
                    time.sleep(.03)
                return "both pressed"
            if hold_timer_start is None:
                hold_timer_start = time.time()
            elif time.time() - hold_timer_start >= 10:
                return possible_restart()
            oled("Holding for",f"{time.time()-hold_timer_start} s")
            print("HOLDING")
            time.sleep(.1)
        else:
            hold_timer_start = None  # Reset if released

        # -- Single button press handling --
        if white_state == 0 and hold == False:
            while white_state == 0:
                white_state = lgpio.gpio_read(h, WHITE_BUTTON_PIN)
                time.sleep(.03)
            return "white_button_pressed"

        if black_state == 0 and hold == False:
            while black_state == 0:
                black_state = lgpio.gpio_read(h, BLACK_BUTTON_PIN)
                time.sleep(.03)
            return "black_button_pressed"

def possible_restart():
    oled.display("Want to", "Restart?")
    while True:
        white_state = lgpio.gpio_read(h, WHITE_BUTTON_PIN)
        black_state = lgpio.gpio_read(h, BLACK_BUTTON_PIN)

        if white_state == 0:
            oled.display("Restarting", "Please wait...")
            time.sleep(1)
            os.execv(sys.executable, ['python3'] + sys.argv)  # Restart program

        if black_state == 0:
            oled.display("Canceled", "Resuming game")
            time.sleep(1)
            return "continue"

        time.sleep(0.05)

def check_initial_setup():
    # Expected initial setup for a chessboard
    expected_positions = {
        "a1": "black_rook", "b1": "black_knight", "c1": "black_bishop", "d1": "black_king",
        "e1": "black_queen", "f1": "black_bishop", "g1": "black_knight", "h1": "black_rook",
        "a2": "black_pawn", "b2": "black_pawn", "c2": "black_pawn", "d2": "black_pawn",
        "e2": "black_pawn", "f2": "black_pawn", "g2": "black_pawn", "h2": "black_pawn",
        "a7": "white_pawn", "b7": "white_pawn", "c7": "white_pawn", "d7": "white_pawn",
        "e7": "white_pawn", "f7": "white_pawn", "g7": "white_pawn", "h7": "white_pawn",
        "a8": "white_rook", "b8": "white_knight", "c8": "white_bishop", "d8": "white_king",
        "e8": "white_queen", "f8": "white_bishop", "g8": "white_knight", "h8": "white_rook"
    }

    while True:
        setup_checker.generate_initial_chess_setup()
        try:
            # Open and read the JSON file
            with open("chessboard.json", "r") as file:
                board_state = json.load(file)

            # Check for missing or incorrect spots
            incorrect_spots = []
            for position, expected_piece in expected_positions.items():
                if position not in board_state or board_state[position] != expected_piece:
                    incorrect_spots.append(position)

            # Check for unexpected pieces in empty spots
            for position in board_state:
                if position not in expected_positions and board_state[position] != "empty":
                    incorrect_spots.append(position)

            if not incorrect_spots:
                return True
            else:
                print("The following spots do not meet the initial setup requirements:")
                for spot in incorrect_spots:
                    print(f"- {spot}: Expected '{expected_positions.get(spot, 'empty')}', Found '{board_state.get(spot, 'missing')}')")

        except FileNotFoundError:
            print("Error: chessboard.json file not found. Please ensure the file exists in the same directory.")
            return False
        except json.JSONDecodeError:
            print("Error: chessboard.json file is not a valid JSON file. Please check its contents.")
            return False

        input("Press Enter to retry...")

def handle_human_turn():
    
    # Make a copy of the current board to pre_turn_board.json
    shutil.copy("chessboard.json", "pre_turn_board.json")
    
    # Open or create chess_board_incomplete.json with the current board state
    with open("pre_turn_board.json", "r") as file:
        board_state = json.load(file)

    manage_game_details("white",difficulty, read = 0)
    pre_board_for_validation = board_state

    oled.display("Your Turn","Make a move")
    play_sound("WhiteTurn", block=True)
    captured = 0
    # Continuously check for changes in progress board
    while True:
        oled.display("Your Turn","Make a move")
        play_sound("press_afterMove", block=True)
        time.sleep(1)
        button_pressed = wait_buttons(turn = 1)
        if(button_pressed == "black_button_pressed"):
            continue
        
        changed_squares = setup_checker.currentVSprevious_board_states()

        if len(changed_squares) == 1:
            play_sound("one_changed", block=True)
            square = ""
            for position, piece in changed_squares.items():
                print(position)
                oled.display("Removed From",f"{position}")
                play_sound(f"{position}", block = True)
                square = position
                

            play_sound("pressWhite_Black", block=True)
            button_pressed = wait_buttons(square)
            if(button_pressed == "black_button_pressed"):
                print("\nReset and try again!\n")
                continue
            
            positions = list(changed_squares.keys())
            board_state[positions[0]]= "empty"

            # Save the updated state back to the file
            with open("pre_turn_board.json", 'w') as file:
                json.dump(board_state, file, indent=4)
            captured = 1
            continue
        elif len(changed_squares) == 2:
            
            
            for position, piece in changed_squares.items():
                if(changed_squares.get(position) == "empty"):
                    from_position = position
                else:
                    to_position = position
            oled.display(f"Moved {board_state[from_position]}:",f"{from_position} to {to_position}", f"{board_state[from_position]}")    
            play_sound("recorded_move_from", block=True)
            play_sound(from_position, block=True)
            play_sound("to", block = True)
            play_sound(to_position, block= True)
            
            for position, piece in changed_squares.items():
                print(position)
            
            play_sound("pressWhite_Black", block=False)
            button_pressed = wait_buttons()
            if(not(validate_move_input(pre_board_for_validation, from_position, to_position, captured)[0])):
                button_pressed = "black_button_pressed"
                time.sleep(5)
            time.sleep(.5)
            if(button_pressed == "black_button_pressed"):
                print("\nReset and try again!\n")
                continue
        elif len(changed_squares) == 0:
            oled.display("No Changes", "Dectected!")
            play_sound("pressWhite_Black", block=True)
            continue
            
        else:
            oled.display("Multiple Changes", "Dectected!")
            play_sound("multiple_changed", block=True)
            play_sound("pressWhite_Black", block=True)
            for position, piece in changed_squares.items():
                play_sound(f"{position}", block=True)
                button_pressed = wait_buttons(position)
            continue

        for position, piece in changed_squares.items():
            if(changed_squares.get(position) == "empty"):
                from_position = position
            else:
                to_position = position
      


        swap_pieces_in_file("pre_turn_board.json","chessboard.json", from_position, to_position)
        
        ### VALIDATION CHECK HERE ###
        
        return

def handle_bot_turn(difficulty = "easy"):
    shutil.copy("chessboard.json", "pre_turn_board.json")
    with open("pre_turn_board.json", "r") as file:
        board_state = json.load(file)
    
    oled.display("Arm's", "Turn")
    play_sound("BlackTurn", block=True)
    manage_game_details("black",difficulty, read = 0)

    ai_move = get_ai_move(difficulty)
    ai_move[0] = engine_to_physical(ai_move[0])
    ai_move[1] = engine_to_physical(ai_move[1])
    print(f"{ai_move[0]}")
    print(f"{ai_move[1]}")
    oled.display("Arm will Move:", f"{ai_move[0]} to {ai_move[1]}", f"{board_state[ai_move[0]]}")
    if(board_state[ai_move[1]] != "empty"): #make sure "to" position is empty
        emptied = False
        arm_move(ai_move[1], "out") 
        while(not(emptied)):
            changed_squares = setup_checker.currentVSprevious_board_states()
            if(changed_squares.get(ai_move[1]) == "empty"):
                board_state[ai_move[1]]= "empty"

                # Save the updated state back to the file
                with open("pre_turn_board.json", 'w') as file:
                    json.dump(board_state, file, indent=4)
                emptied = True
            else:
                play_sound("trying_empty", block=True)
                play_sound(f"{ai_move[1]}", block = True)
                play_sound("help_ask", block=False)
                button = wait_buttons(ai_move[1])
                continue
            
            
    with open("pre_turn_board.json", "r") as file:
        board_state = json.load(file)
        
    arm_move(ai_move[0], ai_move[1])
    arm_not_done = True
    while(arm_not_done):
        changed_squares = setup_checker.currentVSprevious_board_states()
        to_square = False #only true if we have made sure there is a piece here
        from_square = False #only true if its empty now
        all_good = True
        for position, piece in changed_squares.items():
            if(position == ai_move[0]) and (piece == "empty"):
                print("empty")
                from_square = True
            
            if(position == ai_move[1]) and (piece == "piece"):
                print("piece")
                to_square = True
                
            if(position != ai_move[0]) and (position != ai_move[1]):
                speak(f"can you please help me fix {position}")
                play_sound("something_messed", block=True)
                play_sound(f"{position}", block = True)
                button_pressed = wait_buttons(position)
                all_good = False
                break
            if(position == ai_move[1]) and (piece == "empty"):
                play_sound("something_messed", block=True)
                play_sound(f"{position}", block = True)
                button_pressed = wait_buttons(position)
                all_good = False
                break
                
        if not(all_good):
            continue        
        if not(from_square) or not(to_square):
            oled.display("check:", f"{ai_move[0]} and {ai_move[1]}")
            play_sound("something_messed", block=True)
            #play_sound("trying_to_move", block = True)
            #play_sound(board_state[ai_move[0]], block = True)
            #play_sound("from", block = True)
            #play_sound(f"{ai_move[0]}", block = True)
            #play_sound("to", block = True)
            #play_sound(f"{ai_move[1]}", block = True)
            #play_sound("help_ask", block=False)
            button = wait_buttons(ai_move[1])
            continue
                
        arm_not_done = False
    oled.display("Arm Moved:", f"{ai_move[0]} to {ai_move[1]}", board_state[ai_move[0]])
    swap_pieces_in_file("pre_turn_board.json","chessboard.json", ai_move[0], ai_move[1])
    play_sound("black_done", block=True)
    go_rest()
  
def get_ai_move(difficulty = "easy"):
    # Load the chess board
    with open("chessboard.json", "r") as file:
        board_state = json.load(file)
    fen_string = chessboard_to_fen(rotate_board(board_state), ai_color="black")
    print(f"Generated FEN: {fen_string}")

    # Initialize AIChess engine
    ai = AIChess(engine_path=os.getenv('STOCKFISH_PATH', '/usr/games/stockfish'))
    ai.set_position(fen_string)
    
    # Get the next move
    next_move = ai.get_ai_move(difficulty)
    print(f"{difficulty} AI recommends move: {next_move[0]}{next_move[1]}")
    ai.close_engine()
    return next_move

def arm_move(pos_from, pos_to):
    #INTEGRATE THE ARM MOVEMENT HERE
    print(f"arm moving from {pos_from} to {pos_to}")
    open_gripper()
    pick_place_from_to("pickup",pos_from)
    pick_place_from_to("placedown", pos_to)
    

def chessboard_to_fen(board_state,ai_color = "black"):
    rows = []
    for rank in range(8, 0, -1):
        row = ""
        empty_count = 0
        for file in "abcdefgh":
            square = f"{file}{rank}"
            piece = board_state.get(square, "empty")

            if piece == "empty":
                empty_count += 1
            else:
                if empty_count > 0:
                    row += str(empty_count)
                    empty_count = 0
                row += piece_to_fen(piece)

        if empty_count > 0:
            row += str(empty_count)
        rows.append(row)

    turn = "w" if ai_color == "white" else "b"
    fen = "/".join(rows) + f" {turn} - - 0 1"
    return fen


def piece_to_fen(piece):
    mapping = {
        "white_pawn": "P", "white_rook": "R", "white_knight": "N", "white_bishop": "B",
        "white_queen": "Q", "white_king": "K",
        "black_pawn": "p", "black_rook": "r", "black_knight": "n", "black_bishop": "b",
        "black_queen": "q", "black_king": "k"
    }
    return mapping.get(piece, "")


def is_checkmate_or_stalemate(board_state, player_color):
    """Check for checkmate or stalemate using AIChess."""
    fen_string = chessboard_to_fen(board_state,player_color)
    ai = AIChess(engine_path=os.getenv('STOCKFISH_PATH', '/usr/games/stockfish'))
    ai.set_position(fen_string)
    
    if ai.is_checkmate():
        print("Checkmate!")
        play_sound("checkmate", block=False)
        ai.close_engine()
        return True
    elif ai.is_stalemate():
        print("Stalemate!")
        play_sound("draw", block=False)
        ai.close_engine()
        return True
    
    ai.close_engine()
    return False
def swap_pieces_in_file(file_path_from,file_path_to, position1, position2):
    # Load the JSON data from file
    with open(file_path_from, 'r') as file:
        board_state = json.load(file)

    # Swap the pieces
    board_state[position1], board_state[position2] = board_state[position2], board_state[position1]

    # Save the updated state back to the file
    with open(file_path_to, 'w') as file:
        json.dump(board_state, file, indent=4)

def speak(message):
    print(message)

def rotate_board(board_dict: dict) -> dict:
    """Return a new dict with ranks (and optionally files) flipped."""
    new_board = {}
    for square, piece in board_dict.items():
        f, r = square[0], int(square[1])
        new_square = f"{f}{9 - r}"     # 1 ↔ 8, 2 ↔ 7, …
        new_board[new_square] = piece
    return new_board
    

def engine_to_physical(pos):
    return f"{pos[0]}{9-int(pos[1])}"

def manage_game_details(turn = "black", difficulty = "easy", read=0):
    filename = "previous_game_details.json"
    
    if read == 1:
        if os.path.exists(filename):
            with open(filename, "r") as file:
                try:
                    details = json.load(file)
                    return [details.get("Turn", ""), details.get("Difficulty", "")]
                except json.JSONDecodeError:
                    oled.display("No Saved", "Game")
                    return ["none", "none"]
        else:
            return []
    else:
        details = {"Turn": turn, "Difficulty": difficulty}
        with open(filename, "w") as file:
            json.dump(details, file)

def piece(piece):
    play_sound(f"{piece[:6]}", block=True)
    play_sound(f"{piece[6:]}", block = True)

if __name__ == "__main__":
    oled.display("Arm", "Starting")
    go_rest()
    oled.display("Hold Buttons", "To Start")
    play_sound("hold_both_buttons_to_start", block = True)
    hold = wait_buttons(hold = True)

    oled.display("Select", "Game Mode")
    difficulty = ""
    resume_game = 0
    play_sound("choose_difficulty", block=True)
    
    while(1):
        pressed = wait_buttons()
        if(pressed == "black_button_pressed"):
            match difficulty:
                case "easy":
                    oled.display("Medium", "Mode")
                    difficulty = "medium"
                    play_sound("medium_mode", block = True)
                case "medium":
                    oled.display("Hard", "Mode")
                    difficulty = "hard"
                    play_sound("hard_mode", block = True)
                case "hard":
                    oled.display("Resume", "Match")
                    difficulty = "resume_previous_match"
                    play_sound("resume_previous_match", block = True)
                case _:
                    oled.display("Easy", "Mode")
                    difficulty = "easy"
                    play_sound("easy_mode", block = True)
        elif(pressed == "white_button_pressed" and difficulty != ""):
            if(difficulty == "resume_previous_match"):
                play_sound("lets_start_from_where_we_left_off", block=True)
                play_sound("place_pieces", block = True)
                game_details = manage_game_details(read = 1)
                if(game_details[0] == "none"):
                    oled.display("no previous","game saved")
                with open("pre_turn_board.json", "r") as file:
                    board_state = json.load(file)
    
                for position, expected_piece in board_state.items():
                    if expected_piece != "empty":
                        oled.display(f"{expected_piece} in", f"{position}")
                        pressed = wait_buttons()
                        if(setup_checker.check(position) == "empty"):
                            press_again = wait_buttons(position_to_check=position)
                everything_good = 0
                while(not(everything_good)):
                    everything_good = 1
                    for position, expected_piece in board_state.items():
                        if expected_piece == "empty" and setup_checker.check(position) != "empty":
                            everything_good = 0
                            oled.display(f"{position} should", "be empty")
                            pressed = wait_buttons()
                            if(setup_checker.check(position) != "empty"):
                                press_again = wait_buttons(position_to_check=position)
                        elif expected_piece != "empty" and setup_checker.check(position) == "empty":
                            everything_good = 0
                            oled.display(f"{expected_piece}", f"{position}")
                            pressed = wait_buttons()
                            if(setup_checker.check(position) == "empty"):
                                press_again = wait_buttons(position_to_check=position)
                oled.display("Checks Completed", "Starting the Game")
                play_sound("initial_checks_over", block=True)
                if(game_details[0] == "black"):
                    print("\nBlack's turn.")
                    handle_bot_turn(game_details[1])
                    if is_checkmate_or_stalemate(json.load(open("chessboard.json")), "w"):
                         break
                else:
                    print("\nWhite's turn.")
                    handle_human_turn()
                    if is_checkmate_or_stalemate(json.load(open("chessboard.json")), "b"):
                        break
                    print("\nBlack's turn.")
                    handle_bot_turn(game_details[1])
                    if is_checkmate_or_stalemate(json.load(open("chessboard.json")), "w"):
                        break     
                while True:
                    print("\nWhite's turn.")
                    handle_human_turn()
                    if is_checkmate_or_stalemate(json.load(open("chessboard.json")), "b"):
                         break
                    print("\nBlack's turn.")
                    handle_bot_turn(game_details[1])
                    if is_checkmate_or_stalemate(json.load(open("chessboard.json")), "w"):
                         break

            else:
                oled.display("Initial Checks", "Starting")
                play_sound("initial_checks", block=True)
                if check_initial_setup():
                    print("Initial checks are completed correctly.")
                    oled.display("Checks Completed", "Starting the Game")
                    play_sound("initial_checks_over", block=True)
                    while True:
                        print("\nWhite's turn.")
                        handle_human_turn()
                        if is_checkmate_or_stalemate(json.load(open("chessboard.json")), "b"):
                            break
                        print("\nBlack's turn.")
                        handle_bot_turn(difficulty)
                        if is_checkmate_or_stalemate(json.load(open("chessboard.json")), "w"):
                            break
                else:
                    print("Initial check failed.")



    
