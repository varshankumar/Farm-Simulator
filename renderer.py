"""
Pygame rendering and UI system for Farm Simulator.
Handles all visual display including farm grid, HUD, and menus.
"""
import pygame
from typing import Tuple, Optional
from models import GameState, Plot, CropType, CROP_DATABASE, Tool
from game_logic import get_plot_status


# Colors
COLOR_BACKGROUND = (34, 139, 34)  # Forest Green
COLOR_EMPTY_PLOT = (139, 69, 19)  # Brown
COLOR_LOCKED_PLOT = (105, 105, 105)  # Dim Gray
COLOR_HIGHLIGHT = (255, 255, 0)  # Yellow
COLOR_SEED = (210, 180, 140)  # Tan
COLOR_SPROUT = (144, 238, 144)  # Light Green
COLOR_GROWING = (50, 205, 50)  # Lime Green
COLOR_MATURE = (255, 215, 0)  # Gold
COLOR_WATERED = (135, 206, 250)  # Sky Blue
COLOR_TEXT = (255, 255, 255)  # White
COLOR_TEXT_DARK = (0, 0, 0)  # Black
COLOR_HUD_BG = (50, 50, 50, 200)  # Semi-transparent dark gray
COLOR_BUTTON = (70, 130, 180)  # Steel Blue
COLOR_BUTTON_HOVER = (100, 149, 237)  # Cornflower Blue


