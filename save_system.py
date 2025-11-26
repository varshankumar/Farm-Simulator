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
        'selected_tool': state.selected_tool.name,
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
    # ---------- Restore farm ----------
    farm: Dict[tuple[int, int], Plot] = {}
    farm_data = data.get('farm', {})

    for key, plot_data in farm_data.items():
        x, y = map(int, key.split(','))

        crop = None
        crop_raw = plot_data.get('crop')
        if crop_raw:
            try:
                crop_type = CropType[crop_raw['crop_type']]
            except KeyError:
                # Unknown crop type in save – skip this crop
                crop_type = None

            if crop_type is not None:
                crop = Crop(
                    crop_type=crop_type,
                    growth_stage=crop_raw.get('growth_stage', 0),
                    watered=crop_raw.get('watered', False),
                    days_since_plant=crop_raw.get('days_since_plant', 0)
                )

        plot = Plot(
            x=x,
            y=y,
            crop=crop,
            unlocked=plot_data.get('unlocked', True)
        )
        farm[(x, y)] = plot

    # ---------- Restore inventory ----------
    inv_data = data.get('inventory', {})
    raw_seeds = inv_data.get('seeds', {})

    seeds: Dict[CropType, int] = {}
    for name, count in raw_seeds.items():
        try:
            ct = CropType[name]
            seeds[ct] = count
        except KeyError:
            # Ignore unknown crop names
            continue

    inventory = Inventory(
        coins=inv_data.get('coins', 0),
        seeds=seeds
    )

    # ---------- Restore stats ----------
    stats_data = data.get('stats', {})
    raw_crops_harvested = stats_data.get('crops_harvested', {})

    crops_harvested: Dict[CropType, int] = {}
    for name, count in raw_crops_harvested.items():
        try:
            ct = CropType[name]
            crops_harvested[ct] = count
        except KeyError:
            continue

    stats = PlayerStats(
        total_harvests=stats_data.get('total_harvests', 0),
        total_coins_earned=stats_data.get('total_coins_earned', 0),
        days_played=stats_data.get('days_played', 0),
        crops_harvested=crops_harvested
    )

    # ---------- Restore selected crop/tool & other fields ----------
    # Selected crop
    selected_crop_name = data.get('selected_crop', 'WHEAT')
    try:
        selected_crop = CropType[selected_crop_name]
    except KeyError:
        selected_crop = CropType.WHEAT

    # Selected tool – if you later add it to serialize_game_state
    selected_tool_name = data.get('selected_tool', 'PLANT')
    try:
        selected_tool = Tool[selected_tool_name]
    except KeyError:
        selected_tool = Tool.PLANT

    current_day = data.get('current_day', 1)
    farm_size = data.get('farm_size', 10)
    unlocked_area = data.get('unlocked_area', 5)

    return GameState(
        farm=farm,
        inventory=inventory,
        stats=stats,
        current_day=current_day,
        selected_crop=selected_crop,
        selected_tool=selected_tool,
        farm_size=farm_size,
        unlocked_area=unlocked_area
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
