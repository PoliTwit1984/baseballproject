import openai  # Used for accessing OpenAI's API for generating summaries
import requests  # Used for making HTTP requests to the Bing Search API and scraping article content
from bs4 import BeautifulSoup  # Used for parsing HTML content of articles for text extraction
import datetime  # Used for generating the current date for the LinkedIn post header
from dotenv import load_dotenv  # Used for loading environment variables from a .env file
import os  # Used for accessing environment variables

# Load environment variables from a .env file
load_dotenv()

# Set up your OpenAI API key from environment variables
oai_key = os.getenv('OPEN_AI_API_KEY')
client = openai.OpenAI(api_key=oai_key)  # Initialize the OpenAI client with the API key

# Bing Search API setup
search_url = "https://api.bing.microsoft.com/v7.0/news/search"  # Bing Search API endpoint

# Search query parameters
query = "(microsoft copilot) OR (github copilot)"  # Query for articles about Microsoft or GitHub Copilot
freshness = "Day"  # Limit results to the last 24 hours
market = "en-US"  # Target market for the search results

# Set the headers with the Bing Search API subscription key from environment variables
bing_subscription_key = os.getenv('BING_API_KEY')
headers = {"Ocp-Apim-Subscription-Key": bing_subscription_key}

# Parameters for the Bing Search API request
params = {
    "q": query,
    "freshness": freshness,
    "mkt": market
}

# Make the GET request to the Bing Search API
response = requests.get(search_url, headers=headers, params=params)
response.raise_for_status()  # Raise an exception for HTTP errors

# Parse the JSON response to extract news articles
search_results = response.json()
articles = search_results.get('value', [])  # Extract the 'value' key containing articles

# Function to scrape article text and validate URL
def get_article_text_and_validate_url(url):
    try:
        article_response = requests.get(url, timeout=10)
        article_response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(article_response.text, 'html.parser')  # Parse the HTML content

        # Extract text from paragraph tags
        paragraphs = soup.find_all('p')
        article_text = ' '.join([p.get_text().strip() for p in paragraphs])
        
        # Clean the URL for readability
        cleaned_url = article_response.url
        return cleaned_url, article_text.strip()
    except requests.exceptions.RequestException as e:
        return None, None  # Return None if there's an error

# Process each article to extract text
articles_list = []
for article in articles:
    url, article_text = get_article_text_and_validate_url(article.get('url'))
    
    if url and article_text:
        article_text = ' '.join(article_text.split())  # Clean up whitespace
        articles_list.append((url, article_text))

# Function to generate a LinkedIn post from article summaries
def generate_linkedin_post(articles):
    article_summaries = []
    for url, article_text in articles:
        # Generate a summary for each article using OpenAI's API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a LinkedIn influencer specializing in AI and technology trends. Your followers look to you for insights and actionable advice."},
                {"role": "user", "content": f"Summarize this article in a concise short and engaging way for a LinkedIn post using just one sentence focusing on Microsoft Copilot, do not use any hashtags:\n\n{article_text}"}
            ]
        )
        summary = response.choices[0].message.content.strip()
        article_summaries.append((url, summary))

    # Sort summaries by length for prioritization
    article_summaries = sorted(article_summaries, key=lambda x: len(x[1]), reverse=True)

    # Format the LinkedIn post with the current date and article summaries
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    linkedin_post = f"🚀 **Microsoft Copilot News of the Day - {today} automated by Azure Bing Search Service and Azure Open AI** 🚀\n"

    for url, summary in article_summaries:
        linkedin_post += f"\n- {summary} -{url} \n"

    return linkedin_post

# Generate the LinkedIn post
linkedin_post = generate_linkedin_post(articles_list)

# Define hashtags for the LinkedIn post
hashtags = "#Microsoft #AI #Copilot #Innovation #TechNews #Productivity"

# Save the LinkedIn post to a text file and append the hashtags
with open('linkedin_post.txt', 'w', encoding='utf-8') as txtfile:
    txtfile.write(linkedin_post)
    txtfile.write(f"\n{hashtags}")

print("LinkedIn post created successfully!")

# Display the LinkedIn post content and hashtags
print(linkedin_post)
print(f"\n\n{hashtags}")