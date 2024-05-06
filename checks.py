import logging

import settings

from terminal import FancyDisplay, DisplayStatusTypes

def run_sanity(fancy_display: FancyDisplay | None = None):
    passing = True
    if settings.SENSOR_COUNT > settings.LED_COUNT:
        logging.critical(f"Led segments {settings.LED_COUNT} does not match number of sensors {settings.SENSOR_COUNT}")
        passing = False
    
    if not fancy_display:
        return passing
    
    if passing:
        fancy_display.display(DisplayStatusTypes.SUCCESS, "All sanity checks passed")
    else:
        fancy_display.display(DisplayStatusTypes.FAILURE, "Sanity checks failed. Please check logs for more information")
    
    return passing
