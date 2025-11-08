
import requests
from requests.exceptions import RequestException, HTTPError, Timeout
from typing import List, Dict


class WikiSearch:
    """
    A lightweight wrapper for interacting with the Wikipedia API.

    This class allows you to search for Wikipedia articles based on a keyword,
    store the results, and fetch raw page contents for each matched title.
    """

    def get_keywords(self, keyword: str) -> List[str]:
        """
        Extract related Wikipedia article titles for a given keyword.

        This method searches Wikipedia using the input keyword, collects
        relevant article titles, and formats them for subsequent retrieval.

        Args:
            keyword (str): The search keyword or phrase.

        Returns:
            list[str]: A list of related article titles, formatted with '+' 
                    instead of spaces. Each item is guaranteed to be a string.
                    
        Type Schema for Function Calling:
            type: object
            properties:
                keyword:
                    type: string
                    description: The main search keyword to find related Wikipedia articles.
            required: ["keyword"]
        """
        if not keyword or not keyword.strip():
            raise ValueError("Keyword must be a non-empty string.")

        url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch={keyword}"

        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()

        json_response = response.json()
        search_results = json_response.get("query", {}).get("search", [])
        keyword_list = []


        for search in search_results:
            title = search.get("title", "").strip()
            if title:
                search_keyword = "+".join(title.split(" "))
                keyword_list.append(search_keyword)

        return keyword_list

    def get_keyword_page(self, search_keyword: str) -> List[Dict]:
        """
        Fetch the raw Wikipedia page content for a single keyword.

        Args:
            search_keyword (str): One Wikipedia article title.

        Returns:
            list[dict]: [{'title': search_keyword, 'content': page_content, 'url': search_url}]
        """
        
        url = f"https://en.wikipedia.org/w/index.php?title={search_keyword}&action=raw"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        
        content = response.content.decode("utf-8")
        

        if not content:
            print(f"⚠️ No valid pages were fetched. keyword: {search_keyword}")
        
        return [{"title": search_keyword, "content": content, "url": url}]
    




from typing import Any, Dict, List

class SearchTools:

    def __init__(self, index):
        self.index = index

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents in the index related to the given query.

        Args:
            query (str): The search query string.
            num_results (int, optional): The maximum number of search results to return. Default is 5.

        Returns:
            List[Dict[str, Any]]: 
                A list of search results, where each result is represented as a dictionary containing 
                the document’s metadata and content fields (e.g., title, summary, details).
                
        Example:
            >>> tools.search("LeBron James")
            [
                {"title": "LeBron James", "summary": "NBA player...", "details": "..."},
                {"title": "Michael Jordan", "summary": "Former NBA player...", "details": "..."}
            ]
        """
        boost = {"title": 2.0, "summary": 1.0, "details": 0.5}
        
        results = self.index.search(
            query=query,
            boost_dict=boost,
            num_results=num_results,
        )
        return results

    def _chunk_with_word_window(self, data, chunk_size=200, overlap=50):
        """
        Split a single record into overlapping word-based chunks.
        
        Args:
            data (dict): {'title': str, 'content': str}
            chunk_size (int): Number of words per chunk
            overlap (int): Overlap between chunks (in words)
        
        Returns:
            list[dict]: [{'title': ..., 'content': ...}, ...]
        """
        title = data["title"]
        words = data["content"].strip().split(" ")
        chunks = []
        
        start = 0
        total_words = len(words)
        
        while start < total_words:
            end = start + chunk_size
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            chunks.append({
                "title": title,
                "content": chunk_text
            })
            
            start += chunk_size - overlap  # slide window forward
        
        return chunks
    
    def _chunk_with_sliding_window(self, data, chunk_size=500, overlap=100):
        """
        Split a single record into overlapping chunks.
        
        Args:
            data (dict): {'title': str, 'content': str}
            chunk_size (int): Number of characters per chunk
            overlap (int): Overlap between chunks
        
        Returns:
            list[dict]: [{'title': ..., 'content': .... 'url': ....}, ...]
        """
        title = data["title"]
        content = data["content"].strip()
        url = data["url"]
        chunks = []

        start = 0
        text_length = len(content)

        while start < text_length:
            end = start + chunk_size
            chunk_text = content[start:end]
            
            chunks.append({
                "title": title,
                "content": chunk_text,
                "url": url
            })
            start += chunk_size - overlap

        return chunks

    def add_entry(self, data, chunk_size=500, overlap=100):

        """
        Add text entries into the index after chunking them into overlapping windows.

        This method takes a list of text records (each containing a 'title', 'content', 'url'),
        splits each record into smaller chunks using a sliding window, and appends the
        resulting chunks to the internal index.

        Args:
            data (list[dict]): A list of records, each with keys:
                - 'title' (str): The title of the text document.
                - 'content' (str): The full text content of the document.
                - 'url' (str): The url of the document.
            chunk_size (int, optional): Number of characters per chunk. Defaults to 500.
            overlap (int, optional): Number of overlapping characters between chunks.
                This helps preserve context continuity. Defaults to 100.

        Returns:
            list[dict]: A flattened list of all generated text chunks.
                Each element has the structure:
                {
                    'title': str,
                    'content': str
                    'url': str
                }
        """
        all_chunks = []

        for record in data:
            chunks = self._chunk_with_sliding_window(record, chunk_size, overlap)
            
            
            for chunk in chunks:
                self.index.append(chunk)
            all_chunks.extend(chunks)
        
        return all_chunks


