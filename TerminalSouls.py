from enum import Enum
from typing import List, Dict, Optional, Set, Tuple
import os
import random
import time

# ============================================================================
# ENUMERAZIONI E COSTANTI
# ============================================================================

class ItemCategory(Enum):
    WEAPON = "arma"
    ARMOR = "armatura"
    CONSUMABLE = "consumabile"
    KEY_ITEM = "oggetto chiave"
    MATERIAL = "materiale"
    MISC = "vario"

class EntityType(Enum):
    ENEMY = "nemico"
    NPC = "npc"
    MERCHANT = "mercante"
    BOSS = "boss"
    ITEM = "oggetto"

class QuestStatus(Enum):
    NOT_STARTED = "non iniziata"
    IN_PROGRESS = "in corso"
    COMPLETED = "completata"
    FAILED = "fallita"

# ============================================================================
# SISTEMA DI QUEST
# ============================================================================

class Quest:
    """Rappresenta una missione"""
    def __init__(self, name: str, description: str, giver: str, 
        objectives: List[str], reward_coins: int = 0, 
        reward_items: List[str] = None, unlock_location: str = ""):
        self.name = name
        self.description = description
        self.giver = giver
        self.objectives = objectives
        self.completed_objectives: Set[int] = set()
        self.status = QuestStatus.NOT_STARTED
        self.reward_coins = reward_coins
        self.reward_items = reward_items or []
        self.unlock_location = unlock_location
    
    def start(self):
        self.status = QuestStatus.IN_PROGRESS
    
    def complete_objective(self, index: int):
        self.completed_objectives.add(index)
        if len(self.completed_objectives) == len(self.objectives):
            self.status = QuestStatus.COMPLETED
    
    def is_completed(self) -> bool:
        return self.status == QuestStatus.COMPLETED
    
    def get_progress(self) -> str:
        if self.status == QuestStatus.NOT_STARTED:
            return "Non iniziata"
        elif self.status == QuestStatus.COMPLETED:
            return "COMPLETATA"
        else:
            completed = len(self.completed_objectives)
            total = len(self.objectives)
            return f"In corso ({completed}/{total})"

# ============================================================================
# SISTEMA DI COMBATTIMENTO
# ============================================================================

