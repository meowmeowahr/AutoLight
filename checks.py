from loguru import logger

from settings import Settings, SettingsEnum


def run_sanity(settings: Settings):
    passing = True
    if settings.get_by_enum(SettingsEnum.SENSOR_COUNT) > settings.get_by_enum(
        SettingsEnum.MAIN_LED_COUNT
    ):
        logger.critical(
            f"Led segments {settings.get_by_enum(SettingsEnum.MAIN_LED_COUNT)} does "
            f"not match number of sensors "
            f"{settings.get_by_enum(SettingsEnum.SENSOR_COUNT)}"
        )
        passing = False

    if settings.get_by_enum(SettingsEnum.SENSOR_COUNT) != len(
        settings.get_by_enum(SettingsEnum.PER_SENSOR_CALIBRATIONS)
    ):
        logger.critical(
            f"Sensorcount {settings.get_by_enum(SettingsEnum.SENSOR_COUNT)} does not "
            f"match number of calibrations "
            f"{len(settings.get_by_enum(SettingsEnum.PER_SENSOR_CALIBRATIONS))}"
        )
        passing = False

    if passing:
        logger.success("All sanity checks passed")
    else:
        logger.critical("Sanity checks failed. Please check logs for more information")

    return passing
