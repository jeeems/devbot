import sys
import discord
from discord.ext import commands
import os
import logging
from core.analyzers import AICodeReviewer

logger = logging.getLogger(__name__)

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_reviewer = AICodeReviewer()

    @commands.command(name='chat')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def chat_with_ai(self, ctx, *, message: str):
        """Chat with AI assistant for development help"""
        if not message.strip():
            await ctx.send("❌ Please provide a message to chat with the AI.")
            return
            
        # Send typing indicator
        async with ctx.typing():
            try:
                response = await self.ai_reviewer.chat_with_groq(message)
                
                # Send response in chunks if too long
                max_length = 2000
                if len(response) > max_length:
                    chunks = [response[i:i+max_length] for i in range(0, len(response), max_length)]
                    for i, chunk in enumerate(chunks):
                        embed = discord.Embed(
                            title=f"🤖 DevBot Response (Part {i+1}/{len(chunks)})",
                            description=chunk,
                            color=0x00ff00
                        )
                        await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="🤖 DevBot Response",
                        description=response,
                        color=0x00ff00
                    )
                    await ctx.send(embed=embed)
                    
            except Exception as e:
                logger.error(f"Error in chat command: {e}")
                await ctx.send(f"❌ Error getting AI response: {str(e)}")

    @commands.command(name='help-dev')
    async def help_dev(self, ctx):
        """Show all available commands"""
        embed = discord.Embed(
            title="🤖 DevBot Commands",
            description="AI-powered code analysis and development assistant",
            color=0x0099ff
        )
        
        # Repository Analysis Commands
        embed.add_field(
            name="📁 Repository Analysis",
            value=(
                "`!analyze <repo_url> [branch]` - Analyze GitHub repository\n"
                "`!structure <repo_url> [branch]` - Show project structure\n"
                "`!search <repo_url> <filename>` - Search for specific file\n"
                "`!compare <repo_url> <file1> <file2>` - Compare two files"
            ),
            inline=False
        )
        
        # AI Review Commands
        embed.add_field(
            name="🔍 AI Code Review",
            value=(
                "`!ai-review <repo_url> <filename>` - AI code review\n"
                "`!upload` - Upload file for analysis\n"
                "`!chat <message>` - Chat with AI assistant"
            ),
            inline=False
        )
        
        # Bot Commands
        embed.add_field(
            name="🤖 Bot Commands",
            value=(
                "`!status` - Check bot status\n" # Updated command name here
                "`!help-dev` - Show this help message"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 Examples",
            value=(
                "`!analyze https://github.com/user/repo`\n"
                "`!ai-review https://github.com/user/repo main.py`\n"
                "`!chat How do I optimize this Python code?`"
            ),
            inline=False
        )
        
        embed.set_footer(text="DevBot v1.0 - Powered by AI")
        await ctx.send(embed=embed)

    # FIX: Renamed the command from 'bot_status' to 'status'
    @commands.command(name='status')
    async def status(self, ctx):
        """Check bot status and API availability"""
        embed = discord.Embed(
            title="🤖 DevBot Status",
            color=0x00ff00
        )
        
        # Bot info
        embed.add_field(
            name="🔧 Bot Status",
            value=f"✅ Online\n📊 Guilds: {len(self.bot.guilds)}\n👥 Users: {len(self.bot.users)}",
            inline=True
        )
        
        # API status
        api_status = []
        
        # Check GitHub API
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            api_status.append("✅ GitHub API: Connected")
        else:
            api_status.append("❌ GitHub API: Not configured")
        
        # Check Groq API
        groq_token = os.getenv('GROQ_API_KEY')
        if groq_token:
            api_status.append("✅ Groq AI: Connected")
        else:
            api_status.append("❌ Groq AI: Not configured")
        
        # Check OpenAI API
        openai_token = os.getenv('OPENAI_API_KEY')
        if openai_token:
            api_status.append("✅ OpenAI: Connected")
        else:
            api_status.append("❌ OpenAI: Not configured")
        
        embed.add_field(
            name="🔑 API Status",
            value="\n".join(api_status),
            inline=True
        )
        
        # System info
        embed.add_field(
            name="💻 System",
            value=f"🐍 Python: {sys.version_info.major}.{sys.version_info.minor}\n📦 discord.py: {discord.__version__}",
            inline=True
        )
        
        embed.set_footer(text="DevBot v2.0")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors for this cog"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Missing required argument. Use `!help-dev` for usage.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f}s.")
        elif isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        else:
            logger.error(f"Command error in {ctx.command}: {error}")
            await ctx.send(f"❌ An error occurred: {str(error)}")

async def setup(bot):
    await bot.add_cog(GeneralCog(bot))
    logger.info("General cog loaded successfully")