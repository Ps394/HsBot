from Client import Client
from Logger import logger, setup_logging, logging

if __name__ == "__main__":
    setup_logging(log_file="bot.log", level=logging.INFO)

    import os
    import sys
    
    # Try to get token from environment variable
    TOKEN = os.getenv("WZ_BOT_TOKEN")
    
    # On Windows, try to get token from Registry if not in environment
    if not TOKEN and sys.platform == "win32":
        try:
            import winreg
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\HsBot", 0, winreg.KEY_READ)
            TOKEN, _ = winreg.QueryValueEx(reg_key, "WZ_BOT_TOKEN")
            winreg.CloseKey(reg_key)
            logger.info("Bot token loaded from Windows Registry")
        except (FileNotFoundError, OSError):
            pass
    
    # On Linux/Unix, try to get token from config file
    if not TOKEN and sys.platform in ("linux", "darwin"):
        config_file = os.path.expanduser("~/.config/hsbot/config")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        if line.startswith("WZ_BOT_TOKEN="):
                            TOKEN = line.split("=", 1)[1].strip()
                            logger.info("Bot token loaded from config file")
                            break
            except Exception as e:
                logger.warning(f"Failed to read config file: {e}")
    
    if not TOKEN:
        logger.error("No bot token found!")
        logger.error("Please set WZ_BOT_TOKEN environment variable or run install script to configure token.")
        sys.exit(1)

    bot = Client(global_command_sync=False)
    logger.info("Starting bot...")
    bot.run(TOKEN)
    logger.info("Bot stopped...")