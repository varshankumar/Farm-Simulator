"""
Logic Programming module using miniKanren (kanren library).
Implements unlocking system based on game achievements.
Demonstrates Logic Programming paradigm.
"""
# Import from kanren - these are all exported at top level despite linter warnings
from kanren import run, eq, conde, var, Relation, facts, membero  # type: ignore
from typing import List, Dict
from models import GameState, CropType, CROP_DATABASE, PlayerStats


# Define relations for logic programming
unlocks = Relation()
requires = Relation()


def initialize_unlock_rules():
    """
    Initialize the logic programming rules for unlocking content.
    Uses facts and relations to define unlock conditions.
    """
    # Define unlock rules as facts
    # Format: (item_to_unlock, requirement_type, threshold)
    
    facts(unlocks, 
        # Crop unlocks
        ('carrot', 'harvests', 5),
        ('tomato', 'harvests', 15),
        ('corn', 'coins', 100),
        
        # Farm expansion unlocks
        ('area_6x6', 'harvests', 10),
        ('area_7x7', 'coins', 60),
        ('area_8x8', 'harvests', 25),
        ('area_9x9', 'coins', 150),
        ('area_10x10', 'harvests', 50),
    )


def check_unlock_conditions(stats: PlayerStats, item: str) -> bool:
    """
    Use logic programming to check if an item should be unlocked.
    
    Args:
        stats: Current player stats
        item: Item to check for unlock (e.g., 'carrot', 'area_6x6')
    
    Returns:
        True if conditions are met, False otherwise
    """
    # Query the knowledge base for unlock requirements
    x = var()
    y = var()
    
    # Find all requirements for the item
    requirements = run(0, (x, y), unlocks(item, x, y))
    
    if not requirements:
        return True  # No requirements means already unlocked
    
    # Check if all requirements are satisfied
    for req_type, threshold in requirements:
        if req_type == 'harvests':
            if stats.total_harvests < threshold:
                return False
        elif req_type == 'coins':
            if stats.total_coins_earned < threshold:
                return False
        elif req_type == 'days':
            if stats.days_played < threshold:
                return False
    
    return True


def get_unlock_status(stats: PlayerStats) -> Dict[str, bool]:
    """
    Get the unlock status for all items using logic programming.
    
    Returns:
        Dictionary mapping item names to unlock status
    """
    items = [
        'carrot', 'tomato', 'corn',
        'area_6x6', 'area_7x7', 'area_8x8', 'area_9x9', 'area_10x10'
    ]
    
    status = {}
    for item in items:
        status[item] = check_unlock_conditions(stats, item)
    
    return status


def get_next_unlocks(stats: PlayerStats) -> List[str]:
    """
    Get a list of items that are close to being unlocked.
    Uses logic queries to find items with unmet requirements.
    
    Returns:
        List of (item, requirement_description) tuples
    """
    next_unlocks = []
    
    items = [
        'carrot', 'tomato', 'corn',
        'area_6x6', 'area_7x7', 'area_8x8', 'area_9x9', 'area_10x10'
    ]
    
    for item in items:
        if check_unlock_conditions(stats, item):
            continue  # Already unlocked
        
        x = var()
        y = var()
        requirements = run(0, (x, y), unlocks(item, x, y))
        
        for req_type, threshold in requirements:
            if req_type == 'harvests' and stats.total_harvests < threshold:
                remaining = threshold - stats.total_harvests
                next_unlocks.append(f"{item}: {remaining} more harvests needed")
            elif req_type == 'coins' and stats.total_coins_earned < threshold:
                remaining = threshold - stats.total_coins_earned
                next_unlocks.append(f"{item}: {remaining} more coins needed")
    
    return next_unlocks


def update_unlocks(state: GameState) -> GameState:
    """
    Update the game state based on logic programming unlock rules.
    Checks which crops and areas should be unlocked.
    
    Returns:
        New game state with updated unlocks
    """
    from dataclasses import replace
    
    unlock_status = get_unlock_status(state.stats)
    
    # Update crop unlocks
    new_crop_db = {}
    for crop_type in CropType:
        crop_info = CROP_DATABASE[crop_type]
        crop_name = crop_type.name.lower()
        
        if crop_name in unlock_status and unlock_status[crop_name]:
            # Unlock this crop
            new_crop_db[crop_type] = replace(crop_info, unlocked=True)
        else:
            new_crop_db[crop_type] = crop_info
    
    # Temporarily update the global database
    CROP_DATABASE.update(new_crop_db)
    
    # Update farm area unlocks
    new_unlocked_area = state.unlocked_area
    
    area_checks = [
        ('area_6x6', 6),
        ('area_7x7', 7),
        ('area_8x8', 8),
        ('area_9x9', 9),
        ('area_10x10', 10),
    ]
    
    for area_name, size in area_checks:
        if unlock_status.get(area_name, False):
            new_unlocked_area = max(new_unlocked_area, size)
    
    # Update farm plots if area expanded
    if new_unlocked_area > state.unlocked_area:
        new_farm = {}
        for pos, plot in state.farm.items():
            x, y = pos
            # Unlock plots within new area
            if x < new_unlocked_area and y < new_unlocked_area:
                new_farm[pos] = replace(plot, unlocked=True)
            else:
                new_farm[pos] = plot
        
        return replace(state, farm=new_farm, unlocked_area=new_unlocked_area)
    
    return state


# Initialize the knowledge base when module is imported
initialize_unlock_rules()
