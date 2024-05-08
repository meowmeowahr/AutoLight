from loguru import logger

import settings

def run_sanity():
    passing = True
    if settings.SENSOR_COUNT > settings.LED_COUNT:
        logger.critical(f"Led segments {settings.LED_COUNT} does not match number of sensors {settings.SENSOR_COUNT}")
        passing = False

    if settings.SENSOR_COUNT != len(settings.PER_SENSOR_CALIBRATIONS):
        logger.critical(f"Sensorcount {settings.SENSOR_COUNT} does not match number of calibrations {len(settings.PER_SENSOR_CALIBRATIONS)}")
        passing = False
    
    if passing:
        logger.success("All sanity checks passed")
    else:
        logger.critical("Sanity checks failed. Please check logs for more information")
    
    return passing
