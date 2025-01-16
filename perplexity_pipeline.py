import requests
import json

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
HEADERS = {
    "Authorization": "Bearer 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",  # e.g. "Bearer pplx-f0e2d25e..."
    "Content-Type": "application/json"
}

def generate_queries_with_perplexity(prompt: str) -> str:
    """
    Sends a prompt to Perplexity and returns the assistant's textual response
    containing JSON that fits the Queries schema.
    """
    payload = {
        "model": "llama-3.1-sonar-huge-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Return valid JSON for the Queries schema."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        # You can also override this recency filter based on your scenario
        "search_recency_filter": "month",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }

    try:
        response = requests.post(PERPLEXITY_URL, headers=HEADERS, json=payload)
        response.raise_for_status()

        data = response.json()
        # Typically, the textual content is under data["choices"][0]["message"]["content"]
        assistant_content = data["choices"][0]["message"]["content"]
        return assistant_content
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error calling Perplexity API: {e}")
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Perplexity response format: {e}")


# -----------------------------------
# 3) Redesign news_search with Perplexity
# -----------------------------------
def news_search(query: str, recency_filter: str = "month") -> str:
    """
    Retrieves or summarizes relevant news articles for 'query' from Perplexity,
    filtered by 'recency_filter'. Returns a short summary (text).
    """
    system_message = (
        "You are a a world-ckass professional analyst. You are tasked with creating highly informative brief reports with the information you retrieve online"
        "for the given query. You focus on key data points and the key facts (with their dates) as well as their main consequences the causal relationships between them"
    )
    user_message = (
        f"Search query: {query}\n"
        f"Recency filter: {recency_filter}\n\n"
        "Please research the following topic: "
    )

    payload = {
        "model": "llama-3.1-sonar-huge-128k-online",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "search_recency_filter": recency_filter,
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }

    try:
        response = requests.post(PERPLEXITY_URL, headers=HEADERS, json=payload)
        response.raise_for_status()

        data = response.json()
        assistant_content = data["choices"][0]["message"]["content"]
        return assistant_content

    except requests.exceptions.RequestException as e:
        return f"Error: Unable to retrieve news. Details: {e}"
    except (KeyError, IndexError) as e:
        return f"Error: Unexpected response format from Perplexity. Details: {e}"