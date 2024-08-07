from bs4 import BeautifulSoup
from urllib.parse import urlparse
import argparse
import indieweb_utils
import pprint
import requests
import sys

def get_post_text(post):
    if post.get("story_text"):
        return post["story_text"]
    elif post.get("comment_text"):
        return post["comment_text"]
    else:
        return ""


def send_webmention(post_url, target_url):
    print(f"Found a post: {post_url} -> {target_url}")

    try:
        indieweb_utils.send_webmention(post_url, target_url)
    except indieweb_utils.webmentions.discovery.WebmentionEndpointNotFound:
        print("Webmention endpoint not found.")
        return

    print("Webmention sent!")


def main(domain):
    search_url = f"https://hn.algolia.com/api/v1/search?query={domain}&tags=story&hitsPerPage=20"
    try:
        r = requests.get(search_url)
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
            r = requests.get(f"{search_url}&page={page}")
        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(1)

        response = r.json()
        hn_posts = response["hits"]
        for post in hn_posts:
            post_url = "https://news.ycombinator.com/item?id=" + str(post["objectID"])
            post_http_url = post.get("url")
            if post_http_url is not None and urlparse(post_http_url).netloc == domain:
                send_webmention(post_url, post_http_url)
                continue

            story_text = get_post_text(post)
            content = BeautifulSoup(story_text, "html.parser")
            links = content.find_all("a")
            for link in links:
                if link.get("href") is None:
                    continue

                post_domain = urlparse(link.get("href")).netloc
                if post_domain == domain:
                    send_webmention(post_url, link.get("href"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--domain')
    args = parser.parse_args()
    main(args.domain)
