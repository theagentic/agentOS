import logging
import logging.config
import yaml
from pathlib import Path
from spotiauto.automation import PlaylistAutomation

def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    with open("config/config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    logging.basicConfig(
        level=config['logging']['level'],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config['logging']['file']),
            logging.StreamHandler()
        ]
    )

def run_automation():
    automation = PlaylistAutomation("config/config.yaml")
    automation.run()

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting one-time playlist automation")
    
    # Run once and exit
    run_automation()
    
    logger.info("Playlist automation completed, exiting")

if __name__ == "__main__":
    main()
