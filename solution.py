
from utils import *
from enum import Enum


row_units = [cross(r, cols) for r in rows]
column_units = [cross(rows, c) for c in cols]
square_units = [cross(rs, cs) for rs in ('ABC','DEF','GHI') for cs in ('123','456','789')]

# TODO: Update the unit list to add the new diagonal units

diagonal_units = []
diagonal_units.append(['{}{}'.format(r, ir + 1) for ir, r in enumerate(rows)])
diagonal_units.append(['{}{}'.format(r, (9 - ir)) for ir, r in enumerate(rows)])

unitlist = row_units + column_units + square_units + diagonal_units

# Must be called after all units (including diagonals) are added to the unitlist
units = extract_units(unitlist, boxes)
peers = extract_peers(units, boxes)

class UnitType(Enum):
    unknown = 0
    row = 1
    column = 2
    diagonal = 3
    square = 4
    square_row = 5
    square_column = 6
    square_diagonal = 7

def get_box_twin_peer_type(box, peer):
    peer_type = UnitType.unknown

    # row, col, diag are mutually-exclusive
    if len([row for row in row_units if row.count(box) > 0 and row.count(peer) > 0]) > 0:
        peer_type = UnitType.row
    elif len([column for column in column_units if column.count(box) > 0 and column.count(peer) > 0]) > 0:
        peer_type = UnitType.column
    elif len([diagonal for diagonal in diagonal_units if diagonal.count(box) > 0 and diagonal.count(peer) > 0]) > 0:
        peer_type = UnitType.diagonal

    if len([square for square in square_units if square.count(box) > 0 and square.count(peer) > 0]) > 0:
        peer_type = UnitType(peer_type.value + UnitType.square.value)

    return peer_type


def naked_twins(values):
    """Eliminate values using the naked twins strategy.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict
        The values dictionary with the naked twins eliminated from peers

    Notes
    -----
    Your solution can either process all pairs of naked twins from the input once,
    or it can continue processing pairs of naked twins until there are no such
    pairs remaining -- the project assistant test suite will accept either
    convention. However, it will not accept code that does not process all pairs
    of naked twins from the original input. (For example, if you start processing
    pairs of twins and eliminate another pair of twins before the second pair
    is processed then your code will fail the PA test suite.)

    The first convention is preferred for consistency with the other strategies,
    and because it is simpler (since the reduce_puzzle function already calls this
    strategy repeatedly).
    """

    # Check if box has two digit value
    two_digit_boxes = [box for box in values.keys() if len(values[box]) == 2]

    # Construct dict of naked twins (peers with same two-digit value, one box may have multiple peers, assume never >2 in same unit type)
    naked_twin_dict = {}
    for two_digit_box in [box for box in values.keys() if len(values[box]) == 2]:
        for twin_peer in [twin_peer for twin_peer in peers[two_digit_box] if values[twin_peer] == values[two_digit_box]]:
            if (twin_peer + '-' + two_digit_box) in naked_twin_dict:
                continue
            twin_key = two_digit_box + '-' + twin_peer
            naked_twin_dict[twin_key] = {}
            naked_twin_dict[twin_key]['twin1'] = two_digit_box
            naked_twin_dict[twin_key]['twin2'] = twin_peer
            naked_twin_dict[twin_key]['value'] = values[two_digit_box]
            naked_twin_dict[twin_key]['peer_type'] = get_box_twin_peer_type(two_digit_box, twin_peer)

    # Process by removing values from peers that are in the *same unit as BOTH twins*
    for key, naked_twins in naked_twin_dict.items():
        # build list of 'lists of peers' for each naked twin pairing - may be more than one list of peers given different unit types
        target_peers = []

        # twins in same row, get peers in that row...
        if naked_twins['peer_type'] in [UnitType.row, UnitType.square_row]:
            target_peers.append([row for row in row_units if row.count(naked_twins['twin1']) > 0][0])

        # twins in same column, get peers in that column...
        elif naked_twins['peer_type'] in [UnitType.column, UnitType.square_column]:
            target_peers.append([column for column in column_units if column.count(naked_twins['twin1']) > 0][0])

        # twins in same diagonal, get peers in that diagonal...
        elif naked_twins['peer_type'] in [UnitType.diagonal, UnitType.square_diagonal]:
            target_peers.append([diagonal for diagonal in diagonal_units if diagonal.count(naked_twins['twin1']) > 0][0])

        # twins in same square, get peers in that square...
        if naked_twins['peer_type'] in [UnitType.square, UnitType.square_row, UnitType.square_column, UnitType.square_diagonal]:
            target_peers.append([square for square in square_units if square.count(naked_twins['twin1']) > 0][0])

        # remove matching digits for non-twin cells/boxes
        for unit_peers in target_peers:
            for peer in [peer for peer in unit_peers if peer not in [naked_twins['twin1'], naked_twins['twin2']]]:
                # print('checking peer {} with value {} given twin_peers {} and {} with value {}'.format(peer, values[peer], naked_twins['twin1'], naked_twins['twin2'], naked_twins['value']))
                for digit in naked_twins['value']:
                    values[peer] = values[peer].replace(digit, '')

    return values


