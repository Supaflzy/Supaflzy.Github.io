# INTERFACEGEMINIDIFF.py
import json
import os
import re
import random
from Core import Core 

# GameState (Final, Copy-Pasteable Version)
class GameState:
    def __init__(self):
        # Single source of truth for user profile
        self._init_user_profile()
        self._init_game_state()
        # Core objects initialized exactly once
        self.core_objects = {}
        self.initialize_core_objects()

    def _init_user_profile(self):
        self.user_profile = {
            'name': "Traveler",
            'money': 100,
            'crew': [],
            'gear': [],
            'activity': "",
            'thoughts': "",
            'known_contacts': [],
            'budget': 100,
            'visited_countries': [],
            'current_location': {
                'country': "Unknown",
                'town': "Starting Town",
                'latitude': 0.0,
                'longitude': 0.0,
                'neighborhood': None,
            },
            'adventure_summary': 'You started your journey seeking adventure.',
            'relationship_status': "Single",
            'clues': [],
            'mysteryProgress': 0,
            'skills': {'negotiation': 1, 'combat': 1, 'cooking': 1},
            'time': 0,
            'language_proficiency': 3,
            'emotional_state': {'happiness': 5, 'sadness': 0, 'anger': 0, 'fear': 0, 'love': 0},
            'current_narration': ""
        }

    def _init_game_state(self):
        self.neighborhood = []
        self.current_location = self.user_profile['current_location']
        self.game_state = "running"
        self.locked_mode = True
        self.story_progress = {'active_story': False, 'current_genre': None}
        self.lore_database = {}
        self.dynamic_encounters = []
        self.npcs = {}
        self.active_quests = {}

    def initialize_core_objects(self):
        core_initializers = {
            'kobold_ai': lambda: Core.KoboldAIIntegration(self, endpoint="127.0.0.1:5001"),
            'map_generator': lambda: Core.MapGenerator(self),
            'narrator': lambda: Core.Narrator(self),
            'encounter_manager': lambda: Core.EncounterManager(self),
            'game_manager': lambda: Core.GameManager(self),
            'game_handler': lambda: Core.GameHandler(self),
            'emotional_state_tracker': lambda: Core.EmotionalStateTracker(self),
            'communication_system': lambda: Core.CommunicationSystem(self),
            'game_world': lambda: Core.GameWorld(self),
            'player': lambda: Core.Player(self.user_profile['name'])
            # Add other core objects here
        }

        for name, initializer in core_initializers.items():
            try:
                self.core_objects[name] = initializer()
            except Exception as e:
                print(f"Failed to initialize {name}: {e}")
                self.core_objects[name] = None

        # Set up initial narration
        if self.core_objects['kobold_ai']:
            try:
                self.user_profile['current_narration'] = self.core_objects['kobold_ai'].generate_narration(
                    self, "The adventure begins..."
                )
            except Exception:
                self.user_profile['current_narration'] = "The adventure begins..."

class StateManager:
    def __init__(self, game_state):
        self.game_state = game_state
        self.state_history = []
        self.max_history = 10

    def update_state(self, updates: dict) -> bool:
        validated_updates = SafeDataStructures.validate_user_profile(updates)
        current_state = self.game_state.user_profile.copy()
        self.state_history.append(current_state)
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
        
        self.game_state.user_profile.update(validated_updates)
        return True

    def revert_state(self) -> bool:
        if self.state_history:
            self.game_state.user_profile = self.state_history.pop()
            return True
        return False


class SafeDataStructures:
    @staticmethod
    def validate_location(location):
        required_fields = {'country', 'town', 'latitude', 'longitude'}
        if not isinstance(location, dict):
            return {'country': "Unknown", 'town': "Starting Town", 'latitude': 0.0, 'longitude': 0.0}
        return {k: location.get(k, v) for k, v in {
            'country': "Unknown",
            'town': "Starting Town",
            'latitude': 0.0,
            'longitude': 0.0
        }.items()}

    @staticmethod
    def validate_user_profile(profile):
        default_profile = {
            'name': str,
            'money': (int, float),
            'crew': list,
            'gear': list,
            'skills': dict,
            'emotional_state': dict
        }
        
        return {k: (profile.get(k) if isinstance(profile.get(k), v) else v()) 
                for k, v in default_profile.items()}

class InputValidator:
    @staticmethod
    def validate_command(command: str) -> bool:
        valid_commands = {
            'profile', 'explore', 'travel', 'save', 'load', 'exit',
            'interact', 'inventory', 'quest', 'help'
        }
        return command.lower().split()[0] in valid_commands

    @staticmethod
    def sanitize_input(user_input: str) -> str:
        return ' '.join(user_input.strip().split())

    @staticmethod
    def validate_number(value: str, min_val: int, max_val: int) -> tuple[bool, int]:
        try:
            num = int(value)
            return min_val <= num <= max_val, num
        except ValueError:
            return False, 0

