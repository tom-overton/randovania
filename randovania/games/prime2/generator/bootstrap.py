from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.damage_reduction import DamageReduction
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.prime2.generator.pickup_pool import sky_temple_keys
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.damage_state import DamageState


def is_boss_location(node: PickupNode, config: BaseConfiguration) -> bool:
    assert isinstance(config, EchoesConfiguration)
    mode = config.sky_temple_keys
    boss = node.extra.get("boss")
    if boss is not None:
        if boss == "guardian" or mode == LayoutSkyTempleKeyMode.ALL_BOSSES:
            return True

    return False


class EchoesBootstrap(Bootstrap):
    def create_damage_state(self, game: GameDescription, configuration: BaseConfiguration) -> DamageState:
        assert isinstance(configuration, EchoesConfiguration)
        return EnergyTankDamageState(
            configuration.energy_per_tank - 1,
            configuration.energy_per_tank,
            game.resource_database,
            game.region_list,
        )

    def event_resources_for_configuration(
        self,
        configuration: BaseConfiguration,
        resource_database: ResourceDatabase,
    ) -> ResourceGain:
        assert isinstance(configuration, EchoesConfiguration)

        yield resource_database.get_event("Event2"), 1  # Hive Tunnel Web
        yield resource_database.get_event("Event4"), 1  # Command Chamber Gate
        yield resource_database.get_event("Event71"), 1  # Landing Site Webs
        yield resource_database.get_event("Event78"), 1  # Hive Chamber A Gates

        if configuration.use_new_patcher:
            yield resource_database.get_event("Event73"), 1  # Dynamo Chamber Gates
            yield resource_database.get_event("Event75"), 1  # Trooper Security Station Gate
            yield resource_database.get_event("Event20"), 1  # Security Station B DS Appearance

    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
        assert isinstance(configuration, EchoesConfiguration)
        enabled_resources = set()
        allow_vanilla = {
            "allow_jumping_on_dark_water": "DarkWaterJump",
            "allow_vanilla_dark_beam": "VanillaDarkBeam",
            "allow_vanilla_light_beam": "VanillaLightBeam",
            "allow_vanilla_seeker_launcher": "VanillaSeekers",
            "allow_vanilla_echo_visor": "VanillaEcho",
            "allow_vanilla_dark_visor": "VanillaDarkVisor",
            "allow_vanilla_screw_attack": "VanillaSA",
            "allow_vanilla_gravity_boost": "VanillaGravity",
            "allow_vanilla_boost_ball": "VanillaBoost",
            "allow_vanilla_spider_ball": "VanillaSpider",
        }
        for name, index in allow_vanilla.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        if configuration.teleporters.is_vanilla:
            # Vanilla Great Temple Emerald Translator Gate
            enabled_resources.add("VanillaGreatTempleEmeraldGate")

        if configuration.safe_zone.prevents_dark_aether:
            # Safe Zone
            enabled_resources.add("SafeZone")

        return enabled_resources

    def patch_resource_database(self, db: ResourceDatabase, configuration: BaseConfiguration) -> ResourceDatabase:
        assert isinstance(configuration, EchoesConfiguration)

        damage_reductions = copy.copy(db.damage_reductions)
        damage_reductions[db.get_by_type_and_index(ResourceType.DAMAGE, "DarkWorld1")] = [
            DamageReduction(None, configuration.varia_suit_damage / 6.0),
            DamageReduction(db.get_item_by_display_name("Dark Suit"), configuration.dark_suit_damage / 6.0),
            DamageReduction(db.get_item_by_display_name("Light Suit"), 0.0),
        ]
        return dataclasses.replace(db, damage_reductions=damage_reductions)

    def assign_pool_results(self, rng: Random, patches: GamePatches, pool_results: PoolResults) -> GamePatches:
        assert isinstance(patches.configuration, EchoesConfiguration)
        mode = patches.configuration.sky_temple_keys

        if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
            locations = self.all_preplaced_item_locations(patches.game, patches.configuration, is_boss_location)
            self.pre_place_items(rng, locations, pool_results, sky_temple_keys.SKY_TEMPLE_KEY_CATEGORY)

        return super().assign_pool_results(rng, patches, pool_results)

    def apply_game_specific_patches(
        self, game: GameDatabaseView, configuration: BaseConfiguration, patches: GamePatches
    ) -> GameDatabaseView:
        assert isinstance(configuration, EchoesConfiguration)

        resource_database = game.get_resource_database_view()
        scan_visor = resource_database.get_item("Scan")
        scan_visor_req = ResourceRequirement.simple(scan_visor)

        translator_gates = patches.game_specific["translator_gates"]

        for _, _, node in game.node_iterator():
            if not isinstance(node, ConfigurableNode):
                continue

            requirement = LayoutTranslatorRequirement(translator_gates[node.identifier.as_string])
            translator = resource_database.get_item(requirement.item_name)
            game.region_list.configurable_nodes[node.identifier] = RequirementAnd(
                [
                    scan_visor_req,
                    ResourceRequirement.simple(translator),
                ]
            )
