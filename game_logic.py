"""
Pure functional game logic for Farm Simulator.
All functions are side-effect free and return new state objects.
Demonstrates Functional Programming paradigm.
"""
from typing import Tuple, Optional
from dataclasses import replace
from models import (
    GameState, Plot, Crop, Inventory, PlayerStats,
    CropType, CROP_DATABASE, GrowthStage
)


def plant_seed(state: GameState, x: int, y: int) -> Tuple[GameState, str]:
    """
    Plant a seed at the specified plot.
    Pure function - returns new state without modifying input.
    
    Returns: (new_state, message)
    """
    plot = state.farm.get((x, y))
    
    if not plot:
        return state, "Invalid plot location"
    
    if not plot.unlocked:
        return state, "This area is locked!"
    
    if not plot.is_empty():
        return state, "Plot already has a crop!"
    
    crop_type = state.selected_crop
    crop_info = CROP_DATABASE[crop_type]
    
    if not crop_info.unlocked:
        return state, f"{crop_info.name} is not unlocked yet!"
    
    if not state.inventory.has_seeds(crop_type):
        return state, f"No {crop_info.name} seeds available!"
    
    # Check energy
    if state.energy < 5:
        return state, "Not enough energy! (Need 5)"

    # Check season
    if crop_info.preferred_seasons and state.season not in crop_info.preferred_seasons:
        seasons_str = " or ".join(s.value for s in crop_info.preferred_seasons)
        return state, f"{crop_info.name} only grows in {seasons_str}!"

    # Create new crop
    new_crop = Crop(crop_type=crop_type)
    
    # Update plot with new crop
    new_plot = replace(plot, crop=new_crop)
    new_farm = {**state.farm, (x, y): new_plot}
    
    # Update inventory (remove seed)
    new_seeds = {**state.inventory.seeds}
    new_seeds[crop_type] = new_seeds.get(crop_type, 0) - 1
    new_inventory = replace(state.inventory, seeds=new_seeds)
    
    # Return new state
    new_state = replace(state, farm=new_farm, inventory=new_inventory, energy=state.energy - 5)
    return new_state, f"Planted {crop_info.name}!"


def water_crop(state: GameState, x: int, y: int) -> Tuple[GameState, str]:
    """
    Water a crop at the specified plot.
    Pure function - returns new state.
    
    Returns: (new_state, message)
    """
    plot = state.farm.get((x, y))
    
    if not plot:
        return state, "Invalid plot location"
    
    if plot.is_empty():
        return state, "No crop to water!"
    
    # Type guard: we know crop is not None here
    crop = plot.crop
    if crop is None:
        return state, "No crop to water!"
    
    if crop.watered:
        return state, "Crop already watered today!"
    
    # Check energy
    if state.energy < 2:
        return state, "Not enough energy! (Need 2)"

    # Update crop to be watered
    new_crop = replace(crop, watered=True)
    new_plot = replace(plot, crop=new_crop)
    new_farm = {**state.farm, (x, y): new_plot}
    
    new_state = replace(state, farm=new_farm, energy=state.energy - 2)
    return new_state, "Crop watered!"


def harvest_crop(state: GameState, x: int, y: int) -> Tuple[GameState, str]:
    """
    Harvest a mature crop from the specified plot.
    Pure function - returns new state with updated coins and stats.
    
    Returns: (new_state, message)
    """
    plot = state.farm.get((x, y))
    
    if not plot:
        return state, "Invalid plot location"
    
    if plot.is_empty():
        return state, "No crop to harvest!"
    
    if not plot.has_mature_crop():
        return state, "Crop is not ready to harvest!"
    
    # Type guard: we know crop is not None here
    crop = plot.crop
    if crop is None:
        return state, "No crop to harvest!"
    
    # Check energy
    if state.energy < 3:
        return state, "Not enough energy! (Need 3)"

    crop_type = crop.crop_type
    crop_info = CROP_DATABASE[crop_type]
    
    # Clear the plot
    new_plot = replace(plot, crop=None)
    new_farm = {**state.farm, (x, y): new_plot}
    
    # Update inventory (add coins)
    new_inventory = replace(
        state.inventory,
        coins=state.inventory.coins + crop_info.harvest_value
    )
    
    # Update stats
    new_crops_harvested = {**state.stats.crops_harvested}
    new_crops_harvested[crop_type] = new_crops_harvested.get(crop_type, 0) + 1
    
    new_stats = replace(
        state.stats,
        total_harvests=state.stats.total_harvests + 1,
        total_coins_earned=state.stats.total_coins_earned + crop_info.harvest_value,
        crops_harvested=new_crops_harvested
    )
    
    new_state = replace(state, farm=new_farm, inventory=new_inventory, stats=new_stats, energy=state.energy - 3)
    return new_state, f"Harvested {crop_info.name} for {crop_info.harvest_value} coins!"


