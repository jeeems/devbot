import discord
from discord.ext import commands
import os
import logging
from core.analyzers import CodeAnalyzer, AICodeReviewer, ProjectStructureAnalyzer
from core.github_client import check_repo_access

logger = logging.getLogger(__name__)

class AnalysisCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.code_analyzer = CodeAnalyzer()
        self.ai_reviewer = AICodeReviewer()
        self.structure_analyzer = ProjectStructureAnalyzer()

    @commands.command(name='analyze')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def analyze_repo(self, ctx, repo_url: str, branch: str = "main"):
        """Analyze a GitHub repository for code quality and structure"""
        await ctx.send("🔍 Starting repository analysis...")
        
        try:
            # Parse repository URL
            if "github.com" not in repo_url:
                await ctx.send("❌ Please provide a valid GitHub repository URL")
                return
            
            repo_path = repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
            
            # Check repository access
            repo, error = check_repo_access(repo_path, branch)
            if error:
                await ctx.send(f"❌ {error}")
                return
            
            # Get repository contents
            try:
                # Use recursive=True to get all contents in one go
                # This reduces API calls and simplifies traversal
                contents = repo.get_contents("", ref=branch)
                all_repo_contents = []
                
                # Recursively flatten contents
                def flatten_contents(contents_list):
                    for content_item in contents_list:
                        if content_item.type == "dir":
                            try:
                                # Fetch sub-contents for directories
                                sub_contents = repo.get_contents(content_item.path, ref=branch)
                                flatten_contents(sub_contents)
                            except Exception as e:
                                logger.warning(f"Could not access directory {content_item.path}: {e}")
                        else:
                            all_repo_contents.append(content_item)
                
                flatten_contents(contents)

            except Exception as e:
                await ctx.send(f"❌ Error accessing branch '{branch}' or its contents: {str(e)}")
                return
            
            # Analyze project structure
            # Pass all_repo_contents for more accurate framework detection and structure analysis
            structure = self.structure_analyzer.analyze_structure(all_repo_contents)
            framework = self.structure_analyzer.detect_framework(all_repo_contents) # Pass all contents
            
            if framework:
                structure['framework'] = framework
            
            analyzed_files = []
            total_issues = 0
            
            # Process files (up to a reasonable limit to prevent hitting Discord's message limits)
            # Limiting to first 20 files for detailed analysis in embed
            files_to_analyze_detail = []
            for content_file in all_repo_contents:
                if content_file.type == "file":
                    file_ext = os.path.splitext(content_file.name)[1].lower()
                    
                    if file_ext in self.code_analyzer.supported_extensions:
                        files_to_analyze_detail.append(content_file)
            
            # Only analyze a subset for detailed output in Discord embed
            for content_file in files_to_analyze_detail[:20]: # Limit for detailed analysis in embed
                try:
                    file_content = content_file.decoded_content.decode('utf-8')
                    language = self.code_analyzer.supported_extensions[file_ext]
                    
                    # Enhanced analysis based on language
                    if file_ext == '.py':
                        analysis = self.code_analyzer.analyze_python_file(file_content)
                    elif file_ext == '.java':
                        analysis = self.code_analyzer.analyze_java_file(file_content)
                    elif file_ext in ['.js', '.ts', '.jsx', '.tsx']:
                        analysis = self.code_analyzer.analyze_javascript_file(file_content)
                    else:
                        analysis = {'info': f'Basic analysis for {language}'}
                    
                    analyzed_files.append({
                        'name': content_file.name,
                        'path': content_file.path,
                        'language': language,
                        'analysis': analysis,
                        'size': len(file_content)
                    })
                    
                    # Count issues
                    if 'potential_issues' in analysis:
                        total_issues += len(analysis['potential_issues'])
                    if 'unused_imports' in analysis:
                        total_issues += len(analysis['unused_imports'])
                    if 'unused_functions' in analysis:
                        total_issues += len(analysis['unused_functions'])
                    if 'suggestions' in analysis:
                        total_issues += len(analysis['suggestions'])
                    
                except Exception as e:
                    logger.error(f"Error analyzing {content_file.name}: {str(e)}")
                            
            if not analyzed_files:
                await ctx.send("❌ No supported code files found in repository or too many files to analyze.")
                return
            
            # Send structure analysis
            structure_embed = discord.Embed(
                title=f"📁 Project Structure Analysis: {repo.name}",
                description=f"**Framework:** {framework or 'Not detected'}\n**Branch:** {branch}",
                color=0x00ff00
            )
            
            if structure['issues']:
                structure_embed.add_field(
                    name="⚠️ Structure Issues",
                    value='\n'.join(structure['issues']),
                    inline=False
                )
            
            if structure['recommendations']:
                structure_embed.add_field(
                    name="💡 Recommendations",
                    value='\n'.join(structure['recommendations']),
                    inline=False
                )
            
            if framework and framework in self.structure_analyzer.structure_recommendations:
                rec_info = self.structure_analyzer.structure_recommendations[framework]
                structure_embed.add_field(
                    name=f"🏗️ {framework} Best Practices",
                    value=rec_info['description'],
                    inline=False
                )
            
            await ctx.send(embed=structure_embed)
            
            # Send code analysis summary
            embed = discord.Embed(
                title=f"📊 Code Analysis Summary: {repo.name}",
                description=f"**Files analyzed:** {len(analyzed_files)}\n**Total issues found:** {total_issues}",
                color=0x00ff00 if total_issues == 0 else 0xff9900
            )
            
            # Add field for each analyzed file with detailed issues/suggestions
            for file_info in analyzed_files[:8]:  # Show details for first 8 files
                analysis = file_info['analysis']
                issues_details = [] 
                
                if 'potential_issues' in analysis and analysis['potential_issues']:
                    issues_details.append("⚠️ **Potential Issues:**")
                    issues_details.extend([f"- {issue}" for issue in analysis['potential_issues'][:3]])
                    if len(analysis['potential_issues']) > 3:
                        issues_details.append(f"... ({len(analysis['potential_issues']) - 3} more)")
                
                if 'unused_imports' in analysis and analysis['unused_imports']:
                    issues_details.append("🔄 **Unused Imports:**")
                    issues_details.extend([f"- `{imp}`" for imp in analysis['unused_imports'][:5]])
                    if len(analysis['unused_imports']) > 5:
                        issues_details.append(f"... ({len(analysis['unused_imports']) - 5} more)")

                if 'unused_functions' in analysis and analysis['unused_functions']:
                    issues_details.append("🔄 **Unused Functions:**")
                    issues_details.extend([f"- `{func}`" for func in analysis['unused_functions'][:5]])
                    if len(analysis['unused_functions']) > 5:
                        issues_details.append(f"... ({len(analysis['unused_functions']) - 5} more)")
                
                if 'suggestions' in analysis and analysis['suggestions']:
                    issues_details.append("💡 **Suggestions:**")
                    issues_details.extend([f"- {sugg}" for sugg in analysis['suggestions'][:3]])
                    if len(analysis['suggestions']) > 3:
                        issues_details.append(f"... ({len(analysis['suggestions']) - 3} more)")
                
                embed.add_field(
                    name=f"📄 {file_info['name']} ({file_info['language']})",
                    value='\n'.join(issues_details) if issues_details else "✅ No specific issues or suggestions found",
                    inline=False
                )
            
            if len(analyzed_files) > 8:
                embed.add_field(
                    name="📝 Note",
                    value=f"Showing details for first 8 files. Total code files analyzed: {len(analyzed_files)}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            await ctx.send(f"❌ Error analyzing repository: {str(e)}")

    @commands.command(name='ai-review')
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def ai_review(self, ctx, repo_url: str, filename: str, branch: str = "main"):
        """Get AI-powered code review for a specific file"""
        await ctx.send("🤖 Starting AI code review...")
        
        try:
            # Parse repository URL
            if "github.com" not in repo_url:
                await ctx.send("❌ Please provide a valid GitHub repository URL")
                return
            
            repo_path = repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
            
            # Check repository access
            repo, error = check_repo_access(repo_path, branch)
            if error:
                await ctx.send(f"❌ {error}")
                return
            
            # Find and get file content
            file_path = self.code_analyzer.find_file_in_repo(repo, filename, branch)
            if not file_path:
                await ctx.send(f"❌ File '{filename}' not found in repository")
                return
            
            try:
                file_content_obj = repo.get_contents(file_path, ref=branch)
                file_content = file_content_obj.decoded_content.decode('utf-8')
            except Exception as e:
                await ctx.send(f"❌ Error reading file: {str(e)}")
                return
            
            # Determine language
            file_ext = os.path.splitext(filename)[1].lower()
            language = self.code_analyzer.supported_extensions.get(file_ext, 'text')
            
            # Get AI review
            context = f"Repository: {repo.name}\nBranch: {branch}\nFile path: {file_path}"
            
            async with ctx.typing():
                review = await self.ai_reviewer.review_with_groq(
                    file_content, language, filename, context
                )
            
            # Send review in chunks if needed
            max_length = 2000
            if len(review) > max_length:
                chunks = [review[i:i+max_length] for i in range(0, len(review), max_length)]
                for i, chunk in enumerate(chunks):
                    embed = discord.Embed(
                        title=f"🤖 AI Code Review: {filename} (Part {i+1}/{len(chunks)})",
                        description=chunk,
                        color=0x00ff00
                    )
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"🤖 AI Code Review: {filename}",
                    description=review,
                    color=0x00ff00
                )
                await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in AI review: {e}")
            await ctx.send(f"❌ Error during AI review: {str(e)}")

    @commands.command(name='structure')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def structure(self, ctx, repo_url: str, branch: str = "main"):
        """Show detailed project structure"""
        await ctx.send("🔍 Analyzing project structure...")
        
        try:
            # Parse repository URL
            if "github.com" not in repo_url:
                await ctx.send("❌ Please provide a valid GitHub repository URL")
                return
            
            repo_path = repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
            
            # Check repository access
            repo, error = check_repo_access(repo_path, branch)
            if error:
                await ctx.send(f"❌ {error}")
                return
            
            # Get repository contents (recursively to get all files/dirs for structure analysis)
            try:
                contents = repo.get_contents("", ref=branch)
                all_repo_contents = []
                
                def flatten_contents(contents_list):
                    for content_item in contents_list:
                        if content_item.type == "dir":
                            try:
                                sub_contents = repo.get_contents(content_item.path, ref=branch)
                                all_repo_contents.append(content_item) # Add directory itself
                                flatten_contents(sub_contents)
                            except Exception as e:
                                logger.warning(f"Could not access directory {content_item.path}: {e}")
                        else:
                            all_repo_contents.append(content_item)
                
                flatten_contents(contents)

            except Exception as e:
                await ctx.send(f"❌ Error accessing branch '{branch}' or its contents: {str(e)}")
                return
            
            # Analyze structure
            structure = self.structure_analyzer.analyze_structure(all_repo_contents)
            framework = self.structure_analyzer.detect_framework(all_repo_contents)
            
            embed = discord.Embed(
                title=f"📁 Project Structure: {repo.name}",
                description=f"**Framework:** {framework or 'Not detected'}\n**Branch:** {branch}",
                color=0x0099ff
            )
            
            # Files
            if structure['files']:
                files_list = structure['files'][:20]  # Show first 20 files
                embed.add_field(
                    name="📄 Files",
                    value='\n'.join(files_list) + (f"\n... and {len(structure['files']) - 20} more" if len(structure['files']) > 20 else ""),
                    inline=True
                )
            
            # Directories
            if structure['directories']:
                dirs_list = structure['directories'][:20]  # Show first 20 directories
                embed.add_field(
                    name="📁 Directories",
                    value='\n'.join(dirs_list) + (f"\n... and {len(structure['directories']) - 20} more" if len(structure['directories']) > 20 else ""),
                    inline=True
                )
            
            # Issues and recommendations
            if structure['issues']:
                embed.add_field(
                    name="⚠️ Issues",
                    value='\n'.join(structure['issues']),
                    inline=False
                )
            
            if structure['recommendations']:
                embed.add_field(
                    name="💡 Recommendations",
                    value='\n'.join(structure['recommendations']),
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error analyzing structure: {e}")
            await ctx.send(f"❌ Error analyzing structure: {str(e)}")

    @commands.command(name='search')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def search(self, ctx, repo_url: str, filename: str, branch: str = "main"):
        """Search for a specific file in the repository"""
        await ctx.send(f"🔍 Searching for '{filename}'...")
        
        try:
            # Parse repository URL
            if "github.com" not in repo_url:
                await ctx.send("❌ Please provide a valid GitHub repository URL")
                return
            
            repo_path = repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
            
            # Check repository access
            repo, error = check_repo_access(repo_path, branch)
            if error:
                await ctx.send(f"❌ {error}")
                return
            
            # Search for file
            file_path = self.code_analyzer.find_file_in_repo(repo, filename, branch)
            
            if file_path:
                try:
                    file_content_obj = repo.get_contents(file_path, ref=branch)
                    file_size = file_content_obj.size
                    
                    embed = discord.Embed(
                        title=f"📄 Found: {filename}",
                        description=f"**Path:** {file_path}\n**Size:** {file_size} bytes",
                        color=0x00ff00
                    )
                    
                    # Add file URL
                    embed.add_field(
                        name="🔗 GitHub URL",
                        value=f"[View on GitHub]({repo_url}/blob/{branch}/{file_path})",
                        inline=False
                    )
                    
                    await ctx.send(embed=embed)
                    
                except Exception as e:
                    await ctx.send(f"❌ Error accessing file: {str(e)}")
            else:
                await ctx.send(f"❌ File '{filename}' not found in repository")
                
        except Exception as e:
            logger.error(f"Error searching for file: {e}")
            await ctx.send(f"❌ Error searching for file: {str(e)}")

    @commands.command(name='upload')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def upload(self, ctx):
        """Upload a file for analysis"""
        if not ctx.message.attachments:
            await ctx.send("❌ Please attach a file to analyze")
            return
        
        attachment = ctx.message.attachments[0]
        
        # Check file size (max 1MB)
        if attachment.size > 1024 * 1024:
            await ctx.send("❌ File too large (max 1MB)")
            return
        
        # Check file extension
        file_ext = os.path.splitext(attachment.filename)[1].lower()
        if file_ext not in self.code_analyzer.supported_extensions:
            await ctx.send(f"❌ Unsupported file type: {file_ext}")
            return
        
        try:
            # Download and analyze file
            file_content = await attachment.read()
            content_str = file_content.decode('utf-8')
            language = self.code_analyzer.supported_extensions[file_ext]
            
            # Analyze based on language
            if file_ext == '.py':
                analysis = self.code_analyzer.analyze_python_file(content_str)
            elif file_ext == '.java':
                analysis = self.code_analyzer.analyze_java_file(content_str)
            elif file_ext in ['.js', '.ts', '.jsx', '.tsx']:
                analysis = self.code_analyzer.analyze_javascript_file(content_str)
            else:
                analysis = {'info': f'Basic analysis for {language}'}
            
            # Create analysis embed
            embed = discord.Embed(
                title=f"📄 File Analysis: {attachment.filename}",
                description=f"**Language:** {language}\n**Size:** {attachment.size} bytes",
                color=0x00ff00
            )
            
            # Add analysis results with full details (similar to analyze_repo)
            issues_details = []
            
            if 'potential_issues' in analysis and analysis['potential_issues']:
                issues_details.append("⚠️ **Potential Issues:**")
                issues_details.extend([f"- {issue}" for issue in analysis['potential_issues'][:5]])
                if len(analysis['potential_issues']) > 5:
                    issues_details.append(f"... ({len(analysis['potential_issues']) - 5} more)")
            
            if 'suggestions' in analysis and analysis['suggestions']:
                issues_details.append("💡 **Suggestions:**")
                issues_details.extend([f"- {sugg}" for sugg in analysis['suggestions'][:5]])
                if len(analysis['suggestions']) > 5:
                    issues_details.append(f"... ({len(analysis['suggestions']) - 5} more)")
            
            if 'unused_imports' in analysis and analysis['unused_imports']:
                issues_details.append("🔄 **Unused Imports:**")
                issues_details.extend([f"- `{imp}`" for imp in analysis['unused_imports'][:10]])
                if len(analysis['unused_imports']) > 10:
                    issues_details.append(f"... ({len(analysis['unused_imports']) - 10} more)")
            
            if 'unused_functions' in analysis and analysis['unused_functions']: 
                issues_details.append("🔄 **Unused Functions:**")
                issues_details.extend([f"- `{func}`" for func in analysis['unused_functions'][:5]])
                if len(analysis['unused_functions']) > 5:
                    issues_details.append(f"... ({len(analysis['unused_functions']) - 5} more)")

            embed.add_field(
                name="Analysis Results",
                value='\n'.join(issues_details) if issues_details else "✅ No specific issues or suggestions found",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error analyzing uploaded file: {e}")
            await ctx.send(f"❌ Error analyzing file: {str(e)}")

async def setup(bot):
    await bot.add_cog(AnalysisCog(bot))
    logger.info("Analysis cog loaded successfully")