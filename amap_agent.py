import os
import requests
import google.generativeai as genai
import argparse
import json
import re

# Get API keys from environment variables
AMAP_API_KEY = os.environ.get("AMAP_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not AMAP_API_KEY or not GEMINI_API_KEY:
    raise ValueError("Please set the AMAP_API_KEY and GEMINI_API_KEY environment variables.")

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

def search_amap(query, city=None):
    """
    Searches the Amap API for a given query.
    """
    url = f"https://restapi.amap.com/v3/place/text?key={AMAP_API_KEY}&keywords={query}"
    if city:
        url += f"&city={city}&citylimit=true"
    response = requests.get(url)
    return response.json()

def get_location_from_gemini(query):
    """
    Uses Gemini to extract a location from a query.
    """
    prompt = f"""From the user query, extract the location and the city. Return a JSON object with two keys: 'location' and 'city_chinese'.
- 'location' should be the search term.
- 'city_chinese' should be the name of the city, translated into Chinese. If the city is not a major one or is ambiguous, return an empty string.

Examples:
- User Query: "restaurants in Beijing" -> {{"location": "restaurants", "city_chinese": "北京"}}
- User Query: "tourist attractions in Shanghai" -> {{"location": "tourist attractions", "city_chinese": "上海"}}
- User Query: "Eiffel Tower" -> {{"location": "Eiffel Tower", "city_chinese": ""}}

User Query: "{query}"
"""
    response = model.generate_content(prompt)
    print(f"DEBUG: Raw Gemini response: {response.text}")
    try:
        # Use regex to find the JSON block. This is more robust.
        # It looks for a json block that starts with ```json and ends with ```
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)
        else:
            # If no markdown block is found, try to parse the whole string
            return json.loads(response.text)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error decoding Gemini response: {e}")
        # Fallback to using the raw query if Gemini fails
        return {"location": query, "city": ""}


def summarize_with_gemini(search_results):
    """
    Summarizes the search results using the Gemini API.
    """
    prompt = f"Please summarize the following Amap search results in a user-friendly way. For each point of interest, include its name, address, and phone number if available. \n\n{json.dumps(search_results, indent=2, ensure_ascii=False)}"
    response = model.generate_content(prompt)
    return response.text

def main():
    """
    Main function for the Amap agent.
    """
    parser = argparse.ArgumentParser(description="Search for a location using Amap and Gemini.")
    parser.add_argument("query", type=str, help="The location to search for (e.g., 'restaurants in Beijing').")
    args = parser.parse_args()

    print(f"Analyzing your query: '{args.query}' with Gemini...")
    location_info = get_location_from_gemini(args.query)
    search_query = location_info.get("location", args.query)
    city = location_info.get("city_chinese", "")


    print(f"Searching for: '{search_query}' in city: '{city or 'any'}'")

    # Search Amap
    search_results = search_amap(search_query, city)

    if search_results["status"] == "1" and int(search_results["count"]) > 0:
        # Summarize with Gemini
        print("\nSummarizing results with Gemini...")
        summary = summarize_with_gemini(search_results)
        print("\nSummary from Gemini:")
        print(summary)
    else:
        print("No results found or an error occurred.")
        print("Amap API Response:", search_results)


if __name__ == "__main__":
    main()
