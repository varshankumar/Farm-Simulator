"""
Main game loop for Farm Simulator.
Integrates all systems: rendering, input, game logic, and paradigms.
"""
import pygame
import sys
import asyncio
from dataclasses import replace
from models import GameState, Tool, CropType
from game_logic import (
    plant_seed, water_crop, harvest_crop, advance_day, 
    buy_seeds, toggle_crop_selection, natural_growth_tick, realtime_growth_step,
    toggle_help
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
            self.renderer.show_message("Welcome to Little Roots")
    
    async def run_async(self):
        """Main game loop (Async)"""
        # start background tasks
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
        sys.exit()

    def run(self):
        """Legacy run method - redirects to async"""
        asyncio.run(self.run_async())
    
    def handle_events(self):
        """Handle input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Handle help overlay
            if self.state.show_help:
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = toggle_help(self.state)
                continue
            
            if event.type == pygame.KEYDOWN:
                self.handle_keypress(event.key)
            
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.in_shop:
                # Check for help button click
                if self.renderer.is_help_button_clicked(event.pos):
                    self.state = toggle_help(self.state)
                else:
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
            old_coins = self.state.inventory.coins
            self.state, msg = plant_seed(self.state, x, y)
            self.renderer.show_message(msg)
            
            # Visual feedback
            if "Planted" in msg:
                self.renderer.add_floating_text("-5 Energy", pos, (255, 0, 0))
        
        elif button == 3:  # Right click - Water
            self.state, msg = water_crop(self.state, x, y)
            self.renderer.show_message(msg)
            
            if "watered" in msg and "already" not in msg:
                self.renderer.add_floating_text("-2 Energy", pos, (100, 100, 255))
    
    def handle_harvest_key(self, x: int, y: int):
        """Handle harvest action"""
        old_coins = self.state.inventory.coins
        self.state, msg = harvest_crop(self.state, x, y)
        
        # Calculate coin gain
        coin_gain = self.state.inventory.coins - old_coins
        if coin_gain > 0:
            # Convert grid pos to screen pos for floating text
            # This is a bit hacky, ideally renderer handles this conversion
            # But for now we'll just use mouse pos if available or approximate
            mouse_pos = pygame.mouse.get_pos()
            self.renderer.add_floating_text(f"+{coin_gain} Coins!", mouse_pos, (255, 215, 0))
            self.renderer.add_floating_text("-3 Energy", (mouse_pos[0], mouse_pos[1] - 20), (255, 0, 0))

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

        # Advance game time (1 real second = 10 game minutes)
        # 10 game minutes = 10/60 hours = 1/6 hours
        # So 1 real second = 0.166 game hours
        game_hours_passed = delta_seconds * 0.2  #80secs
        new_time = self.state.time + game_hours_passed
        
        if new_time >= 22.0:  # 10 PM mandatory sleep
            self.state, msg = advance_day(self.state)
            self.state = update_unlocks(self.state)
            self.renderer.show_message("It's late! You fell asleep. " + msg)
        else:
            self.state = replace(self.state, time=new_time)

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
                # Only harvest if we haven't just harvested (simple debounce)
                # Ideally we check if there's a mature crop first to avoid spamming
                plot = self.state.farm.get((x, y))
                if plot and plot.has_mature_crop():
                    self.handle_harvest_key(x, y)
                    pygame.time.wait(200)

    
    def growth_event(self, msg: str):
        self.renderer.show_message(msg)
    
    def weather_event(self, event_type: str):
        if event_type == "rain":
            self.state = apply_rain_effect(self.state)
            self.renderer.show_message("Rain event: all crops watered!")

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
