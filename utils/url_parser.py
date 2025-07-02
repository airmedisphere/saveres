import re
from typing import Tuple, Optional
from urllib.parse import urlparse, parse_qs
from utils.logger import log_error, log_info

class URLParser:
    """Advanced URL parser for Telegram links"""
    
    def __init__(self):
        # Comprehensive regex patterns for all Telegram URL formats
        self.patterns = {
            'public_channel': re.compile(r'https?://t\.me/([a-zA-Z0-9_]+)/(\d+)(?:-(\d+))?'),
            'private_channel': re.compile(r'https?://t\.me/c/(\d+)/(\d+)(?:-(\d+))?'),
            'bot_message': re.compile(r'https?://t\.me/b/([a-zA-Z0-9_]+)/(\d+)(?:-(\d+))?'),
            'joinchat': re.compile(r'https?://t\.me/joinchat/([a-zA-Z0-9_-]+)'),
            'plus_invite': re.compile(r'https?://t\.me/\+([a-zA-Z0-9_-]+)'),
            'username_with_params': re.compile(r'https?://t\.me/([a-zA-Z0-9_]+)\?start=([a-zA-Z0-9_-]+)'),
            'message_with_params': re.compile(r'https?://t\.me/([a-zA-Z0-9_]+)/(\d+)\?([^#]+)'),
            'private_with_params': re.compile(r'https?://t\.me/c/(\d+)/(\d+)\?([^#]+)'),
        }
    
    def parse_url(self, url: str) -> Tuple[Optional[str], Optional[int], Optional[int], str]:
        """
        Parse Telegram URL and extract chat_id, from_id, to_id, and type
        Returns: (chat_id, from_id, to_id, url_type)
        """
        try:
            url = url.strip()
            
            # Remove any trailing parameters that might interfere
            url = re.sub(r'[?&]single.*$', '', url)
            url = re.sub(r'[?&]comment.*$', '', url)
            url = re.sub(r'[?&]thread.*$', '', url)
            
            log_info(f"Parsing URL: {url}")
            
            # Public channel/group messages
            match = self.patterns['public_channel'].match(url)
            if match:
                username = match.group(1)
                from_id = int(match.group(2))
                to_id = int(match.group(3)) if match.group(3) else from_id
                return f"@{username}", from_id, to_id, "public"
            
            # Private channel/group messages
            match = self.patterns['private_channel'].match(url)
            if match:
                chat_id = int(f"-100{match.group(1)}")
                from_id = int(match.group(2))
                to_id = int(match.group(3)) if match.group(3) else from_id
                return chat_id, from_id, to_id, "private"
            
            # Bot messages
            match = self.patterns['bot_message'].match(url)
            if match:
                bot_username = match.group(1)
                from_id = int(match.group(2))
                to_id = int(match.group(3)) if match.group(3) else from_id
                return f"@{bot_username}", from_id, to_id, "bot"
            
            # Message with parameters
            match = self.patterns['message_with_params'].match(url)
            if match:
                username = match.group(1)
                message_id = int(match.group(2))
                return f"@{username}", message_id, message_id, "public"
            
            # Private with parameters
            match = self.patterns['private_with_params'].match(url)
            if match:
                chat_id = int(f"-100{match.group(1)}")
                message_id = int(match.group(2))
                return chat_id, message_id, message_id, "private"
            
            # Handle range formats with spaces and different separators
            range_patterns = [
                r'(\d+)\s*-\s*(\d+)',
                r'(\d+)\s*to\s*(\d+)',
                r'(\d+)\s*:\s*(\d+)',
                r'(\d+)\s*~\s*(\d+)',
            ]
            
            for pattern in range_patterns:
                if re.search(pattern, url):
                    # Re-parse with range
                    for url_pattern in self.patterns.values():
                        match = url_pattern.match(url.split('?')[0])  # Remove query params
                        if match:
                            groups = match.groups()
                            if len(groups) >= 2:
                                # Extract range from the URL
                                range_match = re.search(pattern, url)
                                if range_match:
                                    from_id = int(range_match.group(1))
                                    to_id = int(range_match.group(2))
                                    
                                    if 'c/' in url:
                                        chat_id = int(f"-100{groups[0]}")
                                        return chat_id, from_id, to_id, "private"
                                    elif 'b/' in url:
                                        return f"@{groups[0]}", from_id, to_id, "bot"
                                    else:
                                        return f"@{groups[0]}", from_id, to_id, "public"
            
            # If no pattern matches, try to extract basic info
            if 't.me/' in url:
                parts = url.split('/')
                if len(parts) >= 4:
                    if 'c' in parts and len(parts) >= 6:
                        # Private channel
                        chat_id = int(f"-100{parts[4]}")
                        msg_id = int(parts[5].split('?')[0].split('-')[0])
                        return chat_id, msg_id, msg_id, "private"
                    elif 'b' in parts and len(parts) >= 6:
                        # Bot message
                        bot_username = parts[4]
                        msg_id = int(parts[5].split('?')[0].split('-')[0])
                        return f"@{bot_username}", msg_id, msg_id, "bot"
                    elif len(parts) >= 5 and parts[4].isdigit():
                        # Public channel
                        username = parts[3]
                        msg_id = int(parts[4].split('?')[0].split('-')[0])
                        return f"@{username}", msg_id, msg_id, "public"
            
            raise ValueError("URL format not recognized")
            
        except Exception as e:
            log_error(e, f"parse_url: {url}")
            raise ValueError(f"Invalid URL format: {str(e)}")
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is a valid Telegram URL"""
        try:
            self.parse_url(url)
            return True
        except:
            return False
    
    def extract_invite_link(self, url: str) -> Optional[str]:
        """Extract invite hash from join links"""
        try:
            # Handle joinchat links
            match = self.patterns['joinchat'].match(url)
            if match:
                return match.group(1)
            
            # Handle + invite links
            match = self.patterns['plus_invite'].match(url)
            if match:
                return match.group(1)
            
            return None
        except Exception as e:
            log_error(e, f"extract_invite_link: {url}")
            return None

# Global URL parser instance
url_parser = URLParser()