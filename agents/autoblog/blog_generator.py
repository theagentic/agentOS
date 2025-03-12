import re
from datetime import datetime
from typing import Dict, List
import requests
import json
import os

class BlogGenerator:
    def __init__(self, template: str):
        self.template = template
        self.openrouter_api_key = os.environ.get("OPENROUTER_API_KEY", "")
        
    def _extract_tags_from_readme(self, readme: str) -> List[str]:
        """Extract potential tags from the README content"""
        # Look for common programming languages and technologies
        tech_patterns = [
            'python', 'javascript', 'typescript', 'react', 'vue', 'angular',
            'node', 'django', 'flask', 'express', 'spring', 'java', 'golang',
            'rust', 'c\+\+', 'c#', 'php', 'ruby', 'rails', 'ai', 'ml',
            'machine learning', 'deep learning', 'data science', 'blockchain',
            'web3', 'frontend', 'backend', 'fullstack', 'devops', 'aws',
            'azure', 'gcp', 'cloud', 'docker', 'kubernetes'
        ]
        
        tags = set()
        readme_lower = readme.lower()
        
        for tech in tech_patterns:
            if re.search(r'\b' + tech + r'\b', readme_lower):
                tags.add(tech)
                
        return list(tags)
    
    def _summarize_readme(self, readme: str, max_length: int = 500) -> str:
        """Create a summary of the README content"""
        # Remove markdown headings
        clean_text = re.sub(r'#+ ', '', readme)
        
        # Remove URLs, code blocks, and other markdown formatting
        clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_text)
        clean_text = re.sub(r'```[\s\S]*?```', '', clean_text)
        clean_text = re.sub(r'`[^`]+`', '', clean_text)
        
        # Get first few paragraphs
        paragraphs = [p.strip() for p in clean_text.split('\n\n') if p.strip()]
        summary = '\n\n'.join(paragraphs[:3])
        
        if len(summary) > max_length:
            # Truncate and add ellipsis
            summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
            
        return summary
    
    def _generate_content_with_openrouter(self, repo_data: Dict) -> str:
        """Generate blog content using OpenRouter AI"""
        if not self.openrouter_api_key:
            print("Warning: OpenRouter API key not found. Falling back to basic content generation.")
            return None
            
        # Enhanced prompt to match the template style
        prompt = f"""You are a technical blogger with an ENTHUSIASTIC and CONVERSATIONAL style. 
Write a comprehensive blog post about the following GitHub project that matches this specific style:

Project Name: {repo_data['name']}
Description: {repo_data['description']}
Main Language: {repo_data['language']}
README Content: {repo_data['readme'][:1800]}

IMPORTANT STYLE GUIDELINES:
1. Start with an attention-grabbing hook, using a conversational tone directly addressing the reader ("you")
2. Use **bold text** for emphasis on key points and important terms
3. Incorporate rhetorical questions to engage readers
4. Use exclamation marks to convey enthusiasm! Lots of energy!
5. Structure content with clear H3 headers (### Header)
6. Include numbered lists and bullet points for clarity
7. Write in a casual, friendly tone as if talking to a tech-savvy friend
8. Include short, punchy sentences mixed with longer explanations
9. End with a motivational conclusion and clear call to action

CONTENT STRUCTURE:
1. Hook/Intro: An exciting, enthusiastic introduction to the project (with some bold text)
2. Project Overview: What it does and why it's cool
3. Key Features: Bullet points of the standout features
4. Technical Highlights: What makes this project technically impressive
5. Use Cases: How someone might use this in real life (with examples)
6. Pro Tips or Implementation Details: Practical advice related to the repo
7. Conclusion: Enthusiastic wrap-up with encouragement to check out the repo

The content should be in Markdown format. Make it sound excited about technology!
DO NOT include a title or any front matter - just the body content.
"""

        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": "meta-llama/llama-3.3-70b-instruct:free",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,  # Add some creativity
                    "max_tokens": 1500,  # Allow for longer responses
                }),
                timeout=60  # Add timeout to prevent hanging
            )
            
            response.raise_for_status()
            result = response.json()
            if result.get('choices') and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            return None
            
        except Exception as e:
            print(f"Error generating content with OpenRouter: {e}")
            return None
    
    def _enhance_content_formatting(self, content: str) -> str:
        """Add additional formatting enhancements to the content"""
        # Ensure there are enough bold elements (at least 3)
        bold_count = len(re.findall(r'\*\*[^*]+\*\*', content))
        if bold_count < 3:
            # Find important terms to make bold
            important_terms = ['project', 'features', 'code', 'solution', 'implementation', 
                              'framework', 'library', 'tool', 'application']
            for term in important_terms:
                # Only replace the first occurrence of each term, up to 3 total replacements
                if bold_count >= 3:
                    break
                pattern = r'(?<!\*)({}|{}s)(?!\*)'.format(term, term)  # Match term or plural form
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    replacement = f"**{match.group(0)}**"
                    content = content[:match.start()] + replacement + content[match.end():]
                    bold_count += 1
        
        # Ensure there's at least one rhetorical question if none exists
        if '?' not in content:
            question_options = [
                "\n\nWant to know the best part? ",
                "\n\nCurious about how it all works? ",
                "\n\nWondering how this could level up your projects? ",
                "\n\nReady to see how this could transform your workflow? "
            ]
            import random
            content += random.choice(question_options)
        
        # Ensure there's at least one exclamation if none exists
        if '!' not in content:
            content = content.rstrip() + "\n\nExcited to check it out? You should be!"
            
        return content
    
    def generate_blog_post(self, repo_data: Dict) -> str:
        """Generate a complete blog post from repository data"""
        # Extract key information
        repo_name = repo_data['name']
        description = repo_data['description']
        readme = repo_data['readme']
        main_language = repo_data['language'] or "Not specified"
        
        # Generate title
        title = repo_name.replace('-', ' ').replace('_', ' ').title()
        if description:
            title = f"{title}: {description.rstrip('.')}"
            
        # Extract tags
        tags = self._extract_tags_from_readme(readme)
        if main_language and main_language.lower() not in [t.lower() for t in tags]:
            tags.append(main_language.lower())
        tags_str = ', '.join([f'"{tag}"' for tag in tags])
        
        # Format dates
        created_date = datetime.strptime(repo_data['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Try to generate content with OpenRouter
        ai_content = self._generate_content_with_openrouter(repo_data)
        
        # If AI content generation failed, fall back to basic content
        if not ai_content:
            # Create content using the original method
            content_parts = []
            
            # Add introduction
            if description:
                content_parts.append(f"## Introduction\n\nOkay, buckle up tech enthusiasts! Let me introduce you to **{repo_name}** - {description} This isn't just another project, it's a game-changer in the world of {main_language}!")
            
            # Add README content
            readme_summary = self._summarize_readme(readme)
            content_parts.append(f"### Project Overview\n\n{readme_summary}\n\nAre you getting excited yet? You should be!")
            
            # Add code samples if available
            if repo_data['code_samples']:
                content_parts.append("### Code Highlights\n\nLet's dive into some **awesome code** that makes this project tick:")
                for file_name, code in list(repo_data['code_samples'].items())[:2]:
                    code_lines = code.split('\n')[:15]
                    code_snippet = '\n'.join(code_lines)
                    if len(code_lines) < len(code.split('\n')):
                        code_snippet += "\n// ... more code ..."
                    content_parts.append(f"#### {file_name}\n\n```\n{code_snippet}\n```")
            
            # Add conclusion
            content_parts.append("### Conclusion\n\nWow! This project demonstrates incredible skills in "
                            f"**{main_language}** and {', '.join(tags[:3])}. "
                            f"Check out the repository for more details and feel free to contribute! Trust me, you don't want to miss this one!")
            
            # Combine all content
            full_content = '\n\n'.join(content_parts)
        else:
            # Use the AI-generated content and enhance it
            full_content = self._enhance_content_formatting(ai_content)
            
            # Add code samples if they weren't included in the AI content
            if repo_data['code_samples'] and "```" not in full_content:
                code_parts = ["### Code Highlights\n\nCheck out this **awesome code snippet** from the project:"]
                for file_name, code in list(repo_data['code_samples'].items())[:1]:
                    code_lines = code.split('\n')[:10]
                    code_snippet = '\n'.join(code_lines)
                    if len(code_lines) < len(code.split('\n')):
                        code_snippet += "\n// ... more code ..."
                    code_parts.append(f"#### {file_name}\n\n```\n{code_snippet}\n```")
                full_content += '\n\n' + '\n\n'.join(code_parts)
        
        # Fill in the template
        blog_post = self.template.format(
            title=title,
            date=current_date,
            tags=tags_str,
            content=full_content,
            repo_name=repo_name,
            repo_url=repo_data['url'],
            created_date=created_date,
            main_language=main_language
        )
        
        return blog_post
