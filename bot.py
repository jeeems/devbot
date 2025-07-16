import discord
from discord.ext import commands
import os
import asyncio
import logging
from dotenv import load_dotenv
import sys

# Set up logging with UTF-8 encoding for all handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        # Ensure the console handler also uses UTF-8
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# This block is helpful for Windows but the handler encoding is the main fix
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class DevBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        # The command prefix was missing in the original file, adding it back.
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        """This is called when the bot is starting up"""
        logger.info("Setting up bot...")
        
        # Correctly locate the cogs directory relative to the bot.py file
        cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs') if '__file__' in locals() else 'cogs'
        if os.path.exists(cogs_dir):
            for filename in os.listdir(cogs_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    try:
                        # Assuming your cogs are in a 'cogs' subdirectory
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        logger.info(f"✅ Loaded Cog: {filename}")
                    except Exception as e:
                        logger.error(f"❌ Failed to load cog {filename}: {e}", exc_info=True)
        else:
            logger.warning("Cogs directory not found. Creating it...")
            os.makedirs(cogs_dir, exist_ok=True)
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        try:
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="for !help-dev"
                )
            )
        except Exception as e:
            logger.error(f"Failed to set presence: {e}")
    
    async def on_disconnect(self):
        """Called when the bot disconnects"""
        logger.warning("Bot disconnected from Discord")
    
    async def on_resumed(self):
        """Called when the bot resumes connection"""
        logger.info("Bot resumed connection to Discord")
    
    async def on_error(self, event, *args, **kwargs):
        """Global error handler"""
        logger.error(f"An error occurred in event {event}", exc_info=True)
    
    # The global on_command_error handler in bot.py can be simplified
    # since each cog already has a specific error handler.
    # This remains as a fallback.
    async def on_command_error(self, ctx, error):
        """Global command error handler"""
        # Let cog-specific handlers take precedence
        if ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
            return

        if isinstance(error, commands.CommandNotFound):
            return 
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing a required argument. Use `!help-dev` to see command usage.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ This command is on cooldown. Please try again in {error.retry_after:.1f}s.")
        else:
            logger.error(f"An unhandled error occurred in command '{ctx.command}': {error}", exc_info=True)
            await ctx.send(f"❌ An unexpected error occurred. Please check the logs.")


async def main():
    # Load environment variables
    load_dotenv()
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

    if not DISCORD_TOKEN:
        logger.error("❌ Error: DISCORD_TOKEN environment variable not set")
        return

    # Create bot instance
    bot = DevBot()
    
    try:
        # Start the bot
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except discord.LoginFailure:
        logger.error("❌ Invalid Discord token")
    except Exception as e:
        logger.error(f"❌ Unexpected error during bot startup: {e}", exc_info=True)
    finally:
        # Ensure proper cleanup
        if bot and not bot.is_closed():
            await bot.close()
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    try:
        # For Windows, setting the asyncio event loop policy can prevent certain errors
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error in main execution: {e}")
        logging.error(f"Fatal error: {e}", exc_info=True)