def advance_day(state: GameState) -> Tuple[GameState, str]:
    """
    Advance to the next day and update all crops.
    Pure function - returns new state with all crops advanced.
    
    Returns: (new_state, message)
    """
    from models import Season
    new_farm = {}
    
    for pos, plot in state.farm.items():
        if plot.crop is None:
            new_farm[pos] = plot
        else:
            # Advance crop growth if watered
            crop = plot.crop
            if crop.watered:
                new_crop = replace(
                    crop,
                    days_since_plant=crop.days_since_plant + 1,
                    watered=False  # Reset water status
                )
            else:
                # Reset water status but don't advance growth
                new_crop = replace(crop, watered=False)
            
            new_plot = replace(plot, crop=new_crop)
            new_farm[pos] = new_plot
    
    new_stats = replace(state.stats, days_played=state.stats.days_played + 1)
    
    # Advance season every 10 days
    new_day = state.current_day + 1
    new_season = state.season
    if new_day % 10 == 1:
        seasons = list(Season)
        current_idx = seasons.index(state.season)
        new_season = seasons[(current_idx + 1) % len(seasons)]

    # Increase max energy significantly each day to represent growing stamina
    new_max_energy = state.max_energy + 50

    new_state = replace(
        state,
        farm=new_farm,
        current_day=new_day,
        stats=new_stats,
        max_energy=new_max_energy,
        energy=new_max_energy, # Restore to new max energy
        season=new_season,
        time=6.0  # Reset time to 6:00 AM
    )
    
    return new_state, f"Day {new_state.current_day} begins! Max Energy increased to {new_max_energy}!"


def buy_seeds(state: GameState, crop_type: CropType, quantity: int = 1) -> Tuple[GameState, str]:
    """
    Buy seeds from the shop.
    Pure function - returns new state with updated inventory.
    
    Returns: (new_state, message)
    """
    crop_info = CROP_DATABASE[crop_type]
    
    if not crop_info.unlocked:
        return state, f"{crop_info.name} seeds are not available yet!"
    
    total_cost = crop_info.seed_cost * quantity
    
    if not state.inventory.can_afford(total_cost):
        return state, f"Not enough coins! Need {total_cost} coins."
    
    # Update inventory
    new_seeds = {**state.inventory.seeds}
    new_seeds[crop_type] = new_seeds.get(crop_type, 0) + quantity
    
    new_inventory = replace(
        state.inventory,
        coins=state.inventory.coins - total_cost,
        seeds=new_seeds
    )
    
    new_state = replace(state, inventory=new_inventory)
    return new_state, f"Bought {quantity} {crop_info.name} seed(s) for {total_cost} coins!"


def toggle_crop_selection(state: GameState) -> GameState:
    """
    Cycle through available crop types.
    Pure function - returns new state with updated selection.
    """
    available_crops = [ct for ct in CropType if CROP_DATABASE[ct].unlocked]
    if not available_crops:
        return state
    
    current_idx = available_crops.index(state.selected_crop) if state.selected_crop in available_crops else 0
    next_idx = (current_idx + 1) % len(available_crops)
    
    return replace(state, selected_crop=available_crops[next_idx])

def natural_growth_tick(state: GameState) -> GameState:
    """
    Like a mini advance_day: increase days_since_plant for watered crops
    without changing current_day or stats.
    """
    from dataclasses import replace
    new_farm = {}
    for pos, plot in state.farm.items():
        if plot.crop is None:
            new_farm[pos] = plot
        else:
            crop = plot.crop
            if crop.watered:
                new_crop = replace(
                    crop,
                    days_since_plant=crop.days_since_plant + 1,
                    watered=False
                )
            else:
                new_crop = replace(crop, watered=False)
            new_farm[pos] = replace(plot, crop=new_crop)
    return replace(state, farm=new_farm)

from dataclasses import replace
from typing import Dict, Tuple
from models import GameState, CROP_DATABASE, CropType, Plot, Crop

def realtime_growth_step(state: GameState,
                         timers: Dict[Tuple[int, int], float],
                         delta_seconds: float) -> GameState:
    """
    Advance crop growth based on real time, with per-crop time_per_stage.
    - Only watered crops accumulate time.
    - When accumulated time >= time_per_stage, we increment days_since_plant by 1
      and reset watered to False (so player must water again for next stage).
    """
    new_farm = {}

    for pos, plot in state.farm.items():
        crop = plot.crop

        # No crop: clear any timer and continue
        if crop is None:
            timers.pop(pos, None)
            new_farm[pos] = plot
            continue

        # Only grow if the crop is watered
        if not crop.watered:
            # No growth; keep plot / crop as-is
            new_farm[pos] = plot
            continue

        crop_info = CROP_DATABASE[crop.crop_type]

        # Accumulate time for this plot
        current_acc = timers.get(pos, 0.0) + delta_seconds

        # While we've accumulated enough time for at least one stage, grow
        # (loop allows catching up if delta_seconds is large)
        grown_crop = crop
        while current_acc >= crop_info.time_per_stage and not grown_crop.is_mature():
            current_acc -= crop_info.time_per_stage
            grown_crop = replace(
                grown_crop,
                days_since_plant=grown_crop.days_since_plant + 1,
                watered=False,  # must water again for the next stage
            )

        timers[pos] = current_acc
        new_farm[pos] = replace(plot, crop=grown_crop)
    

    return replace(state, farm=new_farm)



def get_plot_status(plot: Plot) -> str:
    """
    Get a human-readable status of a plot.
    Pure function.
    """
    if not plot.unlocked:
        return "Locked"
    if plot.is_empty():
        return "Empty"
    
    # Type guard: we know crop is not None here
    crop = plot.crop
    if crop is None:
        return "Empty"
    
    crop_info = CROP_DATABASE[crop.crop_type]
    
    if crop.is_mature():
        return f"{crop_info.name} (READY!)"
    else:
        progress = crop.days_since_plant
        total = crop_info.growth_stages
        water_status = "💧" if crop.watered else "❌"
        return f"{crop_info.name} ({progress}/{total}) {water_status}"


def toggle_help(state: GameState) -> GameState:
    """Toggle the help menu visibility"""
    return replace(state, show_help=not state.show_help)