class CombatSystem:
    """Gestisce il combattimento"""
    
    @staticmethod
    def calculate_damage(attacker_power: int, defender_defense: int) -> int:
        """Calcola il danno inflitto"""
        base_damage = max(1, attacker_power - defender_defense // 2)
        variance = random.randint(-1, 2)
        return max(1, base_damage + variance)
    
    @staticmethod
    def combat_round(player, enemy, player_action: str = "attack") -> Tuple[str, bool, bool]:
        """
        Esegue un round di combattimento
        Returns: (messaggio, player_alive, enemy_alive)
        """
        output = []
        
        # Turno del giocatore
        if player_action == "attack":
            damage = CombatSystem.calculate_damage(player.get_total_attack(), enemy.defense)
            enemy.current_health -= damage
            
            output.append(f"Attacchi {enemy.name}!")
            output.append(f"Infliggi {damage} danni!")
            
            if enemy.current_health <= 0:
                enemy.is_alive = False
                output.append(f"\n{enemy.name} è stato sconfitto!")
                return "\n".join(output), True, False
        
        elif player_action == "defend":
            output.append(f"Ti metti in difesa!")
            player.defending = True
        
        # Turno del nemico (se ancora vivo)
        if enemy.is_alive:
            # Attacco nemico
            enemy_damage = CombatSystem.calculate_damage(
                enemy.attack, 
                player.get_total_defense() * (2 if player.defending else 1)
            )
            player.current_health -= enemy_damage
            
            output.append(f"\n{enemy.name} ti attacca!")
            output.append(f"Subisci {enemy_damage} danni!")
            
            if player.current_health <= 0:
                output.append(f"\nSei stato sconfitto!")
                return "\n".join(output), False, True
        
        player.defending = False
        return "\n".join(output), True, True
    
    @staticmethod
    def draw_combat_ui(player, enemy) -> str:
        """Disegna l'interfaccia di combattimento"""
        output = []
        output.append("\n" + "╔" + "═" * 58 + "╗")
        output.append("║" + "COMBATTIMENTO".center(58) + "║")
        output.append("╠" + "═" * 58 + "╣")
        
        # Stato giocatore
        player_health_bar = "█" * player.current_health + "░" * (player.max_health - player.current_health)
        output.append(f"║ {player.name:<20} HP: [{player_health_bar}] {player.current_health}/{player.max_health} ║")
        output.append(f"║    ATK: {player.get_total_attack():<3} DEF: {player.get_total_defense():<3}                                ║")
        
        output.append("╠" + "─" * 58 + "╣")
        
        # Stato nemico
        enemy_health_bar = "█" * enemy.current_health + "░" * (enemy.max_health - enemy.current_health)
        output.append(f"║ {enemy.name:<20} HP: [{enemy_health_bar}] {enemy.current_health}/{enemy.max_health} ║")
        output.append(f"║    ATK: {enemy.attack:<3} DEF: {enemy.defense:<3}                                ║")
        
        output.append("╚" + "═" * 58 + "╝")
        
        return "\n".join(output)

# ============================================================================
# ENTITÀ NEMICO
# ============================================================================

class Enemy:
    """Rappresenta un nemico con statistiche di combattimento"""
    def __init__(self, name: str, entity_type: EntityType, max_health: int, 
        attack: int, defense: int, coins_drop: int = 0, 
        description: str = ""):
        self.name = name
        self.type = entity_type
        self.max_health = max_health
        self.current_health = max_health
        self.attack = attack
        self.defense = defense
        self.coins_drop = coins_drop
        self.is_alive = True
        self.description = description

# ============================================================================
# PLAYER
# ============================================================================

class Player:
    """Rappresenta il giocatore con statistiche e inventario"""
    def __init__(self, name: str = "Viandante"):
        self.name = name
        # Statistiche base
        self.max_health = 20
        self.current_health = 20
        self.base_attack = 3
        self.base_defense = 2
        # Inventario
        self.inventory: List[Entity] = []
        self.equipped_weapon: Optional[Entity] = None
        self.equipped_armor: Optional[Entity] = None
        self.coins = 50  # Monete iniziali
        # Stato combattimento
        self.defending = False
        # Quest
        self.active_quests: Dict[str, Quest] = {}
        self.completed_quests: Set[str] = set()
        # Progressione
        self.enemies_defeated = 0
        self.bosses_defeated: Set[str] = set()
    
    def get_total_attack(self) -> int:
        """Calcola l'attacco totale (base + equipaggiamento)"""
        bonus = 0
        if self.equipped_weapon:
            bonus += self.equipped_weapon.attack_bonus
        return self.base_attack + bonus
    
    def get_total_defense(self) -> int:
        """Calcola la difesa totale (base + equipaggiamento)"""
        bonus = 0
        if self.equipped_armor:
            bonus += self.equipped_armor.defense_bonus
        return self.base_defense + bonus
    
    def heal(self, amount: int):
        """Cura il giocatore"""
        self.current_health = min(self.max_health, self.current_health + amount)
    
    def add_to_inventory(self, item: "Entity"):
        """Aggiunge un oggetto all'inventario"""
        self.inventory.append(item)
    
    def remove_from_inventory(self, item: "Entity"):
        """Rimuove un oggetto dall'inventario"""
        if item in self.inventory:
            self.inventory.remove(item)
    
    def equip_weapon(self, weapon: "Entity") -> str:
        """Equipaggia un'arma"""
        if weapon not in self.inventory:
            return "Non hai questo oggetto!"
        
        if weapon.category != ItemCategory.WEAPON:
            return "Questo non è un'arma!"
        
        if self.equipped_weapon:
            old_weapon = self.equipped_weapon.name
            self.equipped_weapon = weapon
            return f"Hai equipaggiato {weapon.name} (precedente: {old_weapon})"
        else:
            self.equipped_weapon = weapon
            return f"Hai equipaggiato {weapon.name}!"
    
    def equip_armor(self, armor: "Entity") -> str:
        """Equipaggia un'armatura"""
        if armor not in self.inventory:
            return "Non hai questo oggetto!"
        
        if armor.category != ItemCategory.ARMOR:
            return "Questa non è un'armatura!"
        
        if self.equipped_armor:
            old_armor = self.equipped_armor.name
            self.equipped_armor = armor
            return f"Hai equipaggiato {armor.name} (precedente: {old_armor})"
        else:
            self.equipped_armor = armor
            return f"Hai equipaggiato {armor.name}!"
    
    def use_consumable(self, consumable: "Entity") -> str:
        """Usa un oggetto consumabile"""
        if consumable not in self.inventory:
            return "Non hai questo oggetto!"
        
        if consumable.category != ItemCategory.CONSUMABLE:
            return "Questo oggetto non è consumabile!"
        
        # Usa l'oggetto
        self.heal(consumable.health_bonus)
        self.remove_from_inventory(consumable)
        return f"Hai usato {consumable.name}! (+{consumable.health_bonus} HP)"
    
    def show_inventory(self) -> str:
        """Mostra l'inventario del giocatore"""
        output = ["\n" + "╔" + "═" * 58 + "╗"]
        output.append("║" + f"INVENTARIO DI {self.name.upper()}".center(58) + "║")
        output.append("╚" + "═" * 58 + "╝")
        
        # Mostra monete
        output.append(f"\nMONETE: {self.coins}")
        
        if not self.inventory:
            output.append("\nInventario vuoto\n")
        else:
            # Raggruppa per categoria
            categories = {}
            for item in self.inventory:
                cat = item.category.value if item.category else "vario"
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
            
            for category, items in sorted(categories.items()):
                output.append(f"\n{category.upper()}:")
                for item in items:
                    equipped = ""
                    if item == self.equipped_weapon:
                        equipped = " [EQUIPAGGIATA]"
                    elif item == self.equipped_armor:
                        equipped = " [EQUIPAGGIATA]"
                    
                    stats = item.get_stats_display()
                    output.append(f"  • {item.name}{equipped}")
                    if stats != "Nessun bonus":
                        output.append(f"    └─ {stats}")
        
        output.append("")
        return "\n".join(output)
    
    def show_stats(self) -> str:
        """Mostra le statistiche del giocatore"""
        output = ["\n" + "╔" + "═" * 58 + "╗"]
        output.append("║" + f"STATISTICHE DI {self.name.upper()}".center(58) + "║")
        output.append("╚" + "═" * 58 + "╝\n")
        
        # Barra della salute
        health_percent = self.current_health / self.max_health
        health_blocks = int(health_percent * 20)
        health_bar = "█" * health_blocks + "░" * (20 - health_blocks)
        output.append(f"SALUTE:  [{health_bar}] {self.current_health}/{self.max_health}")
        
        # Statistiche
        total_atk = self.get_total_attack()
        total_def = self.get_total_defense()
        
        atk_bonus = total_atk - self.base_attack
        def_bonus = total_def - self.base_defense
        
        atk_display = f"{total_atk}" + (f" ({self.base_attack}+{atk_bonus})" if atk_bonus > 0 else "")
        def_display = f"{total_def}" + (f" ({self.base_defense}+{def_bonus})" if def_bonus > 0 else "")
        
        output.append(f"ATTACCO: {atk_display}")
        output.append(f"DIFESA:  {def_display}")
        
        # Equipaggiamento
        output.append(f"\nEQUIPAGGIAMENTO:")
        output.append(f"  Arma:     {self.equipped_weapon.name if self.equipped_weapon else 'Nessuna'}")
        output.append(f"  Armatura: {self.equipped_armor.name if self.equipped_armor else 'Nessuna'}")
        
        # Progressione
        output.append(f"\nPROGRESSIONE:")
        output.append(f"  Nemici sconfitti: {self.enemies_defeated}")
        output.append(f"  Boss sconfitti: {len(self.bosses_defeated)}")
        output.append(f"  Quest completate: {len(self.completed_quests)}")
        
        output.append("")
        return "\n".join(output)
    
    def show_quests(self) -> str:
        """Mostra le quest attive"""
        output = ["\n" + "╔" + "═" * 58 + "╗"]
        output.append("║" + "REGISTRO MISSIONI".center(58) + "║")
        output.append("╚" + "═" * 58 + "╝")
        
        if not self.active_quests and not self.completed_quests:
            output.append("\nNessuna missione attiva\n")
        else:
            if self.active_quests:
                output.append("\nMISSIONI ATTIVE:")
                for quest_name, quest in self.active_quests.items():
                    output.append(f"\n  {quest.name}")
                    output.append(f"     {quest.description}")
                    output.append(f"     Stato: {quest.get_progress()}")
                    output.append(f"     Obiettivi:")
                    for i, obj in enumerate(quest.objectives):
                        status = "✅" if i in quest.completed_objectives else "⬜"
                        output.append(f"       {status} {obj}")
            
            if self.completed_quests:
                output.append(f"\n✅ MISSIONI COMPLETATE: {len(self.completed_quests)}")
        
        output.append("")
        return "\n".join(output)

# ============================================================================
# ENTITY
# ============================================================================

class Entity:
    """Rappresenta un'entità nel gioco (oggetto, NPC, etc.)"""
    def __init__(self, name: str, entity_type: EntityType, description: str = "", 
        category: Optional[ItemCategory] = None, attack_bonus: int = 0, 
        defense_bonus: int = 0, health_bonus: int = 0, price: int = 0,
        dialogue: List[str] = None, quest: Optional[Quest] = None):
        self.name = name
        self.type = entity_type
        self.description = description
        self.category = category
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.health_bonus = health_bonus
        self.price = price
        self.dialogue = dialogue or []
        self.quest = quest
        self.dialogue_index = 0
    
    def get_stats_display(self) -> str:
        """Mostra le statistiche dell'oggetto"""
        stats = []
        if self.attack_bonus != 0:
            stats.append(f"ATK +{self.attack_bonus}" if self.attack_bonus > 0 else f"ATK {self.attack_bonus}")
        if self.defense_bonus != 0:
            stats.append(f"DEF +{self.defense_bonus}" if self.defense_bonus > 0 else f"DEF {self.defense_bonus}")
        if self.health_bonus != 0:
            stats.append(f"HP +{self.health_bonus}" if self.health_bonus > 0 else f"HP {self.health_bonus}")
        return " | ".join(stats) if stats else "Nessun bonus"
    
    def get_next_dialogue(self) -> str:
        """Ottiene la prossima linea di dialogo"""
        if not self.dialogue:
            return "..."
        
        dialogue = self.dialogue[self.dialogue_index]
        self.dialogue_index = (self.dialogue_index + 1) % len(self.dialogue)
        return dialogue

# ============================================================================
# LOCATION
# ============================================================================

class Location:
    """Rappresenta un luogo nel gioco"""
    def __init__(self, name: str, description: str, ascii_art: str = "",
                 is_locked: bool = False, unlock_condition: str = ""):
        self.name = name
        self.description = description
        self.ascii_art = ascii_art
        self.is_locked = is_locked
        self.unlock_condition = unlock_condition
        self.parent: Optional[Location] = None
        self.children: Dict[str, Location] = {}
        self.entities: List[Entity] = []
        self.enemies: List[Enemy] = []
        self.visited = False
        self.bonfire = False  # Punto di riposo
    
    def add_child(self, location: 'Location'):
        """Aggiunge un sotto-luogo"""
        location.parent = self
        self.children[location.name.lower().replace(" ", "_")] = location
    
    def add_entity(self, entity: Entity):
        """Aggiunge un'entità al luogo"""
        self.entities.append(entity)
    
    def add_enemy(self, enemy: Enemy):
        """Aggiunge un nemico al luogo"""
        self.enemies.append(enemy)
    
    def unlock(self):
        """Sblocca il luogo"""
        self.is_locked = False
    
    def get_living_enemies(self) -> List[Enemy]:
        """Ritorna solo i nemici vivi"""
        return [e for e in self.enemies if e.is_alive]
    
    def get_npcs(self) -> List[Entity]:
        """Ritorna gli NPC amichevoli e i mercanti"""
        return [e for e in self.entities if e.type in [EntityType.NPC, EntityType.MERCHANT]]
    
    def get_items(self) -> List[Entity]:
        """Ritorna gli oggetti raccoglibili"""
        return [e for e in self.entities if e.type == EntityType.ITEM]

# ============================================================================
# MAP MANAGER
# ============================================================================

class MapManager:
    """Gestisce la navigazione e la visualizzazione della mappa"""
    def __init__(self, root: Location, player: Player):
        self.root = root
        self.current_location = root
        self.unlocked_locations: Set[str] = {root.name}
        self.player = player
    
    def get_current_path(self) -> str:
        """Ritorna il percorso attuale stile directory"""
        path_parts = []
        current = self.current_location
        while current is not None:
            path_parts.insert(0, current.name)
            current = current.parent
        return " > ".join(path_parts)
    
    def look_around(self) -> str:
        """Mostra cosa c'è nella location corrente"""
        loc = self.current_location
        loc.visited = True
        
        output = ["\n" + "╔" + "═" * 58 + "╗"]
        output.append("║" + f"📍 {loc.name}".center(58) + "║")
        output.append("╚" + "═" * 58 + "╝")
        
        # ASCII Art
        if loc.ascii_art:
            output.append(loc.ascii_art)
        
        output.append(f"\n{loc.description}\n")
        
        # Bonfire
        if loc.bonfire:
            output.append("C'è un FALÒ qui. Puoi riposare per recuperare salute.\n")
        
        # Mostra sotto-luoghi disponibili
        if loc.children:
            output.append("LUOGHI VICINI:")
            for key, child in loc.children.items():
                if child.is_locked:
                    output.append(f"{child.name} [BLOCCATO]")
                else:
                    visited_mark = "✓" if child.visited else "○"
                    output.append(f"  {visited_mark} {child.name}")
        
        # Mostra nemici
        enemies = loc.get_living_enemies()
        if enemies:
            output.append("\nNEMICI:")
            for i, enemy in enumerate(enemies, 1):
                boss_mark = "👑" if enemy.type == EntityType.BOSS else "👹"
                output.append(f"  {i}. {boss_mark} {enemy.name} [HP: {enemy.current_health}/{enemy.max_health}]")
        
        # Mostra NPC
        npcs = loc.get_npcs()
        if npcs:
            output.append("\nNPC:")
            for i, npc in enumerate(npcs, 1):
                quest_mark = "❗" if npc.quest and npc.quest.name not in self.player.active_quests and npc.quest.name not in self.player.completed_quests else ""
                output.append(f"  {i}. {npc.name} {quest_mark}")
        
        # Mostra oggetti
        items = loc.get_items()
        if items:
            output.append("\nOGGETTI:")
            for item in items:
                output.append(f"  • {item.name}")
        
        output.append("")
        return "\n".join(output)
    
    # ...existing code...
    def change_position(self, destination: str) -> str:
        """Cambia posizione verso un sotto-luogo"""
        dest_key = destination.lower().replace(" ", "_")
        
        if dest_key not in self.current_location.children:
            if self.current_location.children:
                available = ", ".join([c.name for c in self.current_location.children.values()])
                return f"❌ Luogo '{destination}' non trovato. Disponibili: {available}"
            else:
                return "❌ Non ci sono altri luoghi raggiungibili da qui."
        
        target = self.current_location.children[dest_key]
        
        if target.is_locked:
            return f"{target.name} è bloccato! {target.unlock_condition}"
        
        self.current_location = target
        self.unlocked_locations.add(target.name)
        return f"Ti sei spostato a: {target.name}\n" + self.look_around()
    
    def go_back(self) -> str:
        """Torna alla location precedente"""
        if self.current_location.parent is None:
            return "❌ Sei già alla radice della mappa!"
        self.current_location = self.current_location.parent
        return f"↩Sei tornato a: {self.current_location.name}\n" + self.look_around()
    
    def travel_to(self, destination: str) -> str:
        """Viaggia verso una qualunque location del mondo (se non è bloccata)."""
        dest_lower = destination.strip().lower()
        all_locs = self._get_all_locations(self.root)
        # Cerca nome esatto (case-insensitive)
        for loc in all_locs:
            if loc.name.lower() == dest_lower:
                if loc.is_locked:
                    return f"🔒 {loc.name} è bloccato! {loc.unlock_condition}"
                # Muovi il giocatore nella location trovata
                self.current_location = loc
                self.unlocked_locations.add(loc.name)
                return f"Hai viaggiato verso: {loc.name}\n" + self.look_around()
        # Non trovato: mostra possibili destinazioni (non bloccate)
        available = [l.name for l in all_locs if not l.is_locked]
        if available:
            return f"Luogo '{destination}' non trovato. Destinazioni disponibili: {', '.join(sorted(available))}"
        return "Luogo non trovato."
    
    def rest_at_bonfire(self) -> str:
# ...existing code...
        
        self.player.current_health = self.player.max_health
        
        # Respawn nemici (tranne boss)
        for loc in self._get_all_locations(self.root):
            for enemy in loc.enemies:
                if enemy.type != EntityType.BOSS:
                    enemy.is_alive = True
                    enemy.current_health = enemy.max_health
        
        return """
╔════════════════════════════════════════════════════════════╗
║                    🔥 RIPOSO AL FALÒ 🔥                    ║
╚════════════════════════════════════════════════════════════╝

Le fiamme ti avvolgono in un caldo abbraccio...
La tua salute è stata completamente ripristinata!
I nemici comuni sono rinati nelle tenebre...

  SALUTE: """ + f"{self.player.current_health}/{self.player.max_health}" + """
        """
    
    def _get_all_locations(self, loc: Location) -> List[Location]:
        """Ottiene tutte le location ricorsivamente"""
        locations = [loc]
        for child in loc.children.values():
            locations.extend(self._get_all_locations(child))
        return locations
    
    def grab_item(self, item_name: str) -> str:
        """Raccoglie un oggetto"""
        items = self.current_location.get_items()
        
        if not items:
            return "Non ci sono oggetti da raccogliere qui!"
        
        item_name_lower = item_name.lower()
        for entity in self.current_location.entities:
            if entity.type == EntityType.ITEM and entity.name.lower() == item_name_lower:
                self.current_location.entities.remove(entity)
                self.player.add_to_inventory(entity)
                return f"Hai raccolto: {entity.name}!\n   └─ {entity.get_stats_display()}"
        
        available = ", ".join([item.name for item in items])
        return f"❌ Oggetto '{item_name}' non trovato. Disponibili: {available}"
    
    def show_map(self) -> str:
        """Mostra la mappa del mondo"""
        output = ["\n" + "╔" + "═" * 58 + "╗"]
        output.append("║" + "MAPPA DEL MONDO".center(58) + "║")
        output.append("╚" + "═" * 58 + "╝")
        output.append("\nLegenda: ✓ visitato | ○ scoperto | 🔒 bloccato\n")
        
        self._build_map_tree(self.root, output, "")
        output.append("")
        return "\n".join(output)
    
    def _build_map_tree(self, location: Location, output: List[str], prefix: str):
        """Costruisce ricorsivamente l'albero della mappa"""
        if location.visited:
            symbol = "✓"
        elif location.name in self.unlocked_locations:
            symbol = "○"
        elif location.is_locked:
            symbol = "🔒"
        else:
            return
        
        current_marker = " 📍 [QUI]" if location == self.current_location else ""
        bonfire_marker = " 🔥" if location.bonfire else ""
        
        output.append(f"{prefix}{symbol} {location.name}{current_marker}{bonfire_marker}")
        
        children = list(location.children.values())
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            new_prefix = prefix + ("    " if is_last else "│   ")
            child_prefix = prefix + ("└── " if is_last else "├── ")
            
            temp_output = []
            self._build_map_tree(child, temp_output, new_prefix)
            if temp_output:
                output.append(child_prefix + temp_output[0].strip())
                output.extend(temp_output[1:])

# ============================================================================
# CREAZIONE DEL MONDO - LORE ESPANSA
# ============================================================================

def create_game_world() -> Tuple[MapManager, Player]:
    """
    LORE: Il Regno di Tenebris
    
    Mille anni fa, il Regno di Tenebris prosperava sotto la luce dell'Astro Eterno.
    Ma quando il Re Nero Malakor scoprì la Magia Proibita, tutto cambiò.
    La sua ambizione di immortalità corrupe l'Astro, trasformando la luce in tenebra.
    
    Il regno cadde nell'oscurità. I morti si risvegliarono. I vivi persero la speranza.
    Solo pochi eroi, i Portatori di Fiamma, possono ancora vedere la luce dei Falò.
    
    Tu sei uno di loro. Risvegliato senza memoria, devi scoprire il tuo destino
    e decidere se spegnere l'oscurità... o abbracciarla.
    """
    
    player = Player("Viandante Perduto")
    
    # ========================================================================
    # RADICE - TERRE DI TENEBRIS
    # ========================================================================
    
    root = Location(
        "Regno di Tenebris",
        "Un vasto continente avvolto dall'oscurità eterna. L'Astro Nero pulsa nel cielo.",
        """
    ⠀⠀⠀⠀⠀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⠀⠀⠀⠀⠀
    ⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⠀⠀
    ⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀
    ⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀
    ⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀
    ⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇
        """
    )
    
    # ========================================================================
    # AREA 1: SANTUARIO DEL RISVEGLIO (Inizio)
    # ========================================================================
    
    santuario = Location(
        "Santuario del Risveglio",
        "Un antico santuario dove i Portatori di Fiamma si risvegliano. Qui sei al sicuro... per ora.",
        """
        ⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀⠀⠀
        ⠀⠀⠀⢰⣿⣿⣿⡿⠛⠛⠛⠛⠛⠛⠛⢿⣿⣿⣿⣿⡆⠀⠀⠀
        ⠀⠀⠀⣿⣿⣿⣿⡇⠀⠀🔥⠀⠀⠀⠀⢸⣿⣿⣿⣿⠀⠀⠀
        ⠀⠀⠀⢿⣿⣿⣿⣿⣄⠀⠀⠀⠀⠀⣠⣿⣿⣿⣿⡿⠀⠀⠀
        ⠀⠀⠀⠀⠻⣿⣿⣿⣿⣿⣶⣶⣾⣿⣿⣿⣿⣿⠟⠀⠀⠀⠀
        """
    )
    santuario.bonfire = True
    
    # NPC: La Guardiana del Fuoco
    guardiana_quest = Quest(
        "Il Primo Passo",
        "La Guardiana ti chiede di recuperare 3 Frammenti di Fiamma per potenziare il Falò.",
        "Guardiana del Fuoco",
        [
            "Raccogli un Frammento di Fiamma nel Villaggio",
            "Raccogli un Frammento di Fiamma nella Foresta",
            "Raccogli un Frammento di Fiamma nella Palude"
        ],
        reward_coins=100,
        reward_items=["Anello del Portatore"]
    )
    
    guardiana = Entity(
        "Guardiana del Fuoco",
        EntityType.NPC,
        "Una figura misteriosa avvolta in vesti luminose. I suoi occhi brillano con antica saggezza.",
        dialogue=[
            "Benvenuto, Portatore di Fiamma. Ti stavamo aspettando.",
            "Il Regno è caduto nell'oscurità, ma tu puoi ancora riportare la luce.",
            "Cerca i Frammenti di Fiamma. Solo con essi potrai affrontare il Re Nero.",
            "Ricorda: ogni morte ti insegnerà qualcosa. Non temere il fallimento."
        ],
        quest=guardiana_quest
    )
    santuario.add_entity(guardiana)
    
    # Mercante iniziale
    mercante_inizio = Entity(
        "Mercante Errante",
        EntityType.MERCHANT,
        "Un vecchio mercante con uno zaino pieno di oggetti misteriosi.",
        dialogue=[
            "Ah, un nuovo Portatore! Dai un'occhiata alla mia merce.",
            "I prezzi sono giusti... per chi sa apprezzare la qualità!",
            "Torna spesso, avrò sempre novità per te."
        ]
    )
    santuario.add_entity(mercante_inizio)
    
    # Oggetto iniziale
    santuario.add_entity(Entity(
        "Spada del Viandante",
        EntityType.ITEM,
        "Una semplice spada di ferro. L'impugnatura è consumata dall'uso.",
        category=ItemCategory.WEAPON,
        attack_bonus=2
    ))
    
    # ========================================================================
    # AREA 2: VILLAGGIO DELLE OMBRE
    # ========================================================================
    
    villaggio = Location(
        "Villaggio delle Ombre",
        "Un tempo questo villaggio era pieno di vita. Ora solo ombre vagano tra le rovine.",
        """
        ⠀⠀⠀⠀⠀⠀⠀⣠⣴⣶⣶⣶⣶⣶⣤⡀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⠿⠿⠿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀
        ⠀⠀⠀⠀⢸⣿⣿⣿⣿⡏⠀👻⠀⢹⣿⣿⣿⣿⡇⠀⠀⠀⠀
        """
    )
    
    piazza = Location(
        "Piazza del Mercato",
        "La piazza centrale del villaggio. Bancarelle abbandonate sono sparse ovunque."
    )
    piazza.add_entity(Entity(
        "Frammento di Fiamma",
        EntityType.ITEM,
        "Un cristallo che pulsa di luce calda. Sembra attratto a te.",
        category=ItemCategory.KEY_ITEM
    ))
    piazza.add_entity(Entity(
        "Pozione di Salute",
        EntityType.ITEM,
        "Una pozione rosso sangue. Ripristina 5 HP.",
        category=ItemCategory.CONSUMABLE,
        health_bonus=5
    ))
    piazza.add_enemy(Enemy(
        "Ombra Vagante",
        EntityType.ENEMY,
        max_health=8,
        attack=4,
        defense=1,
        coins_drop=10
    ))
    piazza.add_enemy(Enemy(
        "Ombra Vagante",
        EntityType.ENEMY,
        max_health=8,
        attack=4,
        defense=1,
        coins_drop=10
    ))
    
    chiesa = Location(
        "Chiesa Abbandonata",
        "Una chiesa in rovina. Vetrate infrante gettano ombre colorate sul pavimento."
    )
    
    # NPC: Padre Aldric
    aldric_quest = Quest(
        "Ricordi Perduti",
        "Padre Aldric cerca un Medaglione di sua figlia, perduto nel Cimitero.",
        "Padre Aldric",
        ["Trova il Medaglione nel Cimitero Maledetto"],
        reward_coins=50,
        reward_items=["Benedizione Sacra"]
    )
    
    padre_aldric = Entity(
        "Padre Aldric",
        EntityType.NPC,
        "Un vecchio prete che si aggrappa alla fede nonostante tutto.",
        dialogue=[
            "La luce degli dei ci ha abbandonati... ma io continuo a pregare.",
            "Mia figlia... è sepolta nel cimitero. Se trovassi il suo medaglione...",
            "Questo villaggio era pieno di gioia. Ora è solo un'eco del passato.",
            "Non ti fidare del Re Nero. Le sue promesse sono veleno."
        ],
        quest=aldric_quest
    )
    chiesa.add_entity(padre_aldric)
    chiesa.add_entity(Entity(
        "Scudo di Legno Rinforzato",
        EntityType.ITEM,
        "Uno scudo pesante ma resistente.",
        category=ItemCategory.ARMOR,
        defense_bonus=3
    ))
    
    cimitero = Location(
        "Cimitero Maledetto",
        "Lapidi rotte emergono dalla terra. Un miasma verde galleggia tra le tombe."
    )
    cimitero.add_enemy(Enemy(
        "Scheletro Guerriero",
        EntityType.ENEMY,
        max_health=12,
        attack=6,
        defense=3,
        coins_drop=15,
        description="Uno scheletro animato dalla magia oscura. Le sue ossa tintinnano."
    ))
    cimitero.add_enemy(Enemy(
        "Ghoul Affamato",
        EntityType.ENEMY,
        max_health=10,
        attack=7,
        defense=2,
        coins_drop=12
    ))
    cimitero.add_entity(Entity(
        "Medaglione Argenteo",
        EntityType.ITEM,
        "Un medaglione con l'incisione 'Per sempre nella luce'.",
        category=ItemCategory.KEY_ITEM
    ))
    
    tempio = Location(
        "Tempio della Purificazione",
        "Un antico tempio dove si praticavano rituali di purificazione. Ora è corrotto."
    )
    tempio.add_enemy(Enemy(
        "Sacerdote Corrotto",
        EntityType.BOSS,
        max_health=30,
        attack=8,
        defense=4,
        coins_drop=100,
        description="Un tempo santo, ora servo dell'oscurità. Impugna un bastone maledetto."
    ))
    tempio.add_entity(Entity(
        "Chiave della Foresta",
        EntityType.ITEM,
        "Una chiave antica che brilla di luce verde. Apre il passaggio verso la Foresta Oscura.",
        category=ItemCategory.KEY_ITEM
    ))
    tempio.add_entity(Entity(
        "Armatura del Pellegrino",
        EntityType.ITEM,
        "Un'armatura leggera ma protettiva.",
        category=ItemCategory.ARMOR,
        defense_bonus=5
    ))
    
    villaggio.add_child(piazza)
    villaggio.add_child(chiesa)
    villaggio.add_child(cimitero)
    villaggio.add_child(tempio)
    
    # ========================================================================
    # AREA 3: FORESTA OSCURA (BLOCCATA)
    # ========================================================================
    
    foresta = Location(
        "Foresta Oscura",
        "Alberi contorti si ergono come dita scheletriche. Il sole non penetra la coltre di foglie.",
        """
        ⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀⠀⠀
        ⠀⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡀⠀⠀⠀
        ⠀⠀⠀⠀⣾⣿⣿🌲⣿⣿⣿⣿⣿⣿🌲⣿⣿⣷⠀⠀⠀
        ⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀
        """,
        is_locked=True,
        unlock_condition="Serve la Chiave della Foresta"
    )
    foresta.bonfire = True
    
    radura = Location(
        "Radura Nebbiosa",
        "Una piccola apertura tra gli alberi. La nebbia danza sul terreno come spiriti."
    )
    radura.add_entity(Entity(
        "Frammento di Fiamma",
        EntityType.ITEM,
        "Un cristallo che pulsa di luce calda.",
        category=ItemCategory.KEY_ITEM
    ))
    radura.add_enemy(Enemy(
        "Lupo Corrotto",
        EntityType.ENEMY,
        max_health=15,
        attack=9,
        defense=3,
        coins_drop=20
    ))
    radura.add_enemy(Enemy(
        "Lupo Alpha",
        EntityType.ENEMY,
        max_health=20,
        attack=11,
        defense=4,
        coins_drop=30
    ))
    
    capanna = Location(
        "Capanna del Saggio",
        "Una capanna di legno miracolosamente intatta. Fumo profumato esce dal camino."
    )
    
    # NPC: Vecchio Saggio Malakai
    malakai_quest = Quest(
        "Erbe della Saggezza",
        "Malakai ha bisogno di 3 Erbe Lunari dalla Palude Velenosa per una pozione potente.",
        "Malakai il Saggio",
        ["Raccogli 3 Erbe Lunari dalla Palude Velenosa"],
        reward_coins=150,
        unlock_location="Montagna Maledetta"
    )
    
    malakai = Entity(
        "Malakai il Saggio",
        EntityType.NPC,
        "Un vecchio mago con una lunga barba bianca. I suoi occhi vedono oltre il presente.",
        dialogue=[
            "Ah, un Portatore di Fiamma! Non ne vedevo da decenni.",
            "Il Re Nero... lo conoscevo, sai? Prima che l'oscurità lo corrompesse.",
            "La magia proibita promette potere, ma il prezzo è sempre la propria umanità.",
            "Nella Montagna Maledetta troverai risposte... ma anche pericoli indicibili.",
            "Se mi aiuti, posso insegnarti segreti dimenticati dal tempo."
        ],
        quest=malakai_quest
    )
    capanna.add_entity(malakai)
    capanna.add_entity(Entity(
        "Bastone del Mago",
        EntityType.ITEM,
        "Un bastone intarsiato di rune. Emana potere magico.",
        category=ItemCategory.WEAPON,
        attack_bonus=6
    ))
    
    tana_lupi = Location(
        "Tana dei Lupi",
        "Una caverna oscura che puzza di sangue e pelo bagnato. Ossa sono sparse ovunque."
    )
    tana_lupi.add_enemy(Enemy(
        "Re dei Lupi",
        EntityType.BOSS,
        max_health=40,
        attack=12,
        defense=5,
        coins_drop=150,
        description="Un lupo gigantesco con occhi rossi. È il guardiano della foresta."
    ))
    tana_lupi.add_entity(Entity(
        "Zanna del Re Lupo",
        EntityType.ITEM,
        "Una zanna enorme e affilata. Potrebbe essere forgiata in un'arma potente.",
        category=ItemCategory.MATERIAL
    ))
    
    foresta.add_child(radura)
    foresta.add_child(capanna)
    foresta.add_child(tana_lupi)
    
    # ========================================================================
    # AREA 4: PALUDE VELENOSA
    # ========================================================================
    
    palude = Location(
        "Palude Velenosa",
        "Acque stagnanti verdi ribollono. L'aria è densa di spore tossiche.",
        """
        ⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⣀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⣠⣾☠️⣿⣿⣿☠️⣷⣄⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀
        """
    )
    
    palude.add_entity(Entity(
        "Frammento di Fiamma",
        EntityType.ITEM,
        "Un cristallo che pulsa di luce calda.",
        category=ItemCategory.KEY_ITEM
    ))
    palude.add_enemy(Enemy(
        "Blob Velenoso",
        EntityType.ENEMY,
        max_health=18,
        attack=8,
        defense=6,
        coins_drop=25
    ))
    palude.add_entity(Entity(
        "Erba Lunare",
        EntityType.ITEM,
        "Un'erba che brilla di luce argentea. Molto rara.",
        category=ItemCategory.MATERIAL
    ))
    
    capanna_strega = Location(
        "Capanna della Strega",
        "Una capanna storta poggiata su palafitte. Luci verdi brillano dalle finestre."
    )
    
    # NPC: Morgana la Strega
    morgana_quest = Quest(
        "Il Cuore della Palude",
        "Morgana vuole il Cuore di Cristallo dell'Idra per completare un rituale.",
        "Morgana la Strega",
        ["Sconfiggi l'Idra Velenosa e recupera il suo Cuore"],
        reward_coins=200,
        reward_items=["Pozione dell'Immortalità Minore"]
    )
    
    morgana = Entity(
        "Morgana la Strega",
        EntityType.NPC,
        "Una strega dai capelli verdi. Sorride mostrando denti troppo affilati.",
        dialogue=[
            "Ehehehe... un visitatore! Quanto tempo!",
            "La palude offre molte cose... se sai dove cercare.",
            "L'Idra è la guardiana di questo luogo. Vuoi affrontarla? Sei coraggioso... o folle.",
            "Il Re Nero mi ha fatto un'offerta una volta. L'ho rifiutata. Vedi dove mi ha portato?",
            "Porta pazienza con me, caro. La solitudine rende... eccentrici."
        ],
        quest=morgana_quest
    )
    capanna_strega.add_entity(morgana)
    
    tana_idra = Location(
        "Tana dell'Idra",
        "Una caverna allagata. Si sentono sibili multipli echeggiare dalle profondità."
    )
    tana_idra.add_enemy(Enemy(
        "Idra Velenosa",
        EntityType.BOSS,
        max_health=50,
        attack=14,
        defense=6,
        coins_drop=200,
        description="Una bestia con tre teste serpentine. Il veleno gocciola dalle sue fauci."
    ))
    tana_idra.add_entity(Entity(
        "Cuore di Cristallo",
        EntityType.ITEM,
        "Un cuore cristallino che ancora batte. Emana energia magica.",
        category=ItemCategory.KEY_ITEM
    ))
    tana_idra.add_entity(Entity(
        "Spada di Veleno",
        EntityType.ITEM,
        "Una spada forgiata con le scaglie dell'Idra. Avvelena i nemici.",
        category=ItemCategory.WEAPON,
        attack_bonus=8
    ))
    
    palude.add_child(capanna_strega)
    palude.add_child(tana_idra)
    
    # ========================================================================
    # AREA 5: MONTAGNA MALEDETTA (BLOCCATA)
    # ========================================================================
    
    montagna = Location(
        "Montagna Maledetta",
        "Le vette sono avvolte in una tempesta eterna. Fulmini squarciano il cielo violaceo.",
        """
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⛰️⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⛰️⛰️⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⛰️⛰️⛰️⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⛰️⛰️⛰️⛰️⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⛰️⛰️⛰️⛰️⛰️⠀⠀⠀⠀⠀⠀
        """,
        is_locked=True,
        unlock_condition="Completa la quest di Malakai il Saggio"
    )
    montagna.bonfire = True
    
    sentiero = Location(
        "Sentiero del Fulmine",
        "Un sentiero roccioso battuto da fulmini incessanti. Ogni passo è pericoloso."
    )
    sentiero.add_enemy(Enemy(
        "Elementale del Fulmine",
        EntityType.ENEMY,
        max_health=25,
        attack=15,
        defense=4,
        coins_drop=40
    ))
    sentiero.add_enemy(Enemy(
        "Gargoyle di Pietra",
        EntityType.ENEMY,
        max_health=30,
        attack=10,
        defense=8,
        coins_drop=35
    ))
    
    torre = Location(
        "Torre del Traditore",
        "Una torre nera che si erge verso il cielo. Qui viveva il Re Nero prima della caduta."
    )
    
    # NPC: Spettro del Cavaliere
    cavaliere = Entity(
        "Spettro del Cavaliere",
        EntityType.NPC,
        "Lo spirito di un cavaliere che serviva il Re. È intrappolato qui per l'eternità.",
        dialogue=[
            "Sei venuto a fermare Malakor? Sei più coraggioso di quanto sembri.",
            "Io... io l'ho servito. Ho visto la sua trasformazione. La sua follia.",
            "L'Astro Eterno... lo corruppe completamente. Ora è un'ombra di ciò che era.",
            "Nella Grotta del Drago troverai un'antica reliquia. Potrebbe aiutarti.",
            "Quando lo affronterai... non mostrare pietà. Ciò che era umano in lui è morto."
        ]
    )
    torre.add_entity(cavaliere)
    torre.add_entity(Entity(
        "Armatura del Cavaliere Oscuro",
        EntityType.ITEM,
        "Un'armatura nera come la notte. Molto pesante ma estremamente protettiva.",
        category=ItemCategory.ARMOR,
        defense_bonus=10
    ))
    
    grotta_drago = Location(
        "Grotta del Drago Antico",
        "Una grotta immensa. Il soffitto è perso nell'oscurità. Ossa gigantesche sono sparse ovunque."
    )
    grotta_drago.add_enemy(Enemy(
        "Drago Antico Dormiente",
        EntityType.BOSS,
        max_health=80,
        attack=18,
        defense=10,
        coins_drop=500,
        description="Un drago colossale con scaglie nere. Dorme da secoli, ma il tuo arrivo lo sveglia."
    ))
    grotta_drago.add_entity(Entity(
        "Spada Ammazza-Draghi",
        EntityType.ITEM,
        "Una spada leggendaria forgiata per uccidere draghi. Brilla di luce argentea.",
        category=ItemCategory.WEAPON,
        attack_bonus=15
    ))
    grotta_drago.add_entity(Entity(
        "Scaglie di Drago",
        EntityType.ITEM,
        "Scaglie durissime del drago. Possono essere forgiate in armature leggendarie.",
        category=ItemCategory.MATERIAL
    ))
    
    montagna.add_child(sentiero)
    montagna.add_child(torre)
    montagna.add_child(grotta_drago)
    
    # ========================================================================
    # AREA FINALE: CASTELLO DEL RE NERO (BLOCCATA)
    # ========================================================================
    
    castello = Location(
        "Castello del Re Nero",
        "Il castello dove tutto ebbe inizio. L'Astro Nero pulsa sopra le torri.",
        """
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀🏰⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀🏰🏰🏰⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀🏰🏰🏰🏰⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀🏰🏰⚫🏰🏰⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀🏰🏰🏰🏰🏰🏰⠀⠀⠀⠀
        """,
        is_locked=True,
        unlock_condition="Sconfiggi il Drago Antico e ottieni la sua benedizione"
    )
    
    cortile = Location(
        "Cortile delle Anime Perdute",
        "Un cortile pieno di statue. Aspetta... si stanno muovendo?"
    )
    cortile.add_enemy(Enemy(
        "Statua Animata",
        EntityType.ENEMY,
        max_health=35,
        attack=16,
        defense=12,
        coins_drop=50
    ))
    cortile.add_enemy(Enemy(
        "Statua Animata",
        EntityType.ENEMY,
        max_health=35,
        attack=16,
        defense=12,
        coins_drop=50
    ))
    
    sala_trono = Location(
        "Sala del Trono",
        "Una sala immensa. Il trono è vuoto, ma senti una presenza oppressiva."
    )
    sala_trono.add_enemy(Enemy(
        "Malakor, Il Re Nero",
        EntityType.BOSS,
        max_health=120,
        attack=20,
        defense=15,
        coins_drop=1000,
        description="Il Re che un tempo governava con saggezza. Ora è un'aberrazione di oscurità pura."
    ))
    sala_trono.add_entity(Entity(
        "Corona dell'Astro Nero",
        EntityType.ITEM,
        "La corona che corrompe chi la indossa. Ma il suo potere è innegabile.",
        category=ItemCategory.KEY_ITEM
    ))
    
    castello.add_child(cortile)
    castello.add_child(sala_trono)
    
    # ========================================================================
    # COSTRUZIONE ALBERO FINALE
    # ========================================================================
    
    root.add_child(santuario)
    root.add_child(villaggio)
    root.add_child(foresta)
    root.add_child(palude)
    root.add_child(montagna)
    root.add_child(castello)
    
    # Crea il manager
    manager = MapManager(root, player)
    manager.current_location = santuario
    manager.unlocked_locations.add(santuario.name)
    manager.unlocked_locations.add(villaggio.name)  # Villaggio subito accessibile
    santuario.visited = True
    
    return manager, player

# ============================================================================
# SISTEMA DI GIOCO E INTERFACCIA
# ============================================================================

def combat_interface(game: MapManager, player: Player, enemy: Enemy) -> bool:
    """
    Gestisce un combattimento completo
    Returns: True se il giocatore vince, False se perde
    """
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + "INIZIO COMBATTIMENTO!".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    time.sleep(1)
    
    while player.current_health > 0 and enemy.is_alive:
        # Mostra UI combattimento
        print(CombatSystem.draw_combat_ui(player, enemy))
        
        # Menu azioni
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║ AZIONI:                                                    ║")
        print("║  [1] Attacco normale                                   ║")
        print("║  [2] Difesa (dimezza danno subito)                    ║")
        print("║  [3] Usa oggetto                                        ║")
        print("║  [4] Fuggi (50% successo)                               ║")
        print("╚════════════════════════════════════════════════════════════╝")
        
        choice = input("\nScegli un'azione [1-4]: ").strip()
        
        if choice == "1":
            # Attacco
            result, player_alive, enemy_alive = CombatSystem.combat_round(player, enemy, "attack")
            print("\n" + result)
            time.sleep(1.5)
            
            if not enemy_alive:
                # Vittoria!
                print("\n" + "╔" + "═" * 58 + "╗")
                print("║" + "VITTORIA!".center(58) + "║")
                print("╚" + "═" * 58 + "╝")
                print(f"\nHai ottenuto {enemy.coins_drop} monete!")
                player.coins += enemy.coins_drop
                player.enemies_defeated += 1
                
                if enemy.type == EntityType.BOSS:
                    player.bosses_defeated.add(enemy.name)
                    print(f"Hai sconfitto un BOSS: {enemy.name}!")
                
                time.sleep(2)
                return True
            
            if not player_alive:
                return False
        
        elif choice == "2":
            # Difesa
            result, player_alive, enemy_alive = CombatSystem.combat_round(player, enemy, "defend")
            print("\n" + result)
            time.sleep(1.5)
            
            if not player_alive:
                return False
        
        elif choice == "3":
            # Usa oggetto
            consumables = [item for item in player.inventory if item.category == ItemCategory.CONSUMABLE]
            
            if not consumables:
                print("\nNon hai oggetti consumabili!")
                time.sleep(1)
                continue
            
            print("\nCONSUMABILI:")
            for i, item in enumerate(consumables, 1):
                print(f"  {i}. {item.name} ({item.get_stats_display()})")
            print("  0. Annulla")
            
            item_choice = input("\nScegli oggetto [0-{}]: ".format(len(consumables))).strip()
            
            try:
                idx = int(item_choice)
                if idx == 0:
                    continue
                if 1 <= idx <= len(consumables):
                    item = consumables[idx - 1]
                    result = player.use_consumable(item)
                    print("\n" + result)
                    time.sleep(1.5)
                    
                    # Il nemico attacca comunque
                    if enemy.is_alive:
                        enemy_damage = CombatSystem.calculate_damage(enemy.attack, player.get_total_defense())
                        player.current_health -= enemy_damage
                        print(f"\n{enemy.name} ti attacca mentre usi l'oggetto!")
                        print(f"Subisci {enemy_damage} danni!")
                        time.sleep(1.5)
                        
                        if player.current_health <= 0:
                            return False
                else:
                    print("Scelta non valida!")
                    time.sleep(1)
            except ValueError:
                print("Inserisci un numero valido!")
                time.sleep(1)
        
        elif choice == "4":
            # Fuggi
            if random.random() < 0.5:
                print("\nSei riuscito a fuggire!")
                time.sleep(1)
                return True
            else:
                print("\nNon riesci a fuggire!")
                # Il nemico attacca
                enemy_damage = CombatSystem.calculate_damage(enemy.attack, player.get_total_defense())
                player.current_health -= enemy_damage
                print(f"{enemy.name} ti attacca mentre fuggi!")
                print(f"Subisci {enemy_damage} danni!")
                time.sleep(1.5)
                
                if player.current_health <= 0:
                    return False
        else:
            print("\nScelta non valida!")
            time.sleep(1)
    
    return False

def show_help():
    """Mostra la lista comandi"""
    help_text = """
╔════════════════════════════════════════════════════════════╗
║                    COMANDI DISPONIBILI                     ║
╠════════════════════════════════════════════════════════════╣
║  MOVIMENTO:                                                ║
║    cp <luogo>       - Spostati in un luogo vicino (child) ║
║    travel <luogo>   - Viaggia verso un luogo distante      ║
║                                                            ║
║  ESPLORAZIONE:                                             ║
║    look             - Guarda intorno                       ║
║    map              - Mostra mappa del mondo               ║
║                                                            ║
║  GIOCATORE:                                                ║
║    inv              - Mostra inventario                    ║
║    stats            - Mostra statistiche                   ║
║    quests           - Mostra missioni attive               ║
║    rest             - Riposa al falò (recupera HP)         ║
║                                                            ║
║  OGGETTI:                                                  ║
║    grab <oggetto>   - Raccogli un oggetto                 ║
║    equip <oggetto>  - Equipaggia arma/armatura            ║
║    use <oggetto>    - Usa un consumabile                  ║
║                                                            ║
║  INTERAZIONI:                                              ║
║    attack <numero>  - Attacca un nemico                   ║
║    talk <numero>    - Parla con un NPC                    ║
║                                                            ║
║  ALTRO:                                                    ║
║    help             - Mostra questo aiuto                  ║
║    quit             - Esci dal gioco                       ║
╚════════════════════════════════════════════════════════════╝
"""
    print(help_text)

def show_intro():
    """Mostra l'introduzione del gioco"""
    intro = """
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║              ⚔️  TERMINAL SOULS: REGNO OSCURO ⚔️          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

         ⠀⠀⠀⠀⠀⠀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⠀⠀⠀⠀⠀
         ⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⠀⠀
         ⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀
         ⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿🔥⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀
         ⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀
         ⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                         LA LORE

Mille anni fa, il Regno di Tenebris prosperava sotto
la luce dell'Astro Eterno. Il Re Malakor era saggio e giusto.

Ma l'ambizione lo corruppe. Cercò l'immortalità attraverso
la Magia Proibita, e nel farlo trasformò l'Astro in oscurità.

Il regno cadde. I morti si risvegliarono. La luce svanì.

Solo i Portatori di Fiamma possono ancora vedere i Falò,
beacon di speranza in un mondo avvolto dalle tenebre.

Tu sei uno di loro. Risvegliato senza memoria nel
Santuario del Risveglio, devi scoprire il tuo destino.

Sceglierai di riportare la luce... o abbraccerai l'oscurità?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Premi INVIO per iniziare la tua avventura...
"""
    print(intro)
    input()

def game_loop():
    """Loop principale del gioco"""
    os.system('clear' if os.name == 'posix' else 'cls')
    
    show_intro()
    
    game, player = create_game_world()
    
    print("\nTi risvegli nel Santuario del Risveglio...")
    time.sleep(1)
    print(game.look_around())
    
    while True:
        try:
            command = input(f"\n[{game.get_current_path()}]> ").strip().lower()
            
            if not command:
                continue
            
            parts = command.split(maxsplit=1)
            cmd = parts[0]
            arg = parts[1] if len(parts) > 1 else ""
            
            # ============================================================
            # COMANDI BASE
            # ============================================================
            
            if cmd in ["quit", "exit", "q"]:
                print("\nAnche i Portatori di Fiamma devono riposare...")
                print("Grazie per aver giocato a Terminal Souls!\n")
                break
            
            elif cmd == "help":
                show_help()
            
            elif cmd == "look":
                print(game.look_around())
            
            elif cmd == "map":
                print(game.show_map())
            
            # ============================================================
            # MOVIMENTO
            # ============================================================
            
            elif cmd == "cp":
                # spostamento verso sotto-luoghi (child) — comportamento identico a change_position
                if not arg:
                    if game.current_location.children:
                        print("\nLUOGHI VICINI:")
                        for key, child in game.current_location.children.items():
                            locked = " [BLOCCATO]" if child.is_locked else ""
                            visited_mark = "✓" if child.visited else "○"
                            print(f"  {visited_mark} {child.name}{locked}")
                        print("\nUso: cp <nome_luogo>")
                    else:
                        print("Non ci sono luoghi vicini raggiungibili da qui.")
                else:
                    print(game.change_position(arg))
            
            elif cmd == "travel":
                # viaggio verso qualunque luogo del mondo (se non bloccato)
                if not arg:
                    # mostra le destinazioni disponibili (non bloccate)
                    all_locs = game._get_all_locations(game.root)
                    destinations = [l.name for l in all_locs if not l.is_locked]
                    if destinations:
                        print("\nDESTINAZIONI DISPONIBILI:")
                        for name in sorted(destinations):
                            print(f"  • {name}")
                        print("\nUso: travel <nome_luogo>")
                    else:
                        print("Nessuna destinazione disponibile al momento.")
                else:
                    print(game.travel_to(arg))
            
            elif cmd in ["back", "indietro"]:
                print(game.go_back())
# ...existing code...
            
            # ============================================================
            # GIOCATORE
            # ============================================================
            
            elif cmd == "inv":
                print(player.show_inventory())
            
            elif cmd == "stats":
                print(player.show_stats())
            
            elif cmd == "quests":
                print(player.show_quests())
            
            elif cmd == "rest":
                print(game.rest_at_bonfire())
            
            # ============================================================
            # OGGETTI
            # ============================================================
            
            elif cmd == "grab":
                if not arg:
                    items = game.current_location.get_items()
                    if items:
                        print("\nOGGETTI DISPONIBILI:")
                        for item in items:
                            print(f"  • {item.name}")
                        print("\nUso: grab <nome_oggetto>")
                    else:
                        print("Non ci sono oggetti da raccogliere qui!")
                else:
                    print(game.grab_item(arg))
            
            elif cmd == "equip":
                if not arg:
                    print("Uso: equip <nome_oggetto>")
                else:
                    # Cerca l'oggetto nell'inventario
                    found = False
                    for item in player.inventory:
                        if item.name.lower() == arg.lower():
                            if item.category == ItemCategory.WEAPON:
                                print(player.equip_weapon(item))
                            elif item.category == ItemCategory.ARMOR:
                                print(player.equip_armor(item))
                            else:
                                print("Questo oggetto non può essere equipaggiato!")
                            found = True
                            break
                    
                    if not found:
                        print(f"Non hai '{arg}' nell'inventario!")
            
            elif cmd == "use":
                if not arg:
                    consumables = [i for i in player.inventory if i.category == ItemCategory.CONSUMABLE]
                    if consumables:
                        print("\nCONSUMABILI:")
                        for item in consumables:
                            print(f"  • {item.name} - {item.get_stats_display()}")
                        print("\nUso: use <nome_oggetto>")
                    else:
                        print("Non hai oggetti consumabili!")
                else:
                    found = False
                    for item in player.inventory:
                        if item.name.lower() == arg.lower():
                            print(player.use_consumable(item))
                            found = True
                            break
                    
                    if not found:
                        print(f"Non hai '{arg}' nell'inventario!")
            
            # ============================================================
            # COMBATTIMENTO
            # ============================================================
            
            elif cmd == "attack":
                enemies = game.current_location.get_living_enemies()
                
                if not enemies:
                    print("Non ci sono nemici qui!")
                    continue
                
                if not arg:
                    print("\nNEMICI DISPONIBILI:")
                    for i, enemy in enumerate(enemies, 1):
                        boss_mark = "👑" if enemy.type == EntityType.BOSS else "👹"
                        print(f"  {i}. {boss_mark} {enemy.name} [HP: {enemy.current_health}/{enemy.max_health}]")
                    print("\nUso: attack <numero>")
                    continue
                
                try:
                    enemy_idx = int(arg) - 1
                    if 0 <= enemy_idx < len(enemies):
                        enemy = enemies[enemy_idx]
                        victory = combat_interface(game, player, enemy)
                        
                        if victory:
                            print(game.look_around())
                        else:
                            # Game Over
                            print("\n" + "╔" + "═" * 58 + "╗")
                            print("║" + "SEI MORTO".center(58) + "║")
                            print("╚" + "═" * 58 + "╝")
                            print("\nLa tua luce si spegne... ma i Portatori di Fiamma non muoiono mai veramente.")
                            print("Vieni risvegliato all'ultimo Falò visitato.\n")
                            
                            # Respawn al falò
                            player.current_health = player.max_health
                            # Trova l'ultimo falò
                            bonfire_loc = None
                            for loc in game._get_all_locations(game.root):
                                if loc.bonfire and loc.visited:
                                    bonfire_loc = loc
                                    break
                            
                            if bonfire_loc:
                                game.current_location = bonfire_loc
                                print(f"Ti risvegli al {bonfire_loc.name}...")
                                time.sleep(2)
                                print(game.look_around())
                    else:
                        print(f"Scegli un numero tra 1 e {len(enemies)}")
                except ValueError:
                    print("Inserisci un numero valido!")
            
            # ============================================================
            # INTERAZIONE NPC
            # ============================================================
            
            elif cmd == "talk":
                npcs = game.current_location.get_npcs()
                
                if not npcs:
                    print("Non ci sono NPC qui!")
                    continue
                
                if not arg:
                    print("\nNPC DISPONIBILI:")
                    for i, npc in enumerate(npcs, 1):
                        quest_mark = "❗" if npc.quest and npc.quest.name not in player.active_quests and npc.quest.name not in player.completed_quests else ""
                        print(f"  {i}. {npc.name} {quest_mark}")
                    print("\nUso: talk <numero>")
                    continue
                
                try:
                    npc_idx = int(arg) - 1
                    if 0 <= npc_idx < len(npcs):
                        npc = npcs[npc_idx]
                        
                        print("\n" + "╔" + "═" * 58 + "╗")
                        print("║" + f"Conversazione con {npc.name}".center(58) + "║")
                        print("╚" + "═" * 58 + "╝\n")
                        
                        dialogue = npc.get_next_dialogue()
                        print(f"{npc.name}: \"{dialogue}\"\n")
                        
                        # Controlla se ha una quest
                        if npc.quest:
                            quest = npc.quest
                            
                            if quest.name in player.completed_quests:
                                print(f"[Quest '{quest.name}' già completata]")
                            elif quest.name in player.active_quests:
                                print(f"[Quest attiva: {quest.name}]")
                                print(f"Progresso: {quest.get_progress()}")
                            else:
                                print(f"\nNUOVA QUEST DISPONIBILE: {quest.name}")
                                print(f"   {quest.description}")
                                print(f"\n   Obiettivi:")
                                for obj in quest.objectives:
                                    print(f"     • {obj}")
                                
                                accept = input("\nAccetti la quest? [s/n]: ").strip().lower()
                                if accept == 's':
                                    quest.start()
                                    player.active_quests[quest.name] = quest
                                    print(f"\nHai accettato la quest '{quest.name}'!")
                    else:
                        print(f"Scegli un numero tra  1 e {len(npcs)}")
                except ValueError:
                    print("Inserisci un numero valido!")
            
            # ============================================================
            # COMANDO NON RICONOSCIUTO
            # ============================================================
            
            else:
                print(f"Comando '{cmd}' non riconosciuto. Digita 'help' per la lista comandi.")
        
        except KeyboardInterrupt:
            print("\n\nGioco interrotto!\n")
            break
        except Exception as e:
            print(f"Errore: {e}")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    game_loop()
