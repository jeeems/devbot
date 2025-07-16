import os
import requests
import ast
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class ProjectStructureAnalyzer:
    def __init__(self):
        self.framework_patterns = {
            'React': ['package.json', 'src/App.js', 'src/index.js', 'public/index.html'],
            'Vue': ['package.json', 'src/main.js', 'src/App.vue'],
            'Angular': ['angular.json', 'src/main.ts', 'src/app/app.module.ts', 'src/index.html', 'src/app/'], # Added common Angular files/dirs
            'Django': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py'],
            'Flask': ['app.py', 'requirements.txt', 'templates/'],
            'Spring Boot': ['pom.xml', 'src/main/java/', 'application.properties'],
            'Express.js': ['package.json', 'app.js', 'server.js'],
            'Next.js': ['next.config.js', 'pages/', 'package.json'],
            'Laravel': ['composer.json', 'artisan', 'app/Http/Controllers/'],
            'Rails': ['Gemfile', 'config/routes.rb', 'app/controllers/'],
            'FastAPI': ['main.py', 'requirements.txt', 'app/'],
            'Nest.js': ['nest-cli.json', 'src/main.ts', 'src/app.module.ts']
        }

        self.structure_recommendations = {
            'React': {
                'recommended': ['src/components/', 'src/hooks/', 'src/utils/', 'src/services/', 'src/assets/'],
                'description': 'Component-based architecture with hooks and services'
            },
            'Django': {
                'recommended': ['apps/', 'static/', 'templates/', 'media/', 'requirements.txt'],
                'description': 'Django apps structure with proper separation of concerns'
            },
            'Spring Boot': {
                'recommended': ['src/main/java/com/company/app/', 'src/main/resources/', 'src/test/'],
                'description': 'Maven/Gradle structure with proper package organization'
            },
            'Express.js': {
                'recommended': ['routes/', 'middleware/', 'models/', 'controllers/', 'config/'],
                'description': 'MVC pattern with proper middleware and routing'
            },
            'Angular': {
                'recommended': ['src/app/components/', 'src/app/services/', 'src/app/models/', 'src/app/shared/', 'src/environments/'],
                'description': 'Modular Angular application structure with services, components, and shared modules'
            }
        }

    def detect_framework(self, repo_contents: List) -> Optional[str]:
        """Detect the framework used in the repository based on file paths."""

        # Create a set of all file and directory paths for efficient lookup
        all_paths = {content.path.lower() if content.type == 'file' else content.path.lower() + '/' for content in repo_contents}

        for framework, patterns in self.framework_patterns.items():
            matches = 0
            for pattern in patterns:
                # Adjust pattern to match GitHub content paths
                normalized_pattern = pattern.lower()
                if not normalized_pattern.endswith('/') and '.' not in os.path.basename(normalized_pattern): # It's a directory name without extension
                    normalized_pattern += '/'

                if any(normalized_pattern in p for p in all_paths): # Check if the normalized pattern exists within any path
                    matches += 1

            if matches >= 2: # At least 2 specific patterns must match for a framework
                # For Angular, check for angular.json as a strong indicator
                if framework == 'Angular' and 'angular.json' not in all_paths:
                    continue # Skip if angular.json isn't directly present for Angular

                return framework
        return None

    def analyze_structure(self, repo_contents: List, framework: str = None) -> Dict[str, Any]:
        """Analyze project structure and provide recommendations"""
        structure = {
            'framework': framework,
            'files': [],
            'directories': [],
            'issues': [],
            'recommendations': []
        }

        all_file_paths = []
        all_dir_paths = []

        for content in repo_contents:
            if content.type == 'file':
                structure['files'].append(content.path) # Store full path
                all_file_paths.append(content.path.lower())
            else: # content.type == 'dir'
                structure['directories'].append(content.path) # Store full path
                all_dir_paths.append(content.path.lower())

        # Check for common issues
        if 'readme.md' not in all_file_paths: # Check lowercase
            structure['issues'].append("Missing README.md file")

        if '.gitignore' not in all_file_paths: # Check lowercase
            structure['issues'].append("Missing .gitignore file")

        if framework and framework in self.structure_recommendations:
            rec = self.structure_recommendations[framework]
            for recommended_path in rec['recommended']:
                # For recommended paths, check if they exist as a file or directory
                normalized_rec_path = recommended_path.lower()

                if not any(normalized_rec_path in p for p in all_file_paths + all_dir_paths):
                    structure['recommendations'].append(f"Consider adding {recommended_path} for {framework} best practices.")

        return structure

