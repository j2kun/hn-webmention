import requests
import indieweb_utils
import sys
import pprint
from bs4 import BeautifulSoup
from urllib.parse import urlparse

DOMAIN = "jeremykun.com"
SEARCH_URL = f"https://hn.algolia.com/api/v1/search?query={DOMAIN}&tags=story&hitsPerPage=20"

def get_post_text(post):
    if post.get("story_text"):
        return post["story_text"]
    elif post.get("comment_text"):
        return post["comment_text"]
    else:
        return ""


def send_webmention(post_url, target_url):
    print(f"Found a link to {DOMAIN} on Hacker News!")
    print("Link to post: " + post_url)
    print("Link to my website: " + target_url)

    try:
        indieweb_utils.send_webmention(post_url, target_url)
    except indieweb_utils.webmentions.discovery.WebmentionEndpointNotFound:
        print("Webmention endpoint not found.")
        return

    print("Webmention sent!")


def main():
    try:
        r = requests.get(SEARCH_URL)
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)

    response = r.json()
    pprint.pp(response)
    num_hits = response["nbHits"]
    num_pages = response["nbPages"]
    print(f"Found {num_hits} posts across {num_pages} paginated search pages.")

    for page in range(0, num_pages):
        print(f"Querying page {page}")
        try:
            r = requests.get(f"{SEARCH_URL}&page={page}")
        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(1)

        response = r.json()
        hn_posts = response["hits"]
        for post in hn_posts:
            post_url = "https://news.ycombinator.com/item?id=" + str(post["objectID"])
            post_http_url = post.get("url")
            if post_http_url is not None and urlparse(post_http_url).netloc == DOMAIN:
                send_webmention(post_url, post_http_url)
                continue

            story_text = get_post_text(post)
            content = BeautifulSoup(story_text, "html.parser")
            links = content.find_all("a")
            for link in links:
                if link.get("href") is None:
                    continue

                domain = urlparse(link.get("href")).netloc
                if domain == DOMAIN:
                    send_webmention(post_url, link.get("href"))


if __name__ == "__main__":
    main()
