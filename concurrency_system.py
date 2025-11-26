"""
Concurrency system using asyncio for background crop growth.
Demonstrates Concurrent Programming paradigm.
"""
import asyncio
from typing import Optional, Callable
from models import GameState


class CropGrowthManager:
    """
    Manages background crop growth using asyncio.
    Crops grow slowly over real time, not just when day advances.
    """
    
    def __init__(self, update_callback: Callable[[str], None]):
        """
        Initialize the growth manager.
        
        Args:
            update_callback: Function to call when growth occurs
        """
        self.update_callback = update_callback
        self.running = False
        self.growth_task: Optional[asyncio.Task] = None
        self.growth_interval = 30.0  # Seconds between growth ticks
    
    async def growth_loop(self):
        """
        Async loop that triggers growth events periodically.
        Runs in background while game is active.
        """
        while self.running:
            await asyncio.sleep(self.growth_interval)
            
            if self.running:
                self.update_callback("Crops are growing naturally...")
    
    def start(self):
        """Start the background growth system"""
        if not self.running:
            self.running = True
            # Note: This would need to be integrated with the main event loop
            # For now, this is a placeholder showing the structure
    
    def stop(self):
        """Stop the background growth system"""
        self.running = False
        if self.growth_task and not self.growth_task.done():
            self.growth_task.cancel()
    
    def set_growth_rate(self, seconds: float):
        """
        Adjust the growth rate.
        
        Args:
            seconds: Time between growth ticks
        """
        self.growth_interval = seconds


class WeatherSystem:
    """
    Async weather system that can trigger random events.
    Example: Rain automatically waters all crops.
    """
    
    def __init__(self, weather_callback: Callable[[str], None]):
        """
        Initialize weather system.
        
        Args:
            weather_callback: Function to call when weather events occur
        """
        self.weather_callback = weather_callback
        self.running = False
        self.weather_task: Optional[asyncio.Task] = None
    
    async def weather_loop(self):
        """
        Async loop that generates random weather events.
        """
        import random
        
        while self.running:
            # Wait 1-3 minutes between weather checks
            wait_time = random.uniform(80, 200)
            await asyncio.sleep(wait_time)
            
            if not self.running:
                break
            
            # 20% chance of rain
            if random.random() < 0.8:
                self.weather_callback("rain")
    
    def start(self):
        """Start the weather system"""
        if not self.running:
            self.running = True
    
    def stop(self):
        """Stop the weather system"""
        self.running = False
        if self.weather_task and not self.weather_task.done():
            self.weather_task.cancel()


async def auto_save_loop(save_callback: Callable[[], None], interval: float = 300.0):
    """
    Async loop for automatic game saving.
    
    Args:
        save_callback: Function to call to save the game
        interval: Seconds between auto-saves (default: 5 minutes)
    """
    while True:
        await asyncio.sleep(interval)
        save_callback()


def apply_rain_effect(state: GameState) -> GameState:
    """
    Apply rain effect: water all planted crops.
    Pure function demonstrating FP + Concurrency integration.
    
    Args:
        state: Current game state
    
    Returns:
        New game state with all crops watered
    """
    from dataclasses import replace
    
    new_farm = {}
    
    for pos, plot in state.farm.items():
        if plot.crop is not None and not plot.crop.watered:
            new_crop = replace(plot.crop, watered=True)
            new_plot = replace(plot, crop=new_crop)
            new_farm[pos] = new_plot
        else:
            new_farm[pos] = plot
    
    return replace(state, farm=new_farm)