class CodeAnalyzer:
    def __init__(self):
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sql': 'sql'
        }

    def find_file_in_repo(self, repo, filename: str, branch: str = "main") -> Optional[str]:
        """Recursively search for a file in the repository"""
        def search_recursive(contents, path=""):
            for content in contents:
                if content.type == "file" and content.name == filename:
                    return content.path
                elif content.type == "dir":
                    try:
                        sub_contents = repo.get_contents(content.path, ref=branch)
                        result = search_recursive(sub_contents, content.path)
                        if result:
                            return result
                    except Exception as e: # Added specific exception handling for sub_contents
                        logger.warning(f"Could not access directory {content.path} during search: {e}")
                        continue
            return None

        try:
            root_contents = repo.get_contents("", ref=branch)
            return search_recursive(root_contents)
        except Exception as e:
            logger.error(f"Error searching for file: {e}") # Use logger here
            return None

    def analyze_python_file(self, content: str) -> Dict[str, Any]:
        """Enhanced Python file analysis"""
        try:
            tree = ast.parse(content)
            analysis = {
                'imports': [],
                'functions': [],
                'classes': [],
                'variables': [],
                'unused_imports': [],
                'unused_functions': [],
                'unused_variables': [],
                'potential_issues': [],
                'suggestions': []
            }

            # Extract all definitions
            defined_names = set()
            used_names = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        analysis['imports'].append(name)
                        defined_names.add(name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            name = alias.asname if alias.asname else alias.name
                            analysis['imports'].append(name)
                            defined_names.add(name)
                elif isinstance(node, ast.FunctionDef):
                    analysis['functions'].append(node.name)
                    defined_names.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append(node.name)
                    defined_names.add(node.name)
                elif isinstance(node, ast.Name):
                    used_names.add(node.id)

            # Find unused items
            analysis['unused_imports'] = [name for name in analysis['imports'] if name not in used_names]

            # Find unused functions (more robust check, ensure it's not called)
            # This is a basic check; for full accuracy, control flow analysis is needed.
            # Here, we assume a function is unused if its name isn't explicitly 'called'
            # (or referenced) anywhere else in the code, excluding its definition.

            # Get all function names that are defined
            defined_functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}

            # Get all names that are called or referenced
            all_referenced_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call): # Function calls
                    if isinstance(node.func, ast.Name):
                        all_referenced_names.add(node.func.id)
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load): # Variable references
                    all_referenced_names.add(node.id)

            analysis['unused_functions'] = [func_name for func_name in defined_functions if func_name not in all_referenced_names and func_name not in analysis['classes']] # Exclude class names if functions are named same as classes

            # Check for potential issues
            if 'print(' in content:
                analysis['potential_issues'].append("Debug print statements found")
            if 'TODO' in content or 'FIXME' in content:
                analysis['potential_issues'].append("TODO/FIXME comments found")
            if 'except:' in content:
                analysis['potential_issues'].append("Bare except clauses found (use specific exceptions)")

            # Suggestions
            if len(analysis['functions']) > 50:
                analysis['suggestions'].append("Consider splitting this file - it has many functions")
            if any(len(line) > 100 for line in content.split('\n')):
                analysis['suggestions'].append("Some lines are too long (>100 characters)")

            return analysis

        except Exception as e:
            return {'error': str(e), 'potential_issues': [f"Parsing error: {str(e)}"]}

    def analyze_java_file(self, content: str) -> Dict[str, Any]:
        """Enhanced Java file analysis"""
        analysis = {
            'potential_issues': [],
            'suggestions': [],
            'imports': [],
            'classes': [],
            'methods': [],
            'unused_imports': [], # Added for Java
            'unused_methods': []  # Added for Java
        }

        lines = content.split('\n')

        # Extract imports
        for line in lines:
            if line.strip().startswith('import '):
                analysis['imports'].append(line.strip().replace('import ', '').replace(';', ''))

        # Extract classes and methods
        defined_methods = set()
        for line in lines:
            class_match = re.search(r'(public|private|protected)\s+(static\s+)?(class|interface)\s+(\w+)', line)
            if class_match:
                analysis['classes'].append(class_match.group(4))

            method_match = re.search(r'(public|private|protected)\s+(static\s+)?[\w<>]+\s+(\w+)\s*\([^)]*\)\s*\{', line)
            if method_match:
                method_name = method_match.group(3)
                analysis['methods'].append(method_name)
                defined_methods.add(method_name)

        # Basic check for unused methods (not exhaustive, actual call graph needed for true accuracy)
        for method_name in defined_methods:
            # Check if method name is referenced anywhere else, excluding its definition line
            method_referenced = False
            for line in lines:
                if method_name in line and f" {method_name}(" in line: # Simple heuristic for method call
                    if f" {method_name}(" not in line.split('{')[0]: # Not its own definition line
                        method_referenced = True
                        break
            if not method_referenced:
                analysis['unused_methods'].append(method_name)

        # Check for issues
        if 'System.out.println' in content:
            analysis['potential_issues'].append("System.out.println statements found (use logging framework like SLF4J)")
        if 'catch (Exception e)' in content or 'catch (Throwable t)' in content:
            analysis['potential_issues'].append("Catching generic Exception/Throwable (use specific exceptions for better error handling)")
        if '// TODO' in content or '// FIXME' in content:
            analysis['potential_issues'].append("TODO/FIXME comments found")
        if 'new File(' in content and 'try {' not in content:
            analysis['potential_issues'].append("File operations without try-with-resources or explicit close (resource leak risk)")
        if re.search(r'public\s+static\s+void\s+main\s*\(String\[\]\s+args\)', content) and len(analysis['classes']) > 1:
            analysis['suggestions'].append("Consider refactoring main method into a dedicated entry point class if project grows")


        # Suggestions
        if len(analysis['methods']) > 20:
            analysis['suggestions'].append("Consider refactoring this class - it has many methods (High Cohesion, Low Coupling principle)")
        if not any('private' in line or 'protected' in line for line in lines):
            analysis['suggestions'].append("Consider using private/protected access modifiers for better encapsulation")
        if 'java.util.Date' in content:
            analysis['suggestions'].append("Consider using java.time (JSR 310) for modern date/time API instead of java.util.Date")

        # Basic unused imports (very naive, depends on actual usage patterns)
        # For more accurate unused import detection, a full AST parsing or IDE-like analysis is needed.
        # This is a placeholder.
        used_imports_count = 0
        for imp in analysis['imports']:
            if re.search(r'\b' + re.escape(imp.split('.')[-1]) + r'\b', content):
                used_imports_count += 1
        if used_imports_count < len(analysis['imports']):
             analysis['unused_imports'].append("Some imports might be unused (manual verification recommended)")

        return analysis

    def analyze_javascript_file(self, content: str, language: str = 'javascript') -> Dict[str, Any]:
        """Enhanced JavaScript/TypeScript analysis"""
        analysis = {
            'potential_issues': [],
            'suggestions': [],
            'functions': [],
            'variables': [],
            'unused_functions': [], # Added for JS/TS
            'unused_variables': [] # Added for JS/TS
        }

        # Extract function definitions and variable declarations
        defined_names = set()
        used_names = set()

        # Function declarations (function keyword, arrow functions, class methods)
        function_patterns = [
            r'function\s+(\w+)\s*\(', # function foo() {}
            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\(.*?\)\s*=>)', # const foo = function() {} or const foo = () => {}
            r'class\s+\w+\s*\{[^}]*?(\w+)\s*\(.*?\)\s*\{' # class methods
        ]

        for pattern in function_patterns:
            for match in re.finditer(pattern, content):
                func_name = match.group(1)
                analysis['functions'].append(func_name)
                defined_names.add(func_name)

        # Variable declarations
        var_patterns = [
            r'(?:const|let|var)\s+([\w,\s]+)\s*=?.*?;', # const x = 1; let y, z;
            r'this\.(\w+)\s*=' # Class properties in TS/JS
        ]
        for pattern in var_patterns:
            for match in re.finditer(pattern, content):
                # Handle multiple variables in one declaration (e.g., let x, y;)
                vars_declared = re.findall(r'(\w+)', match.group(1))
                for var_name in vars_declared:
                    analysis['variables'].append(var_name)
                    defined_names.add(var_name)

        # Find all identifiers that are used
        # This is a very broad approach, a proper AST is needed for precision.
        # For simple usage, any word that looks like a variable/function name.
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
        used_names.update(words)

        # Basic unused detection (prone to false positives/negatives without AST)
        analysis['unused_functions'] = [name for name in analysis['functions'] if name not in used_names and not re.search(fr'\b{name}\s*\(', content)] # Check for calls
        analysis['unused_variables'] = [name for name in analysis['variables'] if name not in used_names and name not in analysis['functions']] # Ensure it's not a function name also

        # Check for issues
        if 'console.log' in content or 'console.error' in content or 'console.warn' in content:
            analysis['potential_issues'].append("Console.log/error/warn statements found (consider removing or using a proper logging library in production)")
        if 'var ' in content:
            analysis['suggestions'].append("Consider using 'let' or 'const' instead of 'var' for better block scoping")
        if re.search(r'==(?!=)', content): # Matches == but not ===
            analysis['suggestions'].append("Consider using strict equality (===) instead of (==) to avoid type coercion issues")
        if 'eval(' in content:
            analysis['potential_issues'].append("`eval()` usage found (potential security risk and performance implications)")
        if 'any' in content and language == 'typescript': # Use the passed 'language' here
            analysis['suggestions'].append("Extensive use of 'any' type in TypeScript (consider more specific types for better type safety)")
        if re.search(r'(?:private|public)\s+.*?:\s+\S+\s*=\s*new\s+\S+\(\)', content):
             analysis['potential_issues'].append("Direct instantiation of services/dependencies in components (consider Dependency Injection framework like Angular's or decorators for others)")

        # More suggestions
        if len(analysis['functions']) > 30:
            analysis['suggestions'].append("Consider refactoring this file - it has too many functions (violates Single Responsibility Principle)")
        if 'jQuery' in content or '$(' in content:
            analysis['suggestions'].append("Consider using modern JavaScript APIs or lighter alternatives instead of jQuery for new development")
        if re.search(r'subscribe\s*\(', content) and 'unsubscribe' not in content:
            analysis['potential_issues'].append("Observable subscriptions without explicit unsubscription (potential memory leak in Angular/RxJS contexts)")

        return analysis

