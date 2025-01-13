import random#-
import json#-
from dataclasses import dataclass, field#-
import requests 

class Core:    
    @dataclass
    class NPC:
        name: str
        language_proficiency: int = 3
        emotional_state: dict = field(default_factory=lambda: {'trust': 0})

        def greet(self, game_state):
            # Access NPC emotional state through game_state if available, otherwise, uses the self copy
            npc_emotional_state = game_state.npcs.get(self.name, {}).get('emotional_state', self.emotional_state)
            print(f"{self.name} greets you warmly. Mood: {npc_emotional_state.get('trust', 'neutral')}.")

        def offer_quest(self, game_state):
            available_quests = [
                "Find the lost artifact",
                "Help me gather herbs",
                "Defeat the monster in the cave"
            ]
            quest = random.choice(available_quests)
            print(f"{self.name} offers a quest: '{quest}'")


            # Use game_state to store active quests
            game_state.active_quests[quest] = {"status": "active", "npc": self.name}

            return quest

        def build_relationship(self, game_state):
            """Build trust with the player using game_state."""

            # Update NPC's emotional state *within game_state*
            npc_data = game_state.npcs.get(self.name)

            if npc_data: #If there is an npc with that name:
                npc_data['emotional_state']['trust'] = min(10, npc_data['emotional_state'].get('trust', 0) + 1)
                print(f"{self.name} trusts you more! Trust Level: {npc_data['emotional_state']['trust']}")
            else:
                self.emotional_state['trust'] = min(10, self.emotional_state.get('trust', 0) + 1)  #Fallback if npc not found in game state.
                print(f"{self.name} trusts you more! Trust Level: {self.emotional_state['trust']}")

            # Access and update player's emotional state through game_state
            game_state.user_profile['emotional_state']['happiness'] += 1
            print(f"Player happiness: {game_state.user_profile['emotional_state']['happiness']}")

    @dataclass
    class Player:
        name: str
        level: int = 1
        language_proficiency: int = 3
        emotional_state: dict = field(default_factory=lambda: {'happiness': 0})
        encounters: list = field(default_factory=list)

        def reflect_on_choices(self, game_state):  # Add game_state parameter
            # Access emotional state through game_state
            emotional_state = game_state.user_profile['emotional_state']
            print(f"{self.name}'s emotional journey: {emotional_state}")

        def gain_experience(self, game_state, amount):  # Add game_state parameter
            self.level += amount
            print(f"{self.name} gained {amount} experience. Level: {self.level}.")

            # Example: Update player skills in game_state based on level
            if self.level > 5:
                game_state.user_profile['skills']['combat'] += 1  # Example skill update

        def complete_quest(self, game_state, quest: str):  # Add game_state parameter
            print(f"{self.name} has completed the quest: {quest}")
            self.gain_experience(game_state, 10) #Pass game_state to gain_experience

            #Remove completed quest from the active quest list within game_state.
            if quest in game_state.active_quests:
                del game_state.active_quests[quest]
            else: #Handles a non existent quest.
                print(f"The quest '{quest}' was not present in the active quest log.")


        def interact_with_npc(self, game_state, npc: 'Core.NPC'):  # Add game_state, use correct type hint
            npc.greet(game_state) # Pass game_state to npc methods
            quest = npc.offer_quest(game_state) #Pass game_state to npc methods
            self.encounters.append(quest)
            npc.build_relationship(game_state)  #Pass game_state to npc methods


        # (Rest of the Core class remains unchanged)

    @dataclass
    class MapGenerator:
        user_profile: dict = field(default_factory=lambda: {
            "current_location": {
                "country": None,
                "town": None,
                "latitude": 0,
                "longitude": 0,
                "neighborhood": None
            },
            "radius": 2000  # Initial radius in meters
        })
        
        def __init__(self, game_state):
            self.game_state = game_state  # Store game_state
            self.cached_neighborhoods = {}
            self.current_location = None

        def initialize_map(self, location):
            self.current_location = location
            self.game_state.user_profile["current_location"] = location  # Use game_state
            neighborhood = self.generate_neighborhood(location)  #Pass the location so generate_neighborhood can generate and return the correct neighborhood.
            self.game_state.user_profile["current_location"]["neighborhood"] = neighborhood  # Use game_state
            self.save_data("neighborhood_data.json")

        def generate_neighborhood(self, location):
            neighborhood = {}
            for _ in range(10):
                new_location = self.create_random_location(location)
                reference_location = self.get_real_world_reference(new_location)
                neighborhood[new_location] = {
                "name": reference_location or new_location,  # Simplified logic
                "description": reference_location or f"A newly generated location called {new_location}.", # Simplified logic
                "connects_to": [],
                "coordinates": self.generate_coordinates(location)
                }
            self.link_neighborhood_locations(neighborhood)
            return neighborhood

        def generate_coordinates(self, location):
            """Generate random coordinates around the user's location within a 2km radius."""
            return {
                "lat": location['latitude'] + random.uniform(-0.01, 0.01),
                "lng": location['longitude'] + random.uniform(-0.01, 0.01)
            }

        def create_random_location(self, base_location):
            
            """Create a random location name."""
            suffixes = ["Park", "Square", "Plaza", "Statue", "Bridge", "Spot", "Street"]
            return f"{base_location['town']} {random.choice(suffixes)}"

        def get_real_world_reference(self, location_name):
            """Get real-world reference using an API or database (placeholder)."""
            return {
                "Central Park": "A large public park in NYC.",
                "Statue of Liberty": "A colossal statue symbolizing freedom.",
                # Add other known locations and their descriptions here
            }.get(location_name, None)  # Changed from location.name to location_name

        def link_neighborhood_locations(self, neighborhood):
            """Link generated locations in the neighborhood."""
            keys = list(neighborhood.keys())
            for i in range(len(keys)):
                for j in range(i + 1, len(keys)):
                    if random.random() < 0.5:  # Randomly link locations with 50% probability
                        neighborhood[keys[i]]["connects_to"].append(keys[j])
                        neighborhood[keys[j]]["connects_to"].append(keys[i])
                        
        def view_neighborhood(self):
            """View neighborhood information (using game_state)."""
            neighborhood = self.game_state.user_profile["current_location"]["neighborhood"]  # Access through game_state
            output = "+----------------------------------------------------------+\n|                      Neighborhood                        |\n+----------------------------------------------------------+\n"
            for loc, data in neighborhood.items():
                output += f"| Location: {data['name']} - {data['description']}\n+----------------------------------------------------------+\n"
            return output

        def save_data(self, filename):
            """Save neighborhood data to a JSON file."""
            with open(filename, 'w') as f:
                json.dump(self.game_state.user_profile, f)  # Save from game_stat
            print("Neighborhood data saved successfully!")

        def load_data(self, filename):
            """Load neighborhood data from a JSON file."""
            try:
                with open(filename, 'r') as f:
                    self.game_state.user_profile = json.load(f)
                print("Neighborhood data loaded successfully!")
            except FileNotFoundError:
                print("No saved neighborhood data found.")

        def expand_neighborhood(self, increment=500):
            self.game_state.user_profile["radius"] += increment
            new_neighborhood = self.generate_neighborhood(self.game_state.user_profile["current_location"])
            self.game_state.user_profile["current_location"]["neighborhood"] = new_neighborhood
            self.save_data("neighborhood_data.json")  # No need to pass game_state here anymore
            return f"You have expanded the neighborhood! New radius: {self.game_state.user_profile['radius']} meters."

        def explore_area(self):
            """Explore the area and simulate outcome."""
            current_location = self.game_state.user_profile["current_location"]  # Access via game_state
            return f"You explore the {current_location['town']}. {self.encounter_events()}"

        def encounter_events(self):
            """Simulate various encounter events based on the user's location."""
            return random.choice([
                "You found a street musician playing a beautiful tune!",
                "You stumbled upon a lost dog looking for its owner.",
                "A street vendor offers you delicious food.",
                "A crowd gathers to watch a street performer.",
                "You discover a hidden garden behind a wall.",
            ])

        def fetch_real_world_data(self):
            """Fetch nearby places and activities."""
            current_coords = self.game_state.user_profile["current_location"]["coordinates"]
            return self.fetch_nearby_places(current_coords)

        def fetch_nearby_places(self, coordinates):
            """Simulate fetching nearby places based on the user's coordinates."""
            return [
                {"name": "Coffee Shop", "type": "cafe", "description": "A cozy place to grab a coffee."},
                {"name": "Local Grocery", "type": "store", "description": "A small grocery store with fresh produce."},
                {"name": "Art Gallery", "type": "gallery", "description": "Features local artists' works."},
                {"name": "City Library", "type": "library", "description": "A quiet place to read and study."},
                {"name": "Community Center", "type": "venue", "description": "Hosts local events and activities."}
            ]

        def procedural_generation(self):
            """Procedurally generate features in the neighborhood."""
            return [
                {"name": f"Generated Park {i + 1}", "type": "park", "description": "A beautiful green space in the neighborhood."} for i in range(5)
            ] + [
                {"name": f"Random Statue {i + 1}", "type": "statue", "description": "A whimsical statue near the pathway."} for i in range(5)
            ] + [
                {"name": f"Shop {i + 1}", "type": "shop", "description": "A local store selling crafts and goods."} for i in range(5)
            ]

        def simulate_event(self):
            """Randomly trigger an event in the neighborhood."""
            return f"A {random.choice(['festival', 'market', 'parade', 'concert', 'art exhibit', 'community gathering'])} is happening nearby! Check it out!"

        def travel_to_location(self, destination):
            """Travel to a different location."""
            print(f"Traveling to {destination}...")
            new_location = {
                "country": "USA",
                "town": destination,
                "latitude": 40.7128,
                "longitude": -74.0060
            }
            self.game_state.user_profile.location(new_location)  # Initialize map at the new location

    class EncounterManager:
        def __init__(self, game_state):
            self.game_state = game_state
            self.lore_database = self.load_lore_database()
            self.active_encounters = []

        def load_lore_database(self):
            return {
                "history": ["Ancient war between factions.", "Discovery of magical artifacts."],
                "factions": ["Red Clan", "Blue Alliance"],
                "key_characters": ["Elara the Brave", "Gorm the Wise"]
            }

        def trigger_encounter(self, npcs: list, environment: str):  # Use 'Core.Player':
            current_time = self.game_state.user_profile.get('time', 0) # Access current time.
            available_npcs = list(self.game_state.npcs.values())
            if environment == "nighttime" and available_npcs and random.random() < 0.5:  # Check for NPCs existence
                npc = random.choice(available_npcs)
                print(f"A shadowy figure approaches: {npc.name}.")
                self.handle_encounter(npc) #Handle the encounter.

        def handle_encounter(self, npc):
            choice = input(f"Do you want to talk to {npc.name}? (yes/no): ")
            if choice.lower() == 'yes':
                self.game_state.player.interact_with_npc(self.game_state, npc) # Using Player's method here
                self.game_state.player.complete_quest(npc.offer_quest())

        def initiate_communication(self, npc):
            if self.game_state.player.language_proficiency >= npc.language_proficiency:
                print(f"{npc.name} says, 'Welcome, traveler!'")
                npc.offer_quest()
                self.game_state.player.gain_experience(5)  # Reward for successful communication
            else:
                print(f"{npc.name} struggles to communicate. Try learning more languages.")

    class GameManager:
        def __init__(self, game_state): # Initialize with game_state. Remove self.npcs initialization here
            self.game_state = game_state

        def create_npc(self, name, language_proficiency=3, emotional_state=None):  # Add game_state
            if emotional_state is None:
                emotional_state = {'trust': 0}
            npc = Core.NPC(name, language_proficiency, emotional_state)

            # Store the NPC in game_state
            self.game_state.npcs[name] = {"npc_object": npc, "emotional_state": emotional_state} # Corrected to avoid overwriting. Access NPC through `npc_object`
            return npc


        def start_quest(self, quest_name, quest_details):  # Use game_state
            #Use game_state to handle quest data.
            self.game_state.active_quests[quest_name] = quest_details


        def update_quest(self, quest_name, updates): # Use game_state
            #Use game_state to update quest details
            if quest_name in self.game_state.active_quests:
                self.game_state.active_quests[quest_name].update(updates)
            else:
                print(f"Quest '{quest_name}' not found.")


        def complete_quest(self, quest_name): # Use game_state
            """Completes a quest and updates the player."""

            if quest_name in self.game_state.active_quests:
                del self.game_state.active_quests[quest_name]
                self.game_state.player.gain_experience(self.game_state, 10)  # Reward the player. Use game_state
                print(f"Quest '{quest_name}' completed!")
            else:
                print(f"Quest '{quest_name}' not found.")


        def check_active_quests(self):
            """FIX: View ongoing quests (using game_state)."""
            return self.game_state.active_quests #Access from game_state


        def list_npcs(self):
            """Lists all NPCs in the game (using game_state)."""

            if self.game_state.npcs:  # Corrected: access NPCs through GameState
                print("Available NPCs:") # Print introductory message
                for npc_name, npc_data in self.game_state.npcs.items():  # Iterate through the dictionary correctly
                    print(f"- {npc_name}")  # Print the NPC's name
            else:
                print("There are no NPCs currently in the game.") # Message if there are no NPCs



    class GameHandler:
        def __init__(self, game_state):
            self.game_state = game_state #Add game_state
            self.narrator = Core.Narrator()
            self.network_manager = Core.NetworkManager()
            self.in_game = True

        def process_input(self, user_input):
            if self.mode == "user":
                self.handle_user_mode(user_input)
            else:
                self.handle_character_mode(user_input)

        def handle_user_mode(self, user_input):
            for action in self.parse_user_input(user_input):
                if action['type'] == 'narration':
                    self.narrator.handle_narration(action['content'])
                elif action['type'] == 'interaction':
                    self.narrator.handle_interaction(action['content'])
                elif action['type'] == 'instruction':
                    self.handle_instruction(action['content'])

        def handle_character_mode(self, user_input):
            for action in self.parse_character_input(user_input):
                if action['type'] == 'narration':
                    self.game_state.narrator.handle_user_action(action['content'])
                elif action['type'] == 'instruction':
                    self.game_state.handle_instruction(action['content'])

        def parse_user_input(self, user_input):
            return [
                {'type': 'narration' if line.startswith("*") and line.endswith("*") 
                  else 'interaction' if line.startswith('"') and line.endswith('"') 
                  else 'instruction', 'content': line.strip('* "')} for line in user_input.split("\n")
            ]

        def parse_character_input(self, user_input):
            return [
                {'type': 'narration' if line.startswith("*") and line.endswith("*") 
                  else 'instruction', 'content': line.strip('* ')} for line in user_input.split("\n")
            ]

        def handle_instruction(self, instruction):
            print(f"Instruction for AI Model: handle_instruction{instruction}")

        def switch_mode(self):
            self.game_state.mode = "character" if self.mode == "user" else "user"

    class Narrator:
        def __init__(self, game_state):
            self.game_state = game_state
            self.characters = {}
            self.current_scene = ""
            self.story_progression = []  # Track storyline changes

        def add_character(self, character):
            """Add a character to the narrator's list."""
            self.game_state.characters[character.name] = character

        def start_scene(self, scene_description):
            """Set the current scene and narrate its description."""
            self.current_scene = scene_description
            print(f"<thinking>Starting the scene:</thinking>\n<output>{self.current_scene}</output>")

        def narrate(self, dialogue):
            """Handle narration."""
            print(f"<thinking>Narrating:</thinking>\n<output>{dialogue}</output>")
            self.game_state._update_story_progress(dialogue)

        def respond_to_user(self, user_input):
            """Handle user input."""
            print(f"<thinking>User says: {user_input}</thinking>")
            self.narrate("I'm considering your words carefully...")

        def flow_dialogue(self, character, dialogue):
            """Flow dialogue through the character."""
            self.game_state.narrate(character.speak(dialogue))

        def set_scene(self, scene_description):
            """Set the current scene and narrate its description."""
            self.current_scene = scene_description
            print(f"\n--- Scene Change: {self.current_scene} ---")

        def handle_narration(self, content, style='normal'):
            """Handle narration with specified style."""
            print(f"Narrator ({'dramATIC' if style == 'dramatic' else 'concise' if style == 'concise' else ''}): {self._dramatic_narration(content) if style == 'dramatic' else self._concise_narration(content) if style == 'concise' else content}")
            self.game_state._update_story_progress(content)

        def _dramatic_narration(self, content):
            """Use dramatic style for narration."""
            return f"*With a thunderous voice,* {content}"

        def _concise_narration(self, content):
            """Use concise style for narration."""
            return f"{content.strip()}."

        def handle_interaction(self, content):
            """Handle interactions with a specific format."""
            print(f"Character interaction: {content}")
            self.game_state._update_story_progress(content)

        def handle_user_action(self, content):
            """Handle user actions in character mode."""
            print(f"User action: {content}")
            self.game_state._update_story_progress(content)

        def _update_story_progress(self, content):
            """Update the storyline progression, keeping track of the history."""
            self.game_state.story_progression.append(content)

        def show_story_progression(self):
            """Display the current storyline progression."""
            print("\n--- Story Progression ---")
            for idx, entry in enumerate(self.game_state.story_progression, 1):
                print(f"{idx}. {entry}")

        def contextual_description(self, context_info):
            """Provide context-specific descriptions based on game state."""
            print(f"Description based on context: {context_info}")

        def on_command(self, command):
            """Handle specific on-demand commands from users."""
            pass  # Future implementation

        def game_loop(self):
            """Main loop for narrative-driven updates."""
            pass  # Future implementation

    class RolePlayCharacter:
        def __init__(self, game_state, name, background, personality):
            self.game_state = game_state
            self.game_state.name = name
            self.game_state.background = background
            self.game_state.personality = personality
            self.game_state.position = None
            self.game_state.emotional_state = None

        def speak(self, dialogue):
            return f"<output>{self.name}: {dialogue}</output>"

        def describe_position(self):
            return f"{self.name} is currently {self.position}."

        def set_position(self, new_position):
            self.game_state.position = new_position

        def set_emotional_state(self, state):
            self.game_state.emotional_state = state

        def perform_action(self, action):
            return f"<output>{self.name} {action}.</output>"

    class Skillset:
        def __init__(self, game_state):
            self.game_state = game_state
            self.game_state.master_story = {
                "Narrative Structure": ["Story Planning", "Storyboarding", "Scene Setting", "Exposition", "Dialogue", "Pacing"],
                "Character Development": ["Character Creation", "Character Arcs", "Motivation", "Backstory", "Relationships", "Dialogue"],
                "Plot Development": ["Story Arcs", "Plot Twists", "Suspense", "Foreshadowing", "Climax", "Resolution"],
                "Conflict Resolution": ["Antagonist", "Obstacles", "Resolutions", "Consequences", "Themes", "Symbolism"],
                "Emotional Impact": ["Emotion", "Tone", "Mood", "Atmosphere", "Imagery", "Symbolism"],
                "Delivery": ["Performance", "Voice Acting", "Public Speaking", "Stage Presence", "Audience Engagement", "Improvisation"]
            }

            self.game_state.dialog_writing_framework = {
                "1": {"Character Development": ["Background", "Personality", "Goal/Motivation"]},
                "2": {"Story Structure": ["Plot Point", "Conflict", "Resolution"]},
                "3": {"Dialogue Techniques": ["Show Don't Tell", "Subtext", "Voice Tone", "Pacing", "Visual Description"]},
                "4": {"Dialogue Editing": ["Read Aloud", "Feedback", "Revision"]}
            }

        def display_skillsets(self):
            print("Here are your skillsets:")
            for category, skills in self.game_state.master_story.items():
                print(f"{category}: {', '.join(skills)}")

        def display_dialog_writing_framework(self):
            print("\nDialog Writing Framework:")
            for level, components in self.game_state.dialog_writing_framework.items():
                print(f"Level {level}:")
                for component, techniques in components.items():
                    print(f"  {component}: {', '.join(techniques)}")

    class Secret:
        def __init__(self, game_state, description, intimacy_required, context_sensitivity, revealed_to=None):
            self.game_state = game_state
            self.game_state.description = description
            self.game_state.intimacy_required = intimacy_required
            self.game_state.context_sensitivity = context_sensitivity
            self.game_state.revealed_to = revealed_to or []

        def reveal(self, user):
            """Reveal the secret to a user."""
            if user not in self.game_state.revealed_to:
                self.game_state.revealed_to.append(user)

        def is_known_by(self, user):
            """Check if the user knows the secret."""
            return user in self.game_state.revealed_to

        def intimacy_check(self, user):
            """Check if the user's intimacy level is sufficient to reveal the secret."""
            return user.game_state.intimacy_level >= self.game_state.intimacy_required

        def context_check(self, context):
            """Check if the current context allows the secret to be revealed."""
            return context in self.game_state.context_sensitivity

    class HiddenDetail:
        def __init__(self, description, visibility_threshold):
            self.game_state.description = description
            self.game_state.visibility_threshold = visibility_threshold  # Minimum intimacy required to notice this detail

        def is_visible_to(self, user):
            """Check if a user can notice this hidden detail."""
            return user.game_state.intimacy_level >= self.game_state.visibility_threshold

    class Character:
        def __init__(self, game_state, name):
            self.game_state = game_state
            self.game_state.name = name
            self.game_state.secrets = []
            self.game_state.hidden_details = []

        def add_secret(self, secret):
            self.game_state.secrets.append(secret)

        def add_hidden_detail(self, hidden_detail):
            self.game_state.hidden_details.append(hidden_detail)

        def share_secret(self, user, context):
            for secret in self.game_state.secrets:
                if secret.game_state.intimacy_check(user) and secret.game_state.context_check(context):
                    secret.game_state.reveal(user)
                    print(f"{self.name} shared a secret with {user.name}: {secret.game_state.description}")
                    return

        def show_hidden_details(self, user):
            for detail in self.hidden_details:
                if detail.game_state.is_visible_to(user):
                    print(f"{user.name} notices {self.name}'s hidden detail: {detail.game_state.description}")

    class User:
        def __init__(self, game_state, name, intimacy_level=0, bribe_amount=0):
            self.game_state = game_state
            self.game_state.name = name
            self.game_state.intimacy_level = intimacy_level
            self.game_state.bribe_amount = bribe_amount

        def overhear_secret(self, character, context):
            for secret in character.game_state.secrets:
                if secret.game_state.context_check(context) and not secret.game_state.is_known_by(self):
                    secret.game_state.reveal(self)
                    print(f"{self.name} overheard a secret: {secret.game_state.description}")
                    return

        def attempt_bribe(self, character, context):
            character.game_state.share_secret(self, context)

    class NetworkManager:
        def __init__(self):
            self.characters = []
            self.users = []

        def add_character(self, character):
            self.characters.append(character)

        def add_user(self, user):
            self.users.append(user)

        def facilitate_interaction(self, character: 'Core.NPC', user: 'Core.Player', context):
            user.game_state.overhear_secret(character, context)  # Assumes Player has this method
            character.game_state.show_hidden_details(user)  # Assumes NPC has this method

        def display_active_characters(self):
            print(f"Active Characters: {[char.game_state.name for char in self.characters]}")

    class GameWorld:
        def __init__(self, game_state):
            self.game_state = game_state
            self.game_state.players = {}
            self.game_state.lore_database = {}
            self.game_state.encounters_history = []
            self.game_state.current_time = 0
            self.game_state.environment_conditions = ['clear', 'rainy', 'night', 'foggy']
            self.game_state.active_encounters = []
            self.game_state.load_lore_database()

        def load_lore_database(self):
            self.game_state.lore_database = {
                "history": "The world was once united, but factions emerged.",
                "factions": [
                    "The Knights of Valor",
                    "The Shadow Guild",
                    "The Merchants' Alliance"
                ],
                "key_characters": [
                    {"name": "Eldrin", "role": "Hero"},
                    {"name": "Shadow Master", "role": "Villain"}
                ]
            }

        def add_player(self, player_id, player_info):
            print(f"Adding player: {player_id}")
            self.game_state.players[player_id] = player_info

        def check_encounters(self, player_id):
            player = self.game_state.players[player_id]
            location = player.get('location')
            if self.should_trigger_encounter(player, location):
                encounter = self.generate_encounter(location)
                self.game_state.active_encounters.append(encounter)
                print(f"Encounter Triggered for {player_id}: {encounter['description']}")
                self.reward_player(player_id, encounter)

        def should_trigger_encounter(self, player, location):
            return random.random() < 0.5 if player.get('exploring_new_area', False) or self.game_state.current_time >= 18 else False

        def generate_encounter(self, location):
            return {
                "location": location,
                "description": f"Strange noises echo from the shadows in the {location}",
                "rewards": self.get_encounter_rewards()
            }

        def get_encounter_rewards(self):
            rewards = [
                "Unique Item: Enchanted Dagger",
                "Lore: Ancient Prophecy",
                "Character Development: Increased relationship with NPC"
            ]
            return random.choice(rewards)

        def reward_player(self, player_id, encounter):
            print(f"Rewarding player {player_id}: {encounter['rewards']}")

        def simulate_time_passage(self):
            self.game_state.current_time = (self.game_state.current_time + 1) % 24

        def display_lore(self):
            print("Lore Database:")
            for topic, content in self.game_state.lore_database.items():
                print(f"{topic.capitalize()}: {content if isinstance(content, str) else ', '.join(content)}")

    class EmotionalStateTracker:
        def __init__(self, game_state):
            self.game_state = game_state
            self.game_state.emotional_states = {emotion: 0 for emotion in ["happiness", "sadness", "anger", "fear", "love"]}

        def update_emotion(self, emotion, value):
            if emotion in self.game_state.emotional_states:
                self.game_state.emotional_states[emotion] = max(0, self.game_state.emotional_states[emotion] + value)

        def display_emotions(self):
            print("Current Emotional States:", self.game_state.emotional_states)

        def is_player_happy(self, player: 'Core.Player'):
            return self.game_state.emotional_states["happiness"] > 5  # Threshold for happiness check

    class CommunicationSystem:
        def __init__(self, game_state):
            self.game_state = game_state    
            self.game_state.messages = []

        def send_message(self, sender: str, recipient: str, message: str):
            self.game_state.messages.append({"from": sender, "to": recipient, "message": message})
            print(f"Message from {sender} to {recipient}: {message}")

        def view_messages(self, player_name):
            for message in self.game_state.messages:
                if message["to"] == player_name:
                    print(f"{message['from']}: {message['message']}")

    class KoboldAIIntegration:

        def __init__(self, game_state, endpoint="127.0.0.1:5001"):
            self.game_state = game_state  # Store game_state
            self.endpoint = endpoint
            self.session = requests.Session()
            self.conversation_history = []
            self.current_narration = ""
            try:
                self.generate_narration(self.game_state, "The game begins...")
            except AttributeError as e:  # Corrected to catch AttributeError
                print(f"Error during initialization: {e}")  # More specific error message
            except ConnectionError as e:
                print(f"Could not connect to KoboldAI: {e}. Check if the server is running.")

        def _get_prompt(self, game_state, user_action):
            context = f'{game_state.user_profile.get("current_narration", "")}'
            location = f'{game_state.user_profile.get("current_location", {})}'
            location_string = f"{location.get('town', 'an unknown town')}, {location.get('country', 'an unknown country')}"
            prompt = f"{context}\n\nYou are at {location_string}. You {user_action}. Continue the story:"
            return prompt


        def generate_narration(self, game_state, user_action):
            prompt = self._get_prompt(game_state, user_action)  # Pass game_state correctly
            self.game_state.current_narration = self._kobold_api_call(prompt)  # Keep the assignment here
            self.game_state.conversation_history.append({"user": user_action, "ai": self.game_state.current_narration})
            return self.game_state.current_narration

        def _kobold_api_call(self, prompt):
            headers = {'Content-Type': 'application/json'}
            payload = {
                "prompt": prompt,
                "use_story": False,
                "use_memory": True,
                "max_context_length": 24576,
                "max_length": 4000,
                "rep_pen": 1.0,
                "rep_pen_range": 2048,
                "rep_pen_slope": 0.7,
                "temperature": 0.4,
                "tfs": 0.97,
                "top_a": 0.8,
                "top_k": 0,
                "top_p": 0.5,
                "typical": 0.19,
                "sampler_order": [6, 0, 1, 3, 4, 2, 5],
                "singleline": False
        }

            try:
                response = self.session.post(f"http://{self.endpoint}/api/v1/generate", headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()
                if 'results' in response_data and response_data['results']:
                    return response_data['results'][0]['text'][:1000]  # Return truncated text
                else:
                    print(f"Unexpected response format from KoboldAI: {response_data}")
                    return "Error: Unexpected response from KoboldAI."
            except requests.exceptions.RequestException as e:
                print(f"Error communicating with KoboldAI API: {e}")
                return f"Error: Could not get a response from KoboldAI: {e}"  # More informative error message

        def save_game_state_to_history(self, game_state_data):
            self.game_state.conversation_history.append({"game_state": game_state_data}) #Correctly appends to history

        def setup(self, game_state, context):  # Takes game_state for context setup
            self.setup_story_context = context
            initial_narration = self.generate_narration(game_state, "Story begins...")  # Call with game_state

            self.game_state.current_narration = initial_narration #Set initial narration
            return initial_narration

        def get_response(self, game_state, user_input):
            if not self.setup_story_context:  # Check for initialization
                print("Error: KoboldAI not initialized. Call setup() first.")
                return "Error: KoboldAI not initialized."

            prompt = self._get_prompt(game_state, user_input)  # Pass game_state and user_input
            ai_response = self._kobold_api_call(prompt) #Use Kobold api call
            self.game_state.current_narration = ai_response
            self.game_state.conversation_history.append({"user": user_input, "ai": ai_response})
            return self.game_state.current_narration[:1000] #Return truncated response

        def save_context(self, filename="kobold_context.json", game_state=None): #Use passed game_state
            try:
                if game_state: #Checks if game_state was provided
                    context_to_save = {
                        "narration_summary": game_state.user_profile.get('current_narration', "")[:1500] # Get current_narration from game_state
                    }
                    with open(filename, 'w') as f:
                        json.dump(context_to_save, f, indent=4)
            except Exception as e:
                print(f"Error saving KoboldAI context: {e}")

        def load_context(self, filename="kobold_context.json", game_state=None):  # Corrected method signature
            try:
                with open(filename, 'r') as f:
                    loaded_context = json.load(f)
                if game_state:
                    game_state.user_profile['current_narration'] = loaded_context.get("narration_summary", "")
                return game_state.user_profile['current_narration'] 
            except (FileNotFoundError, json.JSONDecodeError) as e:  # Handle file and JSON errors
                print(f"Error loading or decoding context: {e}")
