"""
Pygame rendering and UI system for Farm Simulator.
Handles all visual display including farm grid, HUD, and menus.
"""
import pygame
from typing import Tuple, Optional
from models import GameState, Plot, CropType, CROP_DATABASE, Tool
from game_logic import get_plot_status
import random


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
COLOR_LOCKED_BUTTON = (60, 60, 60)  # Dark Gray
COLOR_LOCKED_TEXT = (150, 150, 150)  # Light Gray
COLOR_HELP_BG = (255, 255, 240)  # Ivory
COLOR_HELP_BORDER = (139, 69, 19)  # Saddle Brown


class FloatingText:
    """Visual effect for floating text"""
    def __init__(self, text: str, x: int, y: int, color: Tuple[int, int, int] = COLOR_TEXT):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.life = 60  # Frames to live
        self.y_velocity = -1.0  # Float up

    def update(self):
        self.y += self.y_velocity
        self.life -= 1

    def is_alive(self) -> bool:
        return self.life > 0


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
        
        # Help button
        self.help_button_rect = pygame.Rect(screen_width - 40, 10, 30, 30)
        
        # Visual effects
        self.floating_texts = []
    
    def add_floating_text(self, text: str, pos: Tuple[int, int], color: Tuple[int, int, int] = COLOR_TEXT):
        """Add a floating text effect"""
        self.floating_texts.append(FloatingText(text, pos[0], pos[1], color))

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
        
        # Render help button
        self._draw_help_button(mouse_pos)

        # Render message if active
        if self.message_timer > 0:
            self._render_message()
            self.message_timer -= 1
            
        # Render and update floating texts
        for ft in self.floating_texts[:]:
            ft.update()
            if not ft.is_alive():
                self.floating_texts.remove(ft)
                continue
            
            # Fade out
            alpha = min(255, ft.life * 5)
            text_surf = self.font_medium.render(ft.text, True, ft.color)
            text_surf.set_alpha(alpha)
            self.screen.blit(text_surf, (ft.x, ft.y))
        
        # Render help overlay if active
        if state.show_help:
            self._draw_help_overlay()

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
                
                # Draw plot graphic instead of just color
                self._draw_plot_graphic(plot, rect)
                
                # Highlight if hovered
                if hovered_plot == (x, y):
                    pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, rect, 3)
                else:
                    pygame.draw.rect(self.screen, (50, 30, 10), rect, 1) # Dark brown border

    def _draw_plot_graphic(self, plot: Plot, rect: pygame.Rect):
        """Draw a procedural graphic for the plot"""
        # 1. Draw Soil
        if not plot.unlocked:
            # Locked: Grey stone pattern
            pygame.draw.rect(self.screen, (100, 100, 100), rect)
            # Draw "X" pattern
            pygame.draw.line(self.screen, (80, 80, 80), rect.topleft, rect.bottomright, 2)
            pygame.draw.line(self.screen, (80, 80, 80), rect.topright, rect.bottomleft, 2)
            return

        # Base soil color
        soil_color = (139, 69, 19)  # Dry soil
        if plot.crop and plot.crop.watered:
            soil_color = (101, 51, 14)  # Wet soil (darker)
        
        pygame.draw.rect(self.screen, soil_color, rect)
        
        # Add soil texture (simple noise)
        # We use a deterministic seed based on x,y so it doesn't flicker
        random.seed(plot.x * 100 + plot.y)
        for _ in range(5):
            dot_x = rect.x + random.randint(2, rect.width - 2)
            dot_y = rect.y + random.randint(2, rect.height - 2)
            dot_color = (120, 60, 15) if not (plot.crop and plot.crop.watered) else (80, 40, 10)
            pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y), 2)

        # 2. Draw Crop
        if plot.crop:
            self._draw_crop_graphic(plot.crop, rect)
            
            # 3. Water Indicator (Blue droplet in corner)
            if plot.crop.watered:
                drop_x = rect.right - 8
                drop_y = rect.bottom - 8
                pygame.draw.circle(self.screen, (0, 191, 255), (drop_x, drop_y), 4)

    def _draw_crop_graphic(self, crop, rect: pygame.Rect):
        """Draw the crop based on type and stage"""
        crop_info = CROP_DATABASE[crop.crop_type]
        progress = crop.days_since_plant / crop_info.growth_stages
        
        cx, cy = rect.centerx, rect.centery
        
        # Use progress ratio to determine visual stage, not just growth_stage enum
        if progress <= 0.0: # Just planted
            # Seeds: small tan dots
            pygame.draw.circle(self.screen, (210, 180, 140), (cx - 5, cy - 5), 3)
            pygame.draw.circle(self.screen, (210, 180, 140), (cx + 5, cy + 5), 3)
            pygame.draw.circle(self.screen, (210, 180, 140), (cx - 5, cy + 5), 3)
            pygame.draw.circle(self.screen, (210, 180, 140), (cx + 5, cy - 5), 3)
            
        elif progress < 0.33: # Sprout
            # Small green shoot
            pygame.draw.line(self.screen, (50, 205, 50), (cx, cy + 10), (cx, cy - 5), 3)
            pygame.draw.circle(self.screen, (50, 205, 50), (cx - 5, cy - 5), 4)
            pygame.draw.circle(self.screen, (50, 205, 50), (cx + 5, cy - 5), 4)
            
        elif progress < 1.0: # Growing
            # Taller green plant
            pygame.draw.line(self.screen, (34, 139, 34), (cx, cy + 15), (cx, cy - 10), 4)
            # Leaves
            pygame.draw.ellipse(self.screen, (50, 205, 50), (cx - 15, cy - 5, 15, 8))
            pygame.draw.ellipse(self.screen, (50, 205, 50), (cx, cy - 15, 15, 8))
            
        else: # Mature
            # Draw specific fruit/veg
            self._draw_mature_crop(crop.crop_type, rect)

    def _draw_mature_crop(self, crop_type: CropType, rect: pygame.Rect):
        """Draw the mature fruit/vegetable"""
        cx, cy = rect.centerx, rect.centery
        
        # Foliage background
        pygame.draw.circle(self.screen, (34, 139, 34), (cx, cy + 5), 15)
        
        if crop_type == CropType.WHEAT:
            # Yellow stalks
            pygame.draw.line(self.screen, (255, 215, 0), (cx - 5, cy + 15), (cx - 10, cy - 15), 3)
            pygame.draw.line(self.screen, (255, 215, 0), (cx, cy + 15), (cx, cy - 20), 3)
            pygame.draw.line(self.screen, (255, 215, 0), (cx + 5, cy + 15), (cx + 10, cy - 15), 3)
            
        elif crop_type == CropType.CARROT:
            # Orange triangle pointing down (buried) but visible top
            # Actually let's draw the leafy top and the orange top sticking out
            pygame.draw.circle(self.screen, (255, 140, 0), (cx, cy + 5), 8)
            # Big leafy greens
            pygame.draw.line(self.screen, (50, 205, 50), (cx, cy + 5), (cx - 10, cy - 15), 3)
            pygame.draw.line(self.screen, (50, 205, 50), (cx, cy + 5), (cx + 10, cy - 15), 3)
            
        elif crop_type == CropType.TOMATO:
            # Red circles
            pygame.draw.circle(self.screen, (255, 69, 0), (cx - 8, cy), 7)
            pygame.draw.circle(self.screen, (255, 69, 0), (cx + 8, cy + 5), 7)
            pygame.draw.circle(self.screen, (255, 69, 0), (cx, cy - 8), 7)
            
        elif crop_type == CropType.CORN:
            # Yellow oval with green husk
            pygame.draw.ellipse(self.screen, (255, 255, 0), (cx - 6, cy - 15, 12, 30))
            # Husk lines
            pygame.draw.arc(self.screen, (50, 205, 50), (cx - 10, cy - 10, 20, 30), 3.14, 6.28, 2)

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
        day_text = self.font_large.render(f"Day {state.current_day} ({state.season.value})", True, COLOR_TEXT)
        
        # Format time (e.g., 6.5 -> 06:30)
        hours = int(state.time)
        minutes = int((state.time - hours) * 60)
        time_str = f"{hours:02d}:{minutes:02d}"
        time_text = self.font_large.render(f"🕒 {time_str}", True, COLOR_TEXT)
        
        coins_text = self.font_large.render(f"💰 {state.inventory.coins} coins", True, COLOR_TEXT)
        
        self.screen.blit(day_text, (20, 20))
        self.screen.blit(time_text, (280, 20))
        self.screen.blit(coins_text, (20, 60))
        
        # Render Energy Bar
        energy_ratio = state.energy / state.max_energy
        bar_width = 200
        bar_height = 20
        bar_x = 700
        bar_y = 30
        
        # Background
        pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        # Fill
        fill_width = int(bar_width * energy_ratio)
        color = (0, 255, 0) if energy_ratio > 0.3 else (255, 0, 0)
        pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_width, bar_height))
        # Border
        pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        energy_text = self.font_small.render(f"Energy: {state.energy}/{state.max_energy}", True, COLOR_TEXT)
        self.screen.blit(energy_text, (bar_x, bar_y - 20))
        
        # Render selected crop
        crop_info = CROP_DATABASE[state.selected_crop]
        
        season_str = "/".join(s.value for s in crop_info.preferred_seasons) if crop_info.preferred_seasons else "All"
        is_good_season = state.season in crop_info.preferred_seasons if crop_info.preferred_seasons else True
        color = COLOR_TEXT if is_good_season else (255, 100, 100)
        
        selected_text = self.font_medium.render(f"Selected: {crop_info.name} ({season_str})", True, color)
        seeds_text = self.font_small.render(
            f"Seeds: {state.inventory.seeds.get(state.selected_crop, 0)}", 
            True, COLOR_TEXT
        )
        
        self.screen.blit(selected_text, (280, 60))
        self.screen.blit(seeds_text, (280, 85))
        
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
            
            # Create button rect
            button_rect = pygame.Rect(
                self.screen_width // 2 - 200,
                y_offset,
                400,
                60
            )
            
            if crop_info.unlocked:
                # Active button
                buttons.append((button_rect, crop_type))
                
                # Draw button
                mouse_pos = pygame.mouse.get_pos()
                if button_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER, button_rect)
                else:
                    pygame.draw.rect(self.screen, COLOR_BUTTON, button_rect)
                pygame.draw.rect(self.screen, COLOR_TEXT, button_rect, 2)
                
                # Button text
                season_str = "/".join(s.value for s in crop_info.preferred_seasons) if crop_info.preferred_seasons else "All"
                is_good_season = state.season in crop_info.preferred_seasons if crop_info.preferred_seasons else True
                season_icon = "✅" if is_good_season else "⚠️"
                
                text = self.font_medium.render(
                    f"{crop_info.name} [{season_str} {season_icon}] - {crop_info.seed_cost}g",
                    True, COLOR_TEXT
                )
            else:
                # Locked button
                pygame.draw.rect(self.screen, COLOR_LOCKED_BUTTON, button_rect)
                pygame.draw.rect(self.screen, COLOR_LOCKED_TEXT, button_rect, 2)
                
                # Locked text
                season_str = "/".join(s.value for s in crop_info.preferred_seasons) if crop_info.preferred_seasons else "All"
                text = self.font_medium.render(
                    f"{crop_info.name} [{season_str}] - LOCKED",
                    True, COLOR_LOCKED_TEXT
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

    def _draw_help_button(self, mouse_pos: Tuple[int, int]):
        """Draw the help button"""
        # Check hover
        color = COLOR_BUTTON_HOVER if self.help_button_rect.collidepoint(mouse_pos) else COLOR_BUTTON
        
        pygame.draw.rect(self.screen, color, self.help_button_rect, border_radius=15)
        pygame.draw.rect(self.screen, COLOR_TEXT, self.help_button_rect, 2, border_radius=15)
        
        text = self.font_medium.render("?", True, COLOR_TEXT)
        text_rect = text.get_rect(center=self.help_button_rect.center)
        self.screen.blit(text, text_rect)

    def is_help_button_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        """Check if help button was clicked"""
        return self.help_button_rect.collidepoint(mouse_pos)

    def _draw_help_overlay(self):
        """Draw the help overlay with game rules"""
        # Semi-transparent background
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))
        
        # Help box
        box_width = 800
        box_height = 700
        box_x = (self.screen_width - box_width) // 2
        box_y = (self.screen_height - box_height) // 2
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        
        pygame.draw.rect(self.screen, COLOR_HELP_BG, box_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_HELP_BORDER, box_rect, 3, border_radius=10)
        
        # Title
        title = self.font_large.render("Farm Simulator - Help & Rules", True, COLOR_HELP_BORDER)
        title_rect = title.get_rect(center=(self.screen_width // 2, box_y + 40))
        self.screen.blit(title, title_rect)
        
        # Content
        y_start = box_y + 80
        line_height = 30
        x_margin = box_x + 40
        
        lines = [
            "Controls:",
            "- Left Click: Interact (Plant, Water, Harvest)",
            "- Right Click: Remove Crop",
            "- 'N' Key: Advance to next day (Restores Energy)",
            "- 'S' Key: Open Shop",
            "",
            "Game Mechanics:",
            "- Energy: You have limited energy per day. Sleeping (Next Day) restores it.",
            "- Seasons: Change every 10 days. Crops have preferred seasons.",
            "- Growth: Crops need water to grow. Rain waters crops automatically.",
            "",
            "Crops:",
        ]
        
        for i, line in enumerate(lines):
            color = COLOR_HELP_BORDER if line.endswith(":") else (50, 50, 50)
            font = self.font_medium if line.endswith(":") else self.font_small
            text = font.render(line, True, color)
            self.screen.blit(text, (x_margin, y_start + i * line_height))
            
        # Crop details table
        y_crops = y_start + len(lines) * line_height + 10
        
        # Headers
        headers = ["Crop", "Season", "Growth", "Cost", "Value"]
        col_widths = [150, 150, 100, 100, 100]
        current_x = x_margin
        
        for i, header in enumerate(headers):
            text = self.font_small.render(header, True, COLOR_HELP_BORDER)
            self.screen.blit(text, (current_x, y_crops))
            current_x += col_widths[i]
            
        y_crops += 25
        pygame.draw.line(self.screen, COLOR_HELP_BORDER, (x_margin, y_crops), (x_margin + sum(col_widths), y_crops), 1)
        y_crops += 10
        
        for crop_type, info in CROP_DATABASE.items():
            season_name = "/".join(s.value for s in info.preferred_seasons) if info.preferred_seasons else "Any"
            row_data = [
                info.name,
                season_name,
                f"{info.growth_stages} days",
                f"{info.seed_cost}",
                f"{info.harvest_value}"
            ]
            
            current_x = x_margin
            for i, data in enumerate(row_data):
                text = self.font_small.render(data, True, (0, 0, 0))
                self.screen.blit(text, (current_x, y_crops))
                current_x += col_widths[i]
            y_crops += 25

        # Close instruction
        close_text = self.font_medium.render("Click anywhere or press any key to close", True, COLOR_HELP_BORDER)
        close_rect = close_text.get_rect(center=(self.screen_width // 2, box_y + box_height - 30))
        self.screen.blit(close_text, close_rect)