class AICodeReviewer:
    def __init__(self):
        self.groq_endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.openai_endpoint = "https://api.openai.com/v1/chat/completions"

    async def review_with_groq(self, code: str, language: str, filename: str, context: str = "") -> str:
        """Enhanced Groq API review with better prompts"""
        if not GROQ_API_KEY:
            return "Groq API key not configured"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""
        As an expert {language} developer, review this code from '{filename}' and provide:

        1. **🐛 Potential Bugs**: Identify any bugs or logical errors
        2. **🔧 Code Quality**: Assess code structure, readability, and maintainability
        3. **⚡ Performance**: Suggest optimizations for better performance
        4. **🛡️ Security**: Identify security vulnerabilities
        5. **📏 Best Practices**: Recommend following language-specific best practices
        6. **🧹 Code Cleanup**: Suggest unused code removal and improvements

        {context}

        Code:
        ```{language}
        {code}
        ```

        Provide a detailed but concise review with specific examples and actionable suggestions.
        """

        data = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500,
            "temperature": 0.1
        }

        try:
            response = requests.post(self.groq_endpoint, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error calling Groq API: {str(e)}"

    async def chat_with_groq(self, message: str, context: str = "") -> str:
        """Chat functionality using Groq"""
        if not GROQ_API_KEY:
            return "Groq API key not configured"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""
        You are DevBot, an expert AI assistant specialized in software development.
        You help developers with code review, debugging, best practices, and project structure advice.

        {context}

        User question: {message}

        Provide helpful, accurate, and practical advice.
        """

        data = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.3
        }

        try:
            response = requests.post(self.groq_endpoint, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error calling Groq API: {str(e)}"