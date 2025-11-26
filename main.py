"""
Main game loop for Farm Simulator.
Integrates all systems: rendering, input, game logic, and paradigms.
"""
import pygame
import sys
import asyncio
from models import GameState, Tool, CropType
from game_logic import (
    plant_seed, water_crop, harvest_crop, advance_day, 
    buy_seeds, toggle_crop_selection, natural_growth_tick
)
from renderer import Renderer
from save_system import save_game, load_game, save_exists
from logic_system import update_unlocks, get_next_unlocks
from concurrency_system import CropGrowthManager, WeatherSystem, apply_rain_effect


class FarmSimulator:
    """Main game class"""
    
    def __init__(self):
        """Initialize the game"""
        self.renderer = Renderer()
        self.clock = pygame.time.Clock()
        self.running = True
        self.in_shop = False
        self.g_manager = CropGrowthManager(self.growth_event)
        self.w_manager = WeatherSystem(self.weather_event)
        self.last_growth_time = pygame.time.get_ticks()   
        self.plot_growth_timers = {}
        
        # Load or create game state
        if save_exists():
            print("Loading saved game...")
            self.state = load_game()
            self.renderer.show_message("Game loaded!")
        else:
            print("Starting new game...")
            self.state = GameState.create_initial_state()
            self.renderer.show_message("Welcome to Farm Simulator!")
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)  # 60 FPS
        
        # Save on exit
        print("Saving game...")
        save_game(self.state)
        pygame.quit()
        sys.exit()
    
    def handle_events(self):
        """Handle input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                self.handle_keypress(event.key)
            
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.in_shop:
                self.handle_mouse_click(event.button, event.pos)
    
    def handle_keypress(self, key: int):
        """Handle keyboard input"""
        if self.in_shop:
            if key == pygame.K_ESCAPE:
                self.in_shop = False
            return
        
        if key == pygame.K_n:
            # Advance day
            self.state, msg = advance_day(self.state)
            # Update unlocks after day advance
            self.state = update_unlocks(self.state)
            self.renderer.show_message(msg)
            
            # Check for new unlocks
            next_unlocks = get_next_unlocks(self.state.stats)
            if next_unlocks:
                print("Progress towards unlocks:")
                for unlock in next_unlocks[:3]:  # Show top 3
                    print(f"  - {unlock}")
        
        elif key == pygame.K_s:
            # Open shop
            self.in_shop = True
        
        elif key == pygame.K_TAB:
            # Toggle crop selection
            self.state = toggle_crop_selection(self.state)
            from models import CROP_DATABASE
            crop_info = CROP_DATABASE[self.state.selected_crop]
            self.renderer.show_message(f"Selected: {crop_info.name}")
        
        elif key == pygame.K_F5:
            # Quick save
            if save_game(self.state):
                self.renderer.show_message("Game saved!")
            else:
                self.renderer.show_message("Save failed!")
        
        elif key == pygame.K_r:
            # Trigger rain event (for testing)
            self.state = apply_rain_effect(self.state)
            self.renderer.show_message("It's raining! All crops watered!")
    
    def handle_mouse_click(self, button: int, pos: tuple):
        """Handle mouse clicks on the farm"""
        # Get plot from mouse position
        hovered_plot = self.renderer._get_plot_from_mouse(self.state, pos)
        
        if not hovered_plot:
            return
        
        x, y = hovered_plot
        
        if button == 1:  # Left click - Plant
            self.state, msg = plant_seed(self.state, x, y)
            self.renderer.show_message(msg)
        
        elif button == 3:  # Right click - Water
            self.state, msg = water_crop(self.state, x, y)
            self.renderer.show_message(msg)
    
    def handle_harvest_key(self, x: int, y: int):
        """Handle harvest action"""
        self.state, msg = harvest_crop(self.state, x, y)
        # Update unlocks after harvest
        self.state = update_unlocks(self.state)
        self.renderer.show_message(msg)
    
    def update(self):
    # ----- SHOP HANDLING -----
        if self.in_shop:
        # Draw shop and maybe get a crop to buy
            crop_to_buy = self.renderer.render_shop(self.state)

        # If player clicked on a crop button: buy 1 seed, but stay in shop
            if crop_to_buy:
                self.state, msg = buy_seeds(self.state, crop_to_buy, 1)
                self.renderer.show_message(msg)
            # ❌ do NOT close shop here
            # self.in_shop = False

        # Allow ESC to close the shop reliably
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                self.in_shop = False
                return  # go back to main game next frame

        # While shop is open, skip growth / harvest update logic
            return
    # ----- Real-time growth with per-crop timing -----
        now = pygame.time.get_ticks()
        delta_ms = now - self.last_growth_time
        self.last_growth_time = now

    # convert to seconds
        delta_seconds = delta_ms / 1000.0

        if delta_seconds > 0:
            from game_logic import realtime_growth_step
            self.state = realtime_growth_step(self.state,
                                          self.plot_growth_timers,
                                          delta_seconds)

    # ----- Harvest key (H) as before -----
        keys = pygame.key.get_pressed()
        if keys[pygame.K_h] and not self.in_shop:
            mouse_pos = pygame.mouse.get_pos()
            hovered_plot = self.renderer._get_plot_from_mouse(self.state, mouse_pos)
            if hovered_plot:
                x, y = hovered_plot
                self.state, msg = harvest_crop(self.state, x, y)
                # Update unlocks after harvest
                self.state = update_unlocks(self.state)
                self.renderer.show_message(msg)
                pygame.time.wait(200)

    
    def growth_event(self, msg: str):
        self.renderer.show_message(msg)
    
    def weather_event(self, event_type: str):
        if event_type == "rain":
            self.state = apply_rain_effect(self.state)
            self.renderer.show_message("Rain event: all crops watered!")

    async def run_async(self):
        # start background tasks
        import asyncio
        self.g_manager.running = True
        self.w_manager.running = True
        loop = asyncio.get_running_loop()
        self.g_manager.growth_task = loop.create_task(self.g_manager.growth_loop())
        self.w_manager.weather_task = loop.create_task(self.w_manager.weather_loop())

        while self.running:
            self.handle_events()
            self.update()
            self.render()
            await asyncio.sleep(0)  # give control back to event loop

        # stop background tasks
        self.g_manager.stop()
        self.w_manager.stop()
        print("Saving game...")
        save_game(self.state)

        # ✅ CLEANUP PYGAME
        pygame.quit()

    def render(self):
        """Render the game"""
        if not self.in_shop:
            mouse_pos = pygame.mouse.get_pos()
            self.renderer.render(self.state, mouse_pos)
        # Shop rendering is handled in update()


def main():
    """Entry point"""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  🌾 FARM SIMULATOR 🌾".center(68) + "█")
    print("█" + "  Multi-Paradigm Programming Demonstration".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    print("\n" + "▀" * 70)
    print("  🎮 CONTROLS")
    print("▀" * 70)
    print("  Left Click    → Plant seed on empty plot")
    print("  Right Click   → Water crop (required for growth)")
    print("  H (hover)     → Harvest mature crop")
    print("  N             → Next day (advance time)")
    print("  S             → Open shop menu")
    print("  Tab           → Change selected crop")
    print("  F5            → Quick save")
    print("  R             → Test rain event")
    
    print("\n" + "▀" * 70)
    print("  🎯 GOAL")
    print("▀" * 70)
    print("  • Plant and water crops to help them grow")
    print("  • Harvest mature crops to earn coins")
    print("  • Buy new seeds from the shop")
    print("  • Unlock new crop types and expand your farm!")
    
    print("\n" + "▀" * 70)
    print("  📚 PARADIGMS DEMONSTRATED")
    print("▀" * 70)
    print("  ⭐ Functional Programming   → Pure functions, immutable state")
    print("  ⭐ Logic Programming        → miniKanren unlock rules")
    print("  ⭐ Concurrent Programming   → Async weather & growth systems")
    
    print("\n" + "█" * 70)
    print("█" + " Starting game... Press ALT+F4 or close window to exit ".center(68) + "█")
    print("█" * 70 + "\n")
    
    game = FarmSimulator()
    asyncio.run(game.run_async())

if __name__ == "__main__":
    main()
