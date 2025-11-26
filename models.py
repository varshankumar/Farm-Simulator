"""
Data models for Farm Simulator game using dataclasses.
Demonstrates functional programming with immutable data structures.
"""
from dataclasses import dataclass, field, replace
from typing import Optional, Dict, Tuple
from enum import Enum


class CropType(Enum):
    """Available crop types in the game"""
    WHEAT = "Wheat"
    CARROT = "Carrot"
    TOMATO = "Tomato"
    CORN = "Corn"


class GrowthStage(Enum):
    """Crop growth stages"""
    EMPTY = 0
    SEED = 1
    SPROUT = 2
    GROWING = 3
    MATURE = 4


class Tool(Enum):
    """Player tools/actions"""
    PLANT = "Plant"
    WATER = "Water"
    HARVEST = "Harvest"


@dataclass(frozen=True)
class CropInfo:
    """Information about a crop type"""
    name: str
    growth_stages: int  # Days to mature
    seed_cost: int
    harvest_value: int
    time_per_stage: float
    unlocked: bool = True


# Crop database
CROP_DATABASE: Dict[CropType, CropInfo] = {
    CropType.WHEAT: CropInfo("Wheat", 3, 5, 15, 30.0, True),
    CropType.CARROT: CropInfo("Carrot", 4, 10, 25, 60.0, False),  # Unlockable
    CropType.TOMATO: CropInfo("Tomato", 5, 15, 40, 80.0, False),  # Unlockable
    CropType.CORN: CropInfo("Corn", 6, 20, 60, 100.0, False),      # Unlockable
}


@dataclass(frozen=True)
class Crop:
    """Represents a crop growing on a plot"""
    crop_type: CropType
    growth_stage: int = 0  # 0 = just planted
    watered: bool = False
    days_since_plant: int = 0

    def is_mature(self) -> bool:
        """Check if crop is ready to harvest"""
        crop_info = CROP_DATABASE[self.crop_type]
        return self.days_since_plant >= crop_info.growth_stages


@dataclass(frozen=True)
class Plot:
    """Represents a single farm plot"""
    x: int
    y: int
    crop: Optional[Crop] = None
    unlocked: bool = True  # For farm expansion feature

    def is_empty(self) -> bool:
        """Check if plot has no crop"""
        return self.crop is None

    def has_mature_crop(self) -> bool:
        """Check if plot has a harvestable crop"""
        return self.crop is not None and self.crop.is_mature()


@dataclass(frozen=True)
class Inventory:
    """Player inventory tracking seeds and coins"""
    coins: int = 50  # Starting coins
    seeds: Dict[CropType, int] = field(default_factory=lambda: {
        CropType.WHEAT: 10,  # Start with wheat seeds
    })

    def has_seeds(self, crop_type: CropType, count: int = 1) -> bool:
        """Check if player has enough seeds"""
        return self.seeds.get(crop_type, 0) >= count

    def can_afford(self, cost: int) -> bool:
        """Check if player has enough coins"""
        return self.coins >= cost


@dataclass(frozen=True)
class PlayerStats:
    """Track player achievements for unlocking features"""
    total_harvests: int = 0
    total_coins_earned: int = 0
    days_played: int = 0
    crops_harvested: Dict[CropType, int] = field(default_factory=dict)


@dataclass(frozen=True)
class GameState:
    """Main game state container"""
    farm: Dict[Tuple[int, int], Plot]  # (x, y) -> Plot
    inventory: Inventory
    stats: PlayerStats
    current_day: int = 1
    selected_crop: CropType = CropType.WHEAT
    selected_tool: Tool = Tool.PLANT
    farm_size: int = 10  # Grid size (10x10)
    unlocked_area: int = 5  # Starting usable area (5x5)

    @staticmethod
    def create_initial_state(farm_size: int = 10, unlocked_area: int = 5) -> 'GameState':
        """Create initial game state with empty farm"""
        farm = {}
        for x in range(farm_size):
            for y in range(farm_size):
                # Only unlock center area initially
                is_unlocked = (
                    x < unlocked_area and y < unlocked_area
                )
                farm[(x, y)] = Plot(x=x, y=y, unlocked=is_unlocked)
        
        return GameState(
            farm=farm,
            inventory=Inventory(),
            stats=PlayerStats(),
            farm_size=farm_size,
            unlocked_area=unlocked_area
        )


@dataclass(frozen=True)
class UnlockCondition:
    """Represents a condition for unlocking content"""
    min_harvests: int = 0
    min_coins: int = 0
    min_days: int = 0
    required_crops: Dict[CropType, int] = field(default_factory=dict)