class ErrorHandler:
    @staticmethod
    def handle_game_error(error_type: str, details: str) -> str:
        error_messages = {
            'input': "Invalid input. Please try again.",
            'command': "Unknown command. Type 'help' for available commands.",
            'resource': "Required resource not available.",
            'state': "Invalid game state.",
            'data': "Data error occurred.",
        }
        return f"{error_messages.get(error_type, 'An error occurred')}: {details}"


class Interface:
    GAME_TITLE = "Text Adventure Game"
    EXIT_CMD = "exit"
    MAX_NARRATION_WORDS = 300
    SAVE_TOKEN_LIMIT = 500

    def __init__(self):
    
        self.game_state = GameState()
        self.state_manager = StateManager(self.game_state)
        self.event_queue = []
        self.locations = { #Simplified locations for demonstration
            "city1": {'name': "City 1", 'landmarks': ["Landmark 1", "Landmark 2"], 'events': ["Event 1"]},
            "city2": {'name': "City 2", 'landmarks': ["Landmark 3", "Landmark 4"], 'events': ["Event 2"]},
        }

        self.game_state.initialize_core_objects()
        self.core_objects['kobold_ai'] = Core.KoboldAIIntegration(self.game_state, endpoint="127.0.0.1:5001")
        # Initialize Core objects with game_state. Order is now important.

        try: #Handle kobold initialization error.
            initial_narration = self.game_state.kobold_ai.generate_narration(self.game_state, "The game begins...")
        except (AttributeError, ConnectionError) as e:
            print(f"Error initializing KoboldAI: {e}")
            initial_narration = "Welcome to the adventure!"

        self.game_state.user_profile['current_narration'] = initial_narration
        # Initialize the rest of the Core objects AFTER KoboldAI and current_narration
        self.game_state.map_generator = Core.MapGenerator(self.game_state)
        self.game_state.narrator = Core.Narrator(self.game_state)
        self.game_state.encounter_manager = Core.EncounterManager(self.game_state)
        self.game_state.game_manager = Core.GameManager(self.game_state)
        self.game_state.game_handler = Core.GameHandler(self.game_state)
        self.game_state.emotional_state_tracker = Core.EmotionalStateTracker(self.game_state)
        self.game_state.communication_system = Core.CommunicationSystem(self.game_state)
        self.game_state.game_world = Core.GameWorld(self.game_state)
        self.game_state.skillset = Core.Skillset(self.game_state)
        self.game_state.player = Core.Player("You")


        self.init_memory()

        

    def init_memory(self):
        initial_location = self.game_state.user_profile['current_location']  # Access from game_state
        self.game_state.map_generator.initialize_map(initial_location)  # Initialize map here, using game_state
        self.game_state.narrator.set_scene("the starting area.") #Set initial scene using game_state.

        self.game_state.last_location = (initial_location['town'], 'Unknown')

                # Initialize current_narration using the now-available self.game_state.kobold_ai
        if self.game_state.kobold_ai:  # Check if KoboldAI is available
            initial_narration = self.game_state.kobold_ai.generate_narration(self.game_state, "The game begins...") # Pass the game state object
        else:
            initial_narration = "Welcome to the text adventure!"  # Fallback if KoboldAI is not available

        self.game_state.user_profile['current_narration'] = initial_narration



        # ... rest of the method from the previous response...
        #FIXED: Use the correct dictionary structure for location
        initial_location = self.game_state.user_profile['current_location']  # Access from game_state
         # Use game_state
        self.game_state.narrator.set_scene("the starting area " + self.game_state.map_generator.initialize_map(initial_location) ) 

    def display_menu(self): #Improved to properly start the adventure and include adventure selection logic

        print("Available Adventures:")
        # Example adventures. Replace with your actual adventures
        adventures = [
            {"title": "The Lost Treasure", "starting_location": {"country": "Eldoria", "town": "Silverwood", "latitude": 34.5, "longitude": -118.2}},
            {"title": "The Mystery of the Missing Scientist", "starting_location": {"country": "Atlantis", "town": "Aquatica", "latitude": 25.5, "longitude": -80.2}},
           #Add more as needed
        ]

        for i, adventure in enumerate(adventures):
            print(f"{i+1}. {adventure['title']}")


        while True:
           try:
              choice = int(input("Select an adventure (enter number): "))
              if 1 <= choice <= len(adventures):
                  adventure_data = adventures[choice-1]
                  self.start_adventure(adventure_data) #Pass the selected adventure data!
                  self.game_loop() #Start the game loop after adventure selection
                  break #Exit loop after starting game
              else:
                  print("Invalid choice. Please select a valid adventure number.")


           except ValueError:
               print("Invalid input. Please enter a number.")

    def interact_with_npc(self, npc_name):  # Example
        npc = self.game_state.npcs.get(npc_name) # Retrieve NPC data from game_state
        if npc:
            self.game_state.player.interact_with_npc(self.game_state, npc['npc_object']) # Pass game_state to Player's interact method
            # ... (rest of interaction logic using game_state)
        else:
            print(f"No NPC named '{npc_name}' found.")

    def time_flow(self):
        self.game_state.user_profile['time'] += 0.0005 # Simulating time within the game

    def show_profile(self, character=None):
        if character is None:
            character = self.game_state.user_profile
        return f"""
            Name: {character['name']}
            Money: {character['money']}
            Current Location: {character['current_location']}
            Crew: {', '.join(character['crew']) or "No crew"}
            Gear: {', '.join(character['gear']) or "No gear"}
            Thoughts: {character['thoughts'] or "No thoughts"}
            Known Contacts: {', '.join(character['known_contacts']) or "No known contacts"}
            Visited Countries: {', '.join(character['visited_countries']) or "None"}
            Relationship Status: {character['relationship_status']}
            Skills: {character['skills']}
            Time: {character['time']} hours
            Mystery Progress: {character['mysteryProgress']}
            Language Proficiency: {character['language_proficiency']}
            Emotional State: {character['emotional_state']}
        """

    def calculate_time_passage(self, action):
        time_units = {
            'year': 365,
            'month': 30,
            'week': 7,
            'day': 1,
            'hour': 1 / 24,
            'minute': 1 / 1440,
            'second': 1 / 86400,
        }

        pattern = r'(\d+)\s*(year|month|week|day|hour|minute|second)s?'
        total_time = sum(int(num) * time_units[unit] for num, unit in re.findall(pattern, action))
        return total_time

    def travel_method(self, choice):
        methods = {
            1: ("Train", 30, 3),
            2: ("Plane", 50, 5),
            3: ("Boat", 20, 4)
        }
        
        method_data = methods.get(choice)
        if not method_data:
            return "Invalid travel method"
            
        method, cost, time = method_data
        if self.game_state.user_profile['money'] >= cost:
            self.game_state.user_profile['money'] -= cost
            self.game_state.user_profile['time'] += time
            return f"Traveled by {method}. Cost: {cost}, Time taken: {time} hours"
        
        return "Insufficient funds for travel"

    def add_remove_item(self, action, gear_type):
        item = input(f"Enter the name of the {gear_type} to {action}: ")
        user_profile = self.game_state.user_profile  # Use game_state

        if action == "add":
            user_profile[gear_type].append(item)  # Correct key access
            narration = f"{item} added to {gear_type}."
            self.game_state.narrator.handle_narration(narration) # Use game_state
            return narration
        elif action == "remove" and item in user_profile[gear_type]:  # Correct key access
            user_profile[gear_type].remove(item)
            narration = f"{item} removed from {gear_type}."
            self.game_state.narrator.handle_narration(narration)  # Use game_state
            return narration
        return f"{item} not in {gear_type}."

    def explore_location(self, city):
        if not isinstance(city, str):
            return "Invalid location format"
        
        location_data = self.locations.get(city)
        if not location_data:
            return "Location not found"
            
        self.game_state.update_location({
            'country': location_data['name'],
            'town': city,
            'latitude': 0.0,
            'longitude': 0.0
        })
        
        landmarks = ', '.join(location_data.get('landmarks', []))
        events = ', '.join(location_data.get('events', []))
        
        narration = f"Exploring {city}. Landmarks: {landmarks}. Events: {events}."
        self.game_state.narrator.handle_narration(narration)
        return narration

    def show_story(self): #Updated to use game_state
        current_location_data = self.game_state.user_profile.get('current_location', {}) #Access safely through game_state
        loc = current_location_data.get('town', 'an unknown place') #Access safely from the current_location dictionary.
        narration = f"You are currently in {loc}. What adventures await?"
        self.game_state.narrator.handle_narration(narration)  # Use game_state.
        return narration

    def generate_daily_scenario(self): #Updated to use game_state
        current_location_data = self.game_state.user_profile.get('current_location', {})  # Access through game_state
        loc = current_location_data.get('town', 'an unknown place')  # Access from the location data

        activities = [
            f" trying the famous dish from {loc}.",
            f" visiting a local market in {loc}.",
            f" meeting a new friend at a cafe in {loc}.",
            f" exploring a beautiful park in {loc}."
        ]
        new_activity = random.choice(activities)
        self.game_state.user_profile['activity'] = new_activity
        self.game_state.user_profile['thoughts'] += new_activity
        narration = f"Daily adventure: You{new_activity}"
        self.narrator.handle_narration(narration)
        return narration

    def save_game(self):
        save_data = {
            'user_profile': self.game_state.user_profile,
            'story_progress': self.game_state.story_progress,
            'npcs': self.game_state.npcs,
            'active_quests': self.game_state.active_quests,
            'game_state': self.game_state.game_state,
            'locked_mode': self.game_state.locked_mode
        }

        try:
            with open('save_game.json', 'w', encoding='utf-8') as f:
                json_data = json.dumps(save_data, indent=2)
                if len(json_data) > self.SAVE_TOKEN_LIMIT:
                    json_data = json_data[:self.SAVE_TOKEN_LIMIT]
                f.write(json_data)
            self.game_state.narrator.handle_narration("Game saved successfully.")
            return True
        except IOError as e:
            self.game_state.narrator.handle_narration(f"Save failed: {str(e)}")
            return False

    def load_game(self):
        try:
            with open('save_game.json', 'r', encoding='utf-8') as f:
                load_data = json.load(f)
                
            # Validate required keys
            required_keys = ['user_profile', 'story_progress', 'npcs', 'active_quests']
            if not all(key in load_data for key in required_keys):
                raise ValueError("Save file is missing required data")
                
            # Update game state with loaded data
            self.game_state.user_profile.update(load_data['user_profile'])
            self.game_state.story_progress = load_data['story_progress']
            self.game_state.npcs = load_data['npcs']
            self.game_state.active_quests = load_data['active_quests']
            
            # Reinitialize necessary components
            self.game_state.map_generator.initialize_map(self.game_state.user_profile['current_location'])
            
            self.game_state.narrator.handle_narration("Game loaded successfully.")
            return True
            
        except (json.JSONDecodeError, IOError, ValueError) as e:
            self.game_state.narrator.handle_narration(f"Load failed: {str(e)}")
            return False

    def cleanup_resources(self):
        """Ensure proper cleanup of game resources"""
        try:
            # Save final game state
            self.save_game()
            
            # Clean up core objects
            for name, obj in self.game_state.core_objects.items():
                if hasattr(obj, 'cleanup'):
                    try:
                        obj.cleanup()
                    except Exception as e:
                        print(f"Error cleaning up {name}: {e}")
                        
            # Reset game state
            self.game_state.game_handler.in_game = False
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            print("Game resources cleaned up.")

    def display_adventure_interface(self, width=80, title=None, options="Profile, Explore, Save Game, Load Game, Exit"):
        title = title or self.GAME_TITLE
        icons = ["🗺️", "⚔️", "🛡️", "🌟", "🏰", "🐉", "💎", "🌲", "🚀", "🎩"]

        selected_options = [opt.strip() for opt in options.split(",") if opt.strip()]

        def centered_content(content, total_width):
            padding = (total_width - len(content)) // 2
            return " " * padding + content + " " * padding

        def bordered_line(content, width):
            return f"| {content.ljust(width - 4)} |"

        def create_box(title, content, width):
            lines = content.split("\n")
            box = ["+" + "-" * (width - 2) + "+"]
            title_icon = random.choice(icons)
            box.append(bordered_line(f"{title_icon} {title}", width))
            box.append("|" + "-" * (width - 2) + "|")
            for line in lines:
                box.append(bordered_line(line.strip(), width))
            box.append("+" + "-" * (width - 2) + "+")
            return "\n".join(box)

        options_display = [f"{random.choice(icons)} [{option}]" for option in selected_options]
        options_line = bordered_line(" | ".join(options_display), width) if options_display else bordered_line("No Options Available", width)
        
        content_to_display = self.show_profile() if "Profile" in selected_options else self.show_story()
        
        story_box = create_box("Current View", content_to_display, width)

        print("+" + "-" * (width - 2) + "+")
        print(bordered_line(centered_content(title, width - 4), width))
        print("|" + "=" * (width - 2) + "|")
        print(options_line)
        print("|" + "=" * (width - 2) + "|")
        print(story_box)
        print("+" + "-" * (width - 2) + "+")

    def context_aware_encounters(self):
        player_status =self.game_state.user_profile
        if player_status['current_location'] == "starting area" and random.random() < 0.5:
            self.map_generator.initialize_map(player_status['current_location'])
            self.narrator.handle_narration("A mysterious traveler offers a quest!")
        if random.random() < 0.3:
            self.narrator.handle_narration(f"You received a {random.choice(['unique item', 'lore discovery', 'character development opportunity'])}!")

    def narrate_npc_interaction(self, npc):
        if hasattr(npc, 'name') and hasattr(npc, 'emotional_state'):
            narration = f"{npc.name} greets you warmly. Mood: {npc.emotional_state.get('trust', 'neutral')}."
            self.narrator.handle_interaction(narration)

    def start_story(self):
        user_country =self.game_state.user_profile.get("current_location")
        story = f"You set out from {user_country}!"
        self.game_state.story_progress['active_story'] = True
        self.game_state.current_story = story
        self.narrator.handle_narration(story)
        return self.display_adventure_interface(title="🌍 Adventure Started", options="Explore, Travel, Save Game, Load Game, Exit")

    def start_adventure(self, adventure_data):
        current_location = adventure_data.get('starting_location', self.game_state.user_profile['current_location'])
        story_title = adventure_data.get('title', "Untitled Adventure")
        plot_summary = adventure_data.get('plot_summary', "A mysterious adventure unfolds...")

        self.game_state.user_profile['current_location'] = current_location # Use the current_location *dictionary*, not just the country name.
        self.game_state.map_generator.initialize_map(current_location)
        self.game_state.user_profile['current_location'] = current_location

        if self.game_state.kobold_ai:
            game_state_data = {
                "current_location": current_location,
                "story_title": story_title,
                "plot_summary": plot_summary
            }
            self.game_state.kobold_ai.save_game_state_to_history(game_state_data)  # Corrected call
            kobold_context = {  #Create correct kobold_context
                "user_profile": self.game_state.user_profile,
                "current_location": current_location,
                "story_title": story_title,
                "plot_summary": plot_summary
            }
            self.game_state.kobold_ai.setup(self.game_state, kobold_context) # Pass game_state
            intro_narration = self.game_state.narrator.start_scene(f"You embark on a new adventure: {story_title}")
            self.game_state.user_profile['current_narration'] = intro_narration

    def _generate_episodic_content(self, user_input):
        """Enhanced story generation with full genre variety and method integration"""

        genres = {
            "detective": {"themes": ["noir", "procedural", "private eye", "true crime"]},
            "scifi": {"themes": ["space opera", "cyberpunk", "time travel", "post-apocalyptic"]},
            "romance": {"themes": ["rom-com", "drama", "historical", "contemporary"]},
            "documentary": {"themes": ["nature", "historical", "biographical", "investigative"]},
            "horror": {"themes": ["psychological", "supernatural", "slasher", "cosmic"]},
            "comedy": {"themes": ["sitcom", "dark comedy", "satire", "slapstick"]},
            "drama": {"themes": ["medical", "legal", "family", "political"]},
            "fantasy": {"themes": ["high fantasy", "urban", "magical realism", "mythological"]},
            "thriller": {"themes": ["psychological", "action", "conspiracy", "espionage"]},
            "western": {"themes": ["classical", "modern", "space western", "neo-western"]},
            "sports": {"themes": ["underdog", "comeback", "team building", "competition"]},
            "musical": {"themes": ["broadway", "rock opera", "dance", "biographical"]},
            "adventure": {"themes": ["exploration", "treasure hunt", "survival", "journey"]},
            "war": {"themes": ["historical", "futuristic", "resistance", "espionage"]},
            "crime": {"themes": ["heist", "mob", "white collar", "international"]},
            "supernatural": {"themes": ["paranormal", "mythical", "urban fantasy", "occult"]}
        }

        # Access current_location as a dictionary
        current_location = self.game_state.user_profile['current_location']
        current_country = current_location.get('country', "Unknown")  # Safely access 'country'


        daily_events = self.generate_daily_scenario()

        # Use existing travel method for location-specific content
        if hasattr(self.game_state, 'last_location') and self.game_state.last_location != current_location['town']:
            travel_narrative = self.travel_method(random.randint(1, 3))
            self.narrator.handle_narration(travel_narrative)


        if 'current_genre' not in self.game_state.story_progress or random.random() < 0.2:  # Corrected: "not in"
            self.game_state.story_progress['current_genre'] = random.choice(list(genres.keys()))
            self.game_state.story_progress['episode_number'] = 1
            self.game_state.story_progress['season'] = 1

        genre = self.game_state.story_progress['current_genre']
        theme = random.choice(genres[genre]["themes"])
        episode = self.game_state.story_progress['episode_number']
        season = self.game_state.story_progress['season']

        episode_clues = self.generate_clues()
        encounters = self.generate_random_encounters()

        # Use current_country for location-specific story elements
        location_story = self.generate_story(current_country)

        episode_title = f"S{season}E{episode}: {theme.title()} in {current_country}"  # Use current_country

        emotional_impact = self.emotional_state_tracker.update_emotional_state(genre, theme)
        self.context_aware_encounters()
        
        story = {
            "title": episode_title,
            "genre": genre,
            "theme": theme,
            "setting": current_location,
            "daily_events": daily_events,
            "plot": location_story["plot"],
            "clues": episode_clues,
            "encounters": encounters,
            "emotional_state": emotional_impact
        }

        self.narrator.handle_narration(f"Beginning new episode: {episode_title}")
        self.narrator.set_scene(f"In {current_country}, a {theme} story unfolds...")  # Use current_country

        self.game_state.story_progress['episode_number'] += 1
        if self.game_state.story_progress['episode_number'] > 12:  # Corrected: Indentation and colon
            self.game_state.story_progress['season'] += 1
            self.game_state.story_progress['episode_number'] = 1
            new_genre = random.choice([g for g in genres.keys() if g != genre])
            self.game_state.story_progress['current_genre'] = new_genre
            self.narrator.handle_narration(f"Season {season} finale! Next season will feature {new_genre} stories!")

        if self.game_state.user_profile['current_location'] == current_location:  #Corrected: No semicolon, proper comparison
            next_scenario = self.generate_daily_scenario()
            self.narrator.handle_narration(f"Meanwhile... {next_scenario}")

        self.display_adventure_interface(
            title=episode_title,
            options="Investigate, Interact, Travel, Profile, Save Game, Exit"
        )

        return story

    def update_game_progress(self, action_result: dict) -> dict:
        updates = {
            'time': self.game_state.user_profile['time'] + action_result.get('time_cost', 0),
            'money': self.game_state.user_profile['money'] + action_result.get('money_change', 0),
            'mysteryProgress': self.game_state.user_profile['mysteryProgress'] + action_result.get('progress', 0)
        }
        
        self.state_manager.update_state(updates)
        return updates

    def process_events(self):
        while self.event_queue:
            event = self.event_queue.pop(0)
            if event['type'] == 'encounter':
                self.handle_encounter(event)
            elif event['type'] == 'quest':
                self.handle_quest_update(event)
            elif event['type'] == 'story':
                self.advance_story(event)

    def handle_encounter(self, encounter: dict):
        if not self.game_state.encounter_manager:
            return "Encounter system not available"
            
        result = self.game_state.encounter_manager.process_encounter(encounter)
        self.update_game_progress(result)
        return result.get('narration', 'Encounter completed')

    def advance_story(self, story_event: dict):
        current_progress = self.game_state.user_profile['mysteryProgress']
        new_progress = min(100, current_progress + story_event.get('progress', 5))
        
        updates = {
            'mysteryProgress': new_progress,
            'adventure_summary': f"{self.game_state.user_profile['adventure_summary']} {story_event.get('summary', '')}"
        }
        
        self.state_manager.update_state(updates)
        return new_progress

    def handle_quest_update(self, quest_event: dict):
        quest_id = quest_event.get('quest_id')
        if quest_id in self.game_state.active_quests:
            quest = self.game_state.active_quests[quest_id]
            quest['progress'] += quest_event.get('progress', 1)
            
            if quest['progress'] >= quest['required_progress']:
                self.complete_quest(quest_id)

    def complete_quest(self, quest_id: str):
        quest = self.game_state.active_quests.pop(quest_id)
        rewards = quest.get('rewards', {})
        
        updates = {
            'money': self.game_state.user_profile['money'] + rewards.get('money', 0),
            'gear': self.game_state.user_profile['gear'] + rewards.get('items', [])
        }
        
        self.state_manager.update_state(updates)
        return f"Quest completed! Rewards: {rewards}"

    def _placeholder_method(self, user_input): #FIXED: Added _ to clearly denote an internal method
        """Placeholder for new interface methods.  Copy and modify as needed."""
        # 1. Extract relevant information from user_input (e.g., keywords, parameters)
        # 2. Update game state (self.mem_store) if necessary
        # 3.  Call self.kobold_ai.get_response() to generate narrative text
        # 4.  Return or print the generated text

        narration = self.kobold_ai.get_response(user_input) #Generating the narration using KoboldAI
        print(narration) #print to terminal, update later for production
        return narration


        # Save game state *after* initializing relevant data. FIXED: Moved to ensure accurate initial state
        game_state_data = {
            "current_location": current_location,
            "story_title": story_title,
            "plot_summary": plot_summary,
            # ... other relevant info
        }
        self.kobold_ai.save_game_state_to_history(game_state_data)

    def generate_story(self, country):
        if country == "USA":
            self.game_state.map_generator.initialize_map({"country": "USA", "town": "Anytown USA"})       
            genre = "detective"
            return {
                "genre": genre,
                "title": "The Great American Mystery",
                "plot": "You're a freelance detective gathering clues across the city...",
                "clues": self.generate_clues(),
                "endings": ["success", "failure", "mystery unresolved"],
                "random_encounters": self.generate_random_encounters()
            }
        elif country == "England":
            self.game_state.map_generator.initialize_map({"country": "England", "town": "London"})  
            genre = "sci-fi"
            return {
                "genre": genre,
                "title": "The Sci-fi Chronicles",
                "plot": "You find yourself in a futuristic England with high-tech mysteries...",
                "clues": self.generate_clues(),
                "endings": ["success", "tragedy", "happy ending"],
                "random_encounters": self.generate_random_encounters()
            }
        else:
            self.game_state.map_generator.initialize_map({"country": country, "town": "Generic Town"})
            genre = "adventure"
            return {
                "genre": genre,
                "title": "The Global Quest",
                "plot": "You embark on a journey around the world...",
                "clues": self.generate_clues(),
                "endings": ["success", "failure", "mixed outcome"],
                "random_encounters": self.generate_random_encounters()
            }

    def generate_clues(self):
        return [
            "A suspicious person was seen near the library.",
            "A receipt found at the crime scene leads to a cafe.",
            "Witnesses mentioned hearing a strange sound last night."
        ]

    def generate_random_encounters(self):
        return [
            "You encounter a mysterious stranger in the alley.",
            "Someone asks you for directions and seems suspicious.",
            "You overhear a conversation about a recent theft."
        ]

    def display_story_intro(self, story):
        intro_narration = self.game_state.narrator.start_scene("You awaken in a mysterious land...")# Get intro from Narrator
        self.game_state.user_profile['current_narration'] = intro_narration  # Store the intro narration in memory

        clues = "\n  - ".join(story["clues"])
        return self.display_adventure_interface(title=f"📜 {story['title']}", options=f"""
          | {story['plot']}                                   |
          |                                                       |
          | Your mission is to gather clues and solve the mystery. |
          |                                                       |
          | Clues to find:                                       |
          |  - {clues}                     |
          |                                                       |
          | [Type 'start' to begin gathering clues]              |
          | [Type 'exit' to leave the adventure]                 |
        """)

    def show_progress(self):
        clues_found = self.game_state.user_profile.get('clues', [])
        total_clues = len(self.game_state.user_profile['clues'])
        clues_summary = f"{len(clues_found)} clue(s) collected out of {total_clues}.\n\n"
        
        clues_summary += "Clues found:\n"
        for clue in clues_found:
            clues_summary += f"  - {clue}\n"
            
        return clues_summary + "\nHints:\n"  # You may want to implement the get_hints() method.

    def encounter_event(self, encounter):
        outcome = "You gained valuable information!" if random.random() < 0.7 else "The encounter was unhelpful."
        self.narrator.handle_narration(outcome)  # Added narration of the outcome.
        return outcome

    def travel_to_new_location(self):
        destinations = ["USA", "England", "Japan", "Brazil", "Canada"]
        new_country = random.choice(destinations)
        self.game_state.user_profile['current_location'] = new_country
        
        new_location = {"country": new_country, "town": new_country} #Removed coordinates, no longer required.
        self.game_state.map_generator.initialize_map(new_location) #Correct usage of game_state.
        
        return self.display_adventure_interface(title="✈️ Traveling", options=f"""
          | You have traveled to {new_country}!               |
          | New story generated based on your location.        |
          |                                                       |
          | [Type 'start story' to begin anew]                 |
          | [Type 'exit' to leave the adventure]                |
        """)

    def exit_story(self):
        self.game_state.story_progress['active_story'] = False
        return "You have exited the adventure. Thank you for playing!"

    def on_command(self, input_):
        commands = {
            "show profile": self.show_profile,
            "start game": self.start_interface,
            "start story": lambda: self.start_story(),
            "explore city2": lambda: self.explore_location("city2"),
            "save game": self.save_game,
            "load game": self.load_game,
            "exit": lambda: self.exit_story(),
            "start adventure": lambda: self.start_adventure(),
            "generate daily scenario": self.generate_daily_scenario,
            "next episode": lambda: self._generate_episodic_content(input_),
            "story summary": lambda: self.show_progress(),
            "explore": lambda: self.explore_location(self.game_state.user_profile['current_location']),
        }

        if input_.lower().strip() == "do nothing":
            return "You spent time doing nothing."
        
        try:
            choice = int(input_)
            return self.travel_method(choice)
        except ValueError:
            pass  # Continue to check commands
            action = commands.get(input_.lower().strip())
        
        if action is None:
            time_estimate = self.calculate_time_passage(input_) or 0.010
            current_time =self.game_state.user_profile['time']
            self.game_state.user_profile['time'] += time_estimate
            return f"Time passed: from {current_time:.2f} to {self.game_state.user_profile['time']:.2f} hours."
        


        return action() if action else "Command not recognized."

    def handle_user_input(self, raw_input: str) -> str:
        try:
            sanitized_input = InputValidator.sanitize_input(raw_input)
            
            if not sanitized_input:
                return ErrorHandler.handle_game_error('input', "Empty input")
                
            if not InputValidator.validate_command(sanitized_input):
                return ErrorHandler.handle_game_error('command', sanitized_input)
                
            command_parts = sanitized_input.split()
            command = command_parts[0].lower()
            args = command_parts[1:]
            
            return self.execute_command(command, args)
            
        except Exception as e:
            return ErrorHandler.handle_game_error('data', str(e))

    def execute_command(self, command: str, args: list) -> str:
        command_handlers = {
            'profile': self.show_profile,
            'explore': lambda: self.explore_location(args[0]) if args else "Specify location",
            'travel': lambda: self.handle_travel(args),
            'interact': lambda: self.interact_with_npc(args[0]) if args else "Specify NPC",
            'inventory': self.show_inventory,
            'help': self.show_help
        }
        
        handler = command_handlers.get(command)
        if not handler:
            return ErrorHandler.handle_game_error('command', command)
            
        try:
            return handler()
        except Exception as e:
            return ErrorHandler.handle_game_error('data', str(e))

    def handle_travel(self, args: list) -> str:
        if not args:
            return "Specify travel method (1-3)"
            
        is_valid, choice = InputValidator.validate_number(args[0], 1, 3)
        if not is_valid:
            return "Invalid travel method number"
            
        return self.travel_method(choice)

    def update_game_progress(self, action_result: dict) -> dict:
        updates = {
            'time': self.game_state.user_profile['time'] + action_result.get('time_cost', 0),
            'money': self.game_state.user_profile['money'] + action_result.get('money_change', 0),
            'mysteryProgress': self.game_state.user_profile['mysteryProgress'] + action_result.get('progress', 0)
        }
        
        self.state_manager.update_state(updates)
        return updates

    def process_events(self):
        while self.event_queue:
            event = self.event_queue.pop(0)
            if event['type'] == 'encounter':
                self.handle_encounter(event)
            elif event['type'] == 'quest':
                self.handle_quest_update(event)
            elif event['type'] == 'story':
                self.advance_story(event)

    # First batch of fixes - Game Loop and State Management
    def game_loop(self):
        try:
            while self.game_state.game_handler.in_game:
                self.time_flow()
                self.display_adventure_interface()
            
                user_input = input("What would you like to do? ").lower().strip()
            
                if user_input == self.EXIT_CMD:
                    self.game_state.narrator.handle_narration("Exiting the adventure.")
                    self.game_state.game_handler.in_game = False
                    break
                
                # Consolidated input handling
                if user_input.startswith("interact with "):
                    npc_name = user_input.split(" ")[-1]
                    if npc_name in self.game_state.npcs:
                        npc = self.game_state.npcs[npc_name].get('npc_object')
                        if npc:
                            narration = f"You interact with {npc.name}."
                            self.game_state.narrator.handle_interaction(narration)
                            self.narrate_npc_interaction(npc)
                        else:
                            print(f"Invalid NPC object for '{npc_name}'")
                    else:
                        print(f"No NPC found with the name '{npc_name}'")
                    continue
                
                # Travel handling with proper validation
                if user_input.startswith("travel"):
                    try:
                        print("Select travel method:\n1. Train\n2. Plane\n3. Boat")
                        choice = int(input("Enter number (1-3): "))
                        if 1 <= choice <= 3:
                            print(self.travel_method(choice))
                        else:
                            print("Please select a number between 1 and 3.")
                    except ValueError:
                        print("Please enter a valid number.")
                    continue
                
                # Resource management with context managers
                if user_input == "save game":
                    self.save_game()
                elif user_input == "load game":
                    self.load_game()
                else:
                    result = self.on_command(user_input)
                    if isinstance(result, str) and result != "Command not recognized.":
                        if self.game_state.kobold_ai:
                            try:
                                ai_narration = self.game_state.kobold_ai.get_response(self.game_state, result)
                                truncated_narration = ai_narration[:self.MAX_NARRATION_WORDS]
                                self.game_state.user_profile['current_narration'] = truncated_narration
                                print(truncated_narration)
                            except Exception as e:
                                print(f"Error generating narration: {e}")
                            
                # Mode switching with validation
                mode_choice = input("Switch mode (character/user)? ").strip().lower()
                if mode_choice in ["character", "user"]:
                    self.game_state.game_handler.mode = mode_choice
                    self.game_state.narrator.handle_user_action(f"Switched to {mode_choice.capitalize()} Mode.")
                
                user_input = input("> ")
                if user_input.lower() == 'exit':
                    break
                    
                result = self.handle_user_input(user_input)
                print(result)
                
                if self.game_state.kobold_ai and isinstance(result, str):
                    narration = self.game_state.kobold_ai.get_response(self.game_state, result)
                    print(narration[:self.MAX_NARRATION_WORDS])
                    
        except KeyboardInterrupt:
                print("\nSaving game...")
                self.save_game()
                self.game_state.game_handler.in_game = False
                self.game_state.game_handler.save_game()
                self.game_state.game_handler.close_files()
                print("Game saved. Exiting...")
                exit()

        except Exception as e:
                print(ErrorHandler.handle_game_error('data', str(e)))
        def cleanup_resources(self):
            # Cleanup resources and close any open files
            self.game_state.game_handler.in_game = False
            self.game_state.game_handler.save_game()
            self.game_state.game_handler.close_files()
    


    def start_interface(self):
        self.display_menu()

    def main(self):
        self.load_game()
        initial_location = {
            "country": "South Africa", 
            "town": "Soweto", 
            "latitude": -26.229622, 
            "longitude": 27.873667
        }
        self.game_state.user_profile['current_location'] = initial_location

        # Properly indented code block
        self.map_generator.user_profile = {
            "current_location": {
                "coordinates": {
                    "latitude": initial_location["latitude"],
                    "longitude": initial_location["longitude"]
                }
            }
        }

        print(self.map_generator.fetch_real_world_data())  # This needs to align with the previous line 

        self.start_interface()    


if __name__ == "__main__":
    interface = Interface()
    interface.main()
