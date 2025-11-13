"""
Save and Load system for game persistence.
Serializes game state to JSON and restores it.
"""
import json
from pathlib import Path
from typing import Dict, Any
from dataclasses import asdict
from models import GameState, Plot, Crop, Inventory, PlayerStats, CropType, Tool


SAVE_FILE = "farm_save.json"


def serialize_game_state(state: GameState) -> Dict[str, Any]:
    """
    Convert game state to JSON-serializable dictionary.
    
    Args:
        state: Current game state
    
    Returns:
        Dictionary that can be saved to JSON
    """
    # Convert farm to serializable format
    farm_data = {}
    for (x, y), plot in state.farm.items():
        plot_data = {
            'x': plot.x,
            'y': plot.y,
            'unlocked': plot.unlocked,
            'crop': None
        }
        
        if plot.crop:
            plot_data['crop'] = {
                'crop_type': plot.crop.crop_type.name,
                'growth_stage': plot.crop.growth_stage,
                'watered': plot.crop.watered,
                'days_since_plant': plot.crop.days_since_plant
            }
        
        farm_data[f"{x},{y}"] = plot_data
    
    # Convert inventory
    inventory_data = {
        'coins': state.inventory.coins,
        'seeds': {crop_type.name: count for crop_type, count in state.inventory.seeds.items()}
    }
    
    # Convert stats
    stats_data = {
        'total_harvests': state.stats.total_harvests,
        'total_coins_earned': state.stats.total_coins_earned,
        'days_played': state.stats.days_played,
        'crops_harvested': {crop_type.name: count for crop_type, count in state.stats.crops_harvested.items()}
    }
    
    return {
        'version': '1.0',
        'farm': farm_data,
        'inventory': inventory_data,
        'stats': stats_data,
        'current_day': state.current_day,
        'selected_crop': state.selected_crop.name,
        'farm_size': state.farm_size,
        'unlocked_area': state.unlocked_area
    }


def deserialize_game_state(data: Dict[str, Any]) -> GameState:
    """
    Restore game state from JSON data.
    
    Args:
        data: Dictionary loaded from JSON
    
    Returns:
        Restored game state
    """
    from dataclasses import replace
    
    # Restore farm
    farm = {}
    for key, plot_data in data['farm'].items():
        x, y = map(int, key.split(','))
        
        crop = None
        if plot_data['crop']:
            crop_data = plot_data['crop']
            crop = Crop(
                crop_type=CropType[crop_data['crop_type']],
                growth_stage=crop_data['growth_stage'],
                watered=crop_data['watered'],
                days_since_plant=crop_data['days_since_plant']
            )
        
        plot = Plot(
            x=x,
            y=y,
            crop=crop,
            unlocked=plot_data['unlocked']
        )
        farm[(x, y)] = plot
    
    # Restore inventory
    inv_data = data['inventory']
    seeds = {CropType[name]: count for name, count in inv_data['seeds'].items()}
    inventory = Inventory(coins=inv_data['coins'], seeds=seeds)
    
    # Restore stats
    stats_data = data['stats']
    crops_harvested = {CropType[name]: count for name, count in stats_data['crops_harvested'].items()}
    stats = PlayerStats(
        total_harvests=stats_data['total_harvests'],
        total_coins_earned=stats_data['total_coins_earned'],
        days_played=stats_data['days_played'],
        crops_harvested=crops_harvested
    )
    
    return GameState(
        farm=farm,
        inventory=inventory,
        stats=stats,
        current_day=data['current_day'],
        selected_crop=CropType[data['selected_crop']],
        selected_tool=Tool.PLANT,  # Default tool
        farm_size=data['farm_size'],
        unlocked_area=data['unlocked_area']
    )


def save_game(state: GameState, filename: str = SAVE_FILE) -> bool:
    """
    Save game state to file.
    
    Args:
        state: Game state to save
        filename: File to save to
    
    Returns:
        True if successful, False otherwise
    """
    try:
        data = serialize_game_state(state)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False


def load_game(filename: str = SAVE_FILE) -> GameState:
    """
    Load game state from file.
    
    Args:
        filename: File to load from
    
    Returns:
        Loaded game state, or new state if file doesn't exist
    """
    try:
        if not Path(filename).exists():
            return GameState.create_initial_state()
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        return deserialize_game_state(data)
    except Exception as e:
        print(f"Error loading game: {e}")
        return GameState.create_initial_state()


def save_exists(filename: str = SAVE_FILE) -> bool:
    """
    Check if a save file exists.
    
    Args:
        filename: Save file to check
    
    Returns:
        True if save exists, False otherwise
    """
    return Path(filename).exists()
