from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.super_metroid.layout.super_metroid_configuration import SuperMetroidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def super_metroid_specific_pool(results: PoolResults, configuration: BaseConfiguration, game: GameDatabaseView):
    assert isinstance(configuration, SuperMetroidConfiguration)