class Renderer:
    """Handles all rendering for the game"""
    
    def __init__(self, screen_width: int = 1000, screen_height: int = 800):
        """
        Initialize the renderer.
        
        Args:
            screen_width: Width of the game window
            screen_height: Height of the game window
        """
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Farm Simulator")
        
        # Layout configuration
        self.hud_height = 150
        self.sidebar_width = 250
        self.farm_area_width = screen_width - self.sidebar_width
        self.farm_area_height = screen_height - self.hud_height
        
        # Font setup
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        
        # Message system
        self.message = ""
        self.message_timer = 0
    
    def render(self, state: GameState, mouse_pos: Tuple[int, int]):
        """
        Render the entire game screen.
        
        Args:
            state: Current game state
            mouse_pos: Current mouse position
        """
        self.screen.fill(COLOR_BACKGROUND)
        
        # Calculate which plot is under mouse
        hovered_plot = self._get_plot_from_mouse(state, mouse_pos)
        
        # Render farm grid
        self._render_farm(state, hovered_plot)
        
        # Render HUD
        self._render_hud(state)
        
        # Render sidebar
        self._render_sidebar(state, hovered_plot)
        
        # Render message if active
        if self.message_timer > 0:
            self._render_message()
            self.message_timer -= 1
        
        pygame.display.flip()
    
    def _get_plot_from_mouse(self, state: GameState, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Get the plot coordinates from mouse position.
        
        Returns:
            (x, y) plot coordinates, or None if not over farm
        """
        mx, my = mouse_pos
        
        # Check if mouse is in farm area
        if my < self.hud_height or mx >= self.farm_area_width:
            return None
        
        # Calculate plot size
        tile_size = min(
            self.farm_area_width // state.farm_size,
            self.farm_area_height // state.farm_size
        )
        
        # Calculate offset to center the farm
        offset_x = (self.farm_area_width - tile_size * state.farm_size) // 2
        offset_y = self.hud_height + (self.farm_area_height - tile_size * state.farm_size) // 2
        
        # Calculate plot coordinates
        plot_x = (mx - offset_x) // tile_size
        plot_y = (my - offset_y) // tile_size
        
        if 0 <= plot_x < state.farm_size and 0 <= plot_y < state.farm_size:
            return (plot_x, plot_y)
        
        return None
    
    def _render_farm(self, state: GameState, hovered_plot: Optional[Tuple[int, int]]):
        """Render the farm grid"""
        tile_size = min(
            self.farm_area_width // state.farm_size,
            self.farm_area_height // state.farm_size
        )
        
        # Center the farm
        offset_x = (self.farm_area_width - tile_size * state.farm_size) // 2
        offset_y = self.hud_height + (self.farm_area_height - tile_size * state.farm_size) // 2
        
        for x in range(state.farm_size):
            for y in range(state.farm_size):
                plot = state.farm.get((x, y))
                if not plot:
                    continue
                
                rect_x = offset_x + x * tile_size
                rect_y = offset_y + y * tile_size
                rect = pygame.Rect(rect_x, rect_y, tile_size - 2, tile_size - 2)
                
                # Determine plot color
                color = self._get_plot_color(plot)
                pygame.draw.rect(self.screen, color, rect)
                
                # Highlight if hovered
                if hovered_plot == (x, y):
                    pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, rect, 3)
                else:
                    pygame.draw.rect(self.screen, COLOR_TEXT_DARK, rect, 1)
                
                # Draw crop indicator
                if plot.crop and tile_size > 20:
                    self._render_crop_indicator(plot, rect)
    
    def _get_plot_color(self, plot: Plot) -> Tuple[int, int, int]:
        """Get the color for a plot based on its state"""
        if not plot.unlocked:
            return COLOR_LOCKED_PLOT
        
        if plot.is_empty():
            return COLOR_EMPTY_PLOT
        
        # Type guard: we know crop is not None here
        crop = plot.crop
        if crop is None:
            return COLOR_EMPTY_PLOT
        
        crop_info = CROP_DATABASE[crop.crop_type]
        
        # Color based on growth stage
        progress_ratio = crop.days_since_plant / crop_info.growth_stages
        
        if crop.is_mature():
            return COLOR_MATURE
        elif progress_ratio >= 0.66:
            return COLOR_GROWING
        elif progress_ratio >= 0.33:
            return COLOR_SPROUT
        else:
            return COLOR_SEED
    
    def _render_crop_indicator(self, plot: Plot, rect: pygame.Rect):
        """Render a small indicator on the crop"""
        # Type guard: check if crop exists
        crop = plot.crop
        if crop is None:
            return
        
        if crop.watered:
            # Draw water droplet indicator
            center = rect.center
            pygame.draw.circle(self.screen, COLOR_WATERED, center, 5)
    
    def _render_hud(self, state: GameState):
        """Render the HUD at the top of the screen"""
        # Create semi-transparent background
        hud_surface = pygame.Surface((self.screen_width, self.hud_height))
        hud_surface.set_alpha(200)
        hud_surface.fill((40, 40, 40))
        self.screen.blit(hud_surface, (0, 0))
        
        # Render day and coins
        day_text = self.font_large.render(f"Day {state.current_day}", True, COLOR_TEXT)
        coins_text = self.font_large.render(f"💰 {state.inventory.coins} coins", True, COLOR_TEXT)
        
        self.screen.blit(day_text, (20, 20))
        self.screen.blit(coins_text, (20, 60))
        
        # Render selected crop
        crop_info = CROP_DATABASE[state.selected_crop]
        selected_text = self.font_medium.render(f"Selected: {crop_info.name}", True, COLOR_TEXT)
        seeds_text = self.font_small.render(
            f"Seeds: {state.inventory.seeds.get(state.selected_crop, 0)}", 
            True, COLOR_TEXT
        )
        
        self.screen.blit(selected_text, (300, 30))
        self.screen.blit(seeds_text, (300, 65))
        
        # Render controls hint
        controls = self.font_small.render(
            "LClick: Plant | RClick: Water | H: Harvest | N: Next Day | S: Shop | Tab: Change Crop",
            True, COLOR_TEXT
        )
        self.screen.blit(controls, (20, 110))
    
    def _render_sidebar(self, state: GameState, hovered_plot: Optional[Tuple[int, int]]):
        """Render the sidebar with plot info and stats"""
        sidebar_x = self.farm_area_width
        
        # Background
        sidebar_surface = pygame.Surface((self.sidebar_width, self.screen_height - self.hud_height))
        sidebar_surface.fill((30, 30, 30))
        self.screen.blit(sidebar_surface, (sidebar_x, self.hud_height))
        
        y_offset = self.hud_height + 20
        
        # Plot info
        if hovered_plot:
            plot = state.farm.get(hovered_plot)
            if plot:
                title = self.font_medium.render("Plot Info:", True, COLOR_TEXT)
                self.screen.blit(title, (sidebar_x + 10, y_offset))
                y_offset += 35
                
                status = get_plot_status(plot)
                status_lines = status.split('\n')
                for line in status_lines:
                    text = self.font_small.render(line, True, COLOR_TEXT)
                    self.screen.blit(text, (sidebar_x + 10, y_offset))
                    y_offset += 25
                
                y_offset += 20
        
        # Stats
        stats_title = self.font_medium.render("Statistics:", True, COLOR_TEXT)
        self.screen.blit(stats_title, (sidebar_x + 10, y_offset))
        y_offset += 35
        
        stats_lines = [
            f"Total Harvests: {state.stats.total_harvests}",
            f"Coins Earned: {state.stats.total_coins_earned}",
            f"Days Played: {state.stats.days_played}",
            f"Farm Area: {state.unlocked_area}x{state.unlocked_area}"
        ]
        
        for line in stats_lines:
            text = self.font_small.render(line, True, COLOR_TEXT)
            self.screen.blit(text, (sidebar_x + 10, y_offset))
            y_offset += 25
    
    def _render_message(self):
        """Render a temporary message"""
        text = self.font_medium.render(self.message, True, COLOR_TEXT)
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
        
        # Background
        bg_rect = text_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect)
        pygame.draw.rect(self.screen, COLOR_TEXT, bg_rect, 2)
        
        self.screen.blit(text, text_rect)
    
    def show_message(self, message: str, duration: int = 60):
        """
        Display a temporary message.
        
        Args:
            message: Message to display
            duration: How many frames to show the message
        """
        self.message = message
        self.message_timer = duration
    
    def render_shop(self, state: GameState) -> Optional[CropType]:
        """
        Render shop menu and handle shop interaction.
        
        Returns:
            CropType if player wants to buy, None otherwise
        """
        # Create shop overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(230)
        overlay.fill((20, 20, 20))
        self.screen.blit(overlay, (0, 0))
        
        # Shop title
        title = self.font_large.render("SEED SHOP", True, COLOR_TEXT)
        title_rect = title.get_rect(center=(self.screen_width // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Player coins
        coins_text = self.font_medium.render(f"Your Coins: {state.inventory.coins}", True, COLOR_TEXT)
        self.screen.blit(coins_text, (self.screen_width // 2 - 100, 100))
        
        # List crops
        y_offset = 150
        buttons = []
        
        for crop_type in CropType:
            crop_info = CROP_DATABASE[crop_type]
            
            if not crop_info.unlocked:
                continue
            
            # Create button
            button_rect = pygame.Rect(
                self.screen_width // 2 - 200,
                y_offset,
                400,
                60
            )
            buttons.append((button_rect, crop_type))
            
            # Draw button
            mouse_pos = pygame.mouse.get_pos()
            if button_rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER, button_rect)
            else:
                pygame.draw.rect(self.screen, COLOR_BUTTON, button_rect)
            pygame.draw.rect(self.screen, COLOR_TEXT, button_rect, 2)
            
            # Button text
            text = self.font_medium.render(
                f"{crop_info.name} - {crop_info.seed_cost} coins (Value: {crop_info.harvest_value})",
                True, COLOR_TEXT
            )
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
            
            y_offset += 80
        
        # Instructions
        inst_text = self.font_small.render("Click to buy 1 seed | Press ESC to close", True, COLOR_TEXT)
        inst_rect = inst_text.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
        self.screen.blit(inst_text, inst_rect)
        
        pygame.display.flip()
        
        # Wait for click
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for button_rect, crop_type in buttons:
                    if button_rect.collidepoint(mouse_pos):
                        return crop_type
        
        return None
