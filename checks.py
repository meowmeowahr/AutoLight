from loguru import logger

from settings import Settings


def run_sanity(settings: Settings):
    passing = True
    if settings.sensor_count > settings.led_count:
        logger.critical(
            f"Led segments {settings.led_count} does "
            f"not match number of sensors "
            f"{settings.sensor_count}"
        )
        passing = False

    if settings.sensor_count != len(
        settings.sensor_calibrations
    ):
        logger.critical(
            f"Sensorcount {settings.sensor_count} does not "
            f"match number of calibrations "
            f"{len(settings.sensor_calibrations)}"
        )
        passing = False

    if passing:
        logger.success("All sanity checks passed")
    else:
        logger.critical("Sanity checks failed. Please check logs for more information")

    return passing