def eliminate(values):
    """Apply the eliminate strategy to a Sudoku puzzle

    The eliminate strategy says that if a box has a value assigned, then none
    of the peers of that box can have the same value.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict
        The values dictionary with the assigned values eliminated from peers
    """
    solved_values = [box for box in values.keys() if len(values[box]) == 1]

    for box in solved_values:
        digit = values[box]
        # get peers per utility function
        for peer in peers[box]:
            # remove solved digit from peer
            values[peer] = values[peer].replace(digit, '')

    return values


def only_choice(values):
    """Apply the only choice strategy to a Sudoku puzzle

    The only choice strategy says that if only one box in a unit allows a certain
    digit, then that box must be assigned that digit.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict
        The values dictionary with all single-valued boxes assigned

    Notes
    -----
    You should be able to complete this function by copying your code from the classroom
    """
    # get flat list of rows, columns, squares
    for unit in unitlist:
        for digit in '123456789':
            # find any boxes containing an 'only choice' digit
            dplaces = [box for box in unit if digit in values[box]]
            if len(dplaces) == 1:
                values[dplaces[0]] = digit
    return values


def reduce_puzzle(values):
    """Reduce a Sudoku puzzle by repeatedly applying all constraint strategies

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict or False
        The values dictionary after continued application of the constraint strategies
        no longer produces any changes, or False if the puzzle is unsolvable 
    """
    stalled = False
    while not stalled:
        # Check how many boxes have a determined value
        solved_values_before = len([box for box in values.keys() if len(values[box]) == 1])

        # Use the Eliminate Strategy
        values = eliminate(values)

        # Use the Only Choice Strategy
        values = only_choice(values)

        # apply naked twins strategy
        values = naked_twins(values)

        # Check how many boxes have a determined value, to compare
        solved_values_after = len([box for box in values.keys() if len(values[box]) == 1])

        # If no new values were added, stop the loop.
        stalled = solved_values_before == solved_values_after

        # Sanity check, return False if there is a box with zero available values:
        if len([box for box in values.keys() if len(values[box]) == 0]):
            return False
    return values


def search(values):
    """Apply depth first search to solve Sudoku puzzles in order to solve puzzles
    that cannot be solved by repeated reduction alone.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict or False
        The values dictionary with all boxes assigned or False

    Notes
    -----
    You should be able to complete this function by copying your code from the classroom
    and extending it to call the naked twins strategy.
    """

    values = reduce_puzzle(values)

    if values is False:
        return False ## Failed earlier

    if all(len(values[s]) == 1 for s in boxes):
        return values ## Solved!

    # Choose one of the unfilled squares with the fewest possibilities
    n, s = min((len(values[s]), s) for s in boxes if len(values[s]) > 1)

    # Now use recursion to solve each one of the resulting sudokus, and
    for value in values[s]:
        new_sudoku = values.copy()
        new_sudoku[s] = value
        attempt = search(new_sudoku)
        if attempt:
            return attempt


def solve(grid):
    """Find the solution to a Sudoku puzzle using search and constraint propagation

    Parameters
    ----------
    grid(string)
        a string representing a sudoku grid.
        
        Ex. '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'

    Returns
    -------
    dict or False
        The dictionary representation of the final sudoku grid or False if no solution exists.
    """
    values = grid2values(grid)
    values = search(values)
    return values


if __name__ == "__main__":
    diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    display(grid2values(diag_sudoku_grid))
    result = solve(diag_sudoku_grid)
    display(result)

    try:
        import PySudoku
        PySudoku.play(grid2values(diag_sudoku_grid), result, history)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')
