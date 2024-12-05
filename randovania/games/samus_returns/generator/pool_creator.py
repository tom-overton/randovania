from __future__ import annotations

from typing import TYPE_CHECKING

from frozendict import frozendict

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.pickup import pickup_category
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.samus_returns.layout.msr_configuration import MSRArtifactConfig, MSRConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView, ResourceDatabaseView
    from randovania.layout.base.base_configuration import BaseConfiguration

METROID_DNA_CATEGORY = pickup_category.PickupCategory(
    name="dna", long_name="Metroid DNA", hint_details=("some ", "Metroid DNA"), hinted_as_major=False, is_key=True
)


def create_msr_artifact(
    artifact_number: int,
    resource_database: ResourceDatabaseView,
) -> PickupEntry:
    return PickupEntry(
        name=f"Metroid DNA {artifact_number + 1}",
        progression=((resource_database.get_item(f"Metroid DNA {artifact_number + 1}"), 1),),
        model=PickupModel(game=RandovaniaGame.METROID_SAMUS_RETURNS, name="adn"),
        pickup_category=METROID_DNA_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        offworld_models=frozendict({RandovaniaGame.AM2R: "sItemDNA"}),
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
        ),
    )


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDatabaseView) -> None:
    assert isinstance(configuration, MSRConfiguration)

    results.extend_with(artifact_pool(game, configuration.artifacts))


def artifact_pool(game: GameDatabaseView, config: MSRArtifactConfig) -> PoolResults:
    # Check whether we have valid artifact requirements in configuration
    max_artifacts = 0
    if config.prefer_anywhere:
        max_artifacts = 39
    if config.prefer_metroids:
        max_artifacts += 25
    if config.prefer_stronger_metroids:
        max_artifacts += 14
    if config.prefer_bosses and max_artifacts < 36:
        max_artifacts += 4
    if config.required_artifacts > max_artifacts:
        raise InvalidConfiguration("More Metroid DNA than allowed!")

    keys: list[PickupEntry] = [create_msr_artifact(i, game.get_resource_database_view()) for i in range(39)]
    keys_to_shuffle = keys[: config.placed_artifacts]
    starting_keys = keys[config.placed_artifacts :]

    return PoolResults(keys_to_shuffle, {}, starting_keys)
