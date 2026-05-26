"""
build_stopword_file_helper.py
============================

A utility script for targeted text analysis and refinement of the 
application's curated stopword list.

Purpose:
--------
This script provides a focused environment for analyzing word frequencies 
within a specific Project Gutenberg text (e.g., a biologically relevant work). 
By outputting comprehensive frequency counts to TSV files, it enables 
the identification of high-frequency "noise" words—such as common 
linguistic particles or Gutenberg-specific metadata—that should be added to 
'stopwords.txt'. 

This curation process ensures that the main GUI application provides 
meaningful "interesting word" results rather than a list of common words 
generally common in English, such as "the", "and", "of", as well as words
that are common in these scientific biological texts that do not carry 
significant meaning, such as "ann", "seq", "frequently", "chapter", "dr",
"ms", etc.

Features:
---------
- Targeted fetch and metadata extraction from a specific Project Gutenberg ID.
- Comprehensive TSV output of all non-stopword tokens (frequency >= 5).
- Interactive 'Top K' terminal display for quick data validation.
- Standardized directory management for parsed output files.

Author: Karen R. Christie
Original Date: November 2025
Module-level Docstring Updated: May 2026
================================================================================
"""

"""
build_stopword_file_helper.py
============================

A utility script for targeted text analysis and refinement of the 
application's curated stopword list.

Purpose:
--------
This script provides a focused environment for analyzing word frequencies 
within a specific Project Gutenberg text (e.g., a biologically relevant work). 
By outputting comprehensive frequency counts to TSV files, it enables 
the identification of high-frequency "noise" words—such as common 
linguistic particles or Gutenberg-specific metadata—that should be added to 
'stopwords.txt'. 

This curation process ensures that the main GUI application provides 
meaningful "interesting word" results rather than common English particles 
(e.g., "the", "and", "of") or frequent but low-value tokens common in some
scientific or literary texts (e.g., "ann", "seq", "frequently", "chapter", 
"dr", "ms").

Features:
---------
- Targeted fetch and metadata extraction from a specific Project Gutenberg ID.
- Comprehensive TSV output of all non-stopword tokens (frequency >= 5).
- Interactive 'Top K' terminal display for quick data validation.
- Standardized directory management for parsed output files.

Author: Karen R. Christie
Original Date: November 2025
Module-level Docstring Updated: May 2026
"""

# use 45917



import re
import requests
from html.parser import HTMLParser
from collections import Counter
import string
import csv
import os


# ================================
# Helper: Safe filename cleaner
# ================================
def make_filename_safe(s):
    """Clean unsafe characters for use in filenames."""
    s = s.strip().replace(" ", "_")
    s = re.sub(r"[^a-zA-Z0-9_\-]", "", s)
    s = re.sub(r"_+", "_", s)
    return s or "Unknown"


# ================================
# Helper: Make Gutenberg link
# ================================
def make_gutenberg_link(book_id):
    """
    Accepts a Gutenberg book ID like '15491' or 'pg15491'
    and returns a URL to the plain text file.
    """
    book_id = str(book_id).lower().replace("pg", "").strip()
    return f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"


# ================================
# Helper: Extract title + author
# ================================
def extract_title_and_author(text):
    """
    Look for 'Title:' and 'Author:' lines in Gutenberg header.
    Returns (safe_title, safe_author_last)
    """
    title = "UnknownTitle"
    author_last = "UnknownAuthor"

    for line in text.splitlines():
        if line.lower().startswith("title:"):
            title = make_filename_safe(line.split(":", 1)[1].strip())

        if line.lower().startswith("author:"):
            author = line.split(":", 1)[1].strip()
            author_last = make_filename_safe(author.split()[-1])

    return title, author_last


# ================================
# Helper: Load stopwords
# ================================
def load_stopwords(filepath="stopwords.txt"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        print("Error loading stopwords:", e)
        return set()


# ================================
# Helper: Ask user for top_k
# ================================
def get_top_k():
    """
    Ask the user for the number of top-frequency words (10–40).
    - Enter defaults to 10.
    - Invalid input reprompts.
    - Out-of-range input is clamped.
    """
    while True:
        user_input = input("\nEnter # of top frequent words to display (10–40) [Enter=10]: ").strip()

        if user_input == "":
            print("Using default: 10")
            return 10

        if not user_input.isdigit():
            print("❌ Please enter a valid number (10–40) or press Enter for default.")
            continue

        user_k = int(user_input)

        if user_k < 10:
            print("⚠️ Minimum allowed is 10. Using 10.")
            return 10
        if user_k > 40:
            print("⚠️ Maximum allowed is 40. Using 40.")
            return 40

        return user_k


# ================================
# HTML Parser class
# ================================
class MyHTMLParser(HTMLParser):
    """Parses text and collects alphabetic tokens."""

    def __init__(self):
        super().__init__()
        self._words = []

    def handle_data(self, data):
        for token in data.split():
            cleaned = token.strip(string.punctuation)
            if not cleaned:
                continue
            if any(ch.isdigit() for ch in cleaned):
                continue
            alphabetic = cleaned.replace("-", "").replace("'", "").isalpha()
            if alphabetic:
                self._words.append(cleaned.lower())

    # ----------------------------
    # Frequency analysis
    # ----------------------------
    def frequency(self, n, stopwords=None, outfile=None, top_k=10):
        """
        Count word frequencies, excluding stopwords.
        Write full results to TSV.
        Return + print the top_k items.
        """

        if stopwords is None:
            stopwords = set()

        if outfile is None:
            raise ValueError("outfile must be provided.")

        # Clamp top_k 10–40
        if top_k < 10:
            top_k = 10
        elif top_k > 40:
            top_k = 40

        counts = Counter(self._words)

        # Words that meet minimum frequency and are not stopwords
        filtered_items = [(w, c) for w, c in counts.items()
                          if c >= n and w not in stopwords]

        # Alphabetical for file output
        filtered_alpha = sorted(filtered_items, key=lambda x: x[0])

        # Sorted by descending frequency for top-k
        filtered_freq = sorted(filtered_items, key=lambda x: x[1], reverse=True)

        try:
            # Write full TSV results
            with open(outfile, "w", newline="", encoding="utf-8") as out:
                writer = csv.writer(out, delimiter="\t")
                for word, count in filtered_alpha:
                    writer.writerow([word, count])

            print(f"\n📄 Full word counts written to {outfile}")

            # Get top_k
            top_items = filtered_freq[:top_k]

            # Print them
            if top_items:
                print(f"\n🔥 Top {top_k} highest-frequency non-stopword tokens (count ≥ {n}):\n")
                for i, (word, count) in enumerate(top_items, start=1):
                    print(f"{i:>2}. {word:<20} {count}")

            return top_items

        except Exception as e:
            print("Error writing output file:", e)
            return []


# ================================
# MAIN PROGRAM
# ================================
if __name__ == "__main__":

    # --- Ask for Gutenberg ID ---
    user_book_id = input("Enter Gutenberg book ID (e.g., 15491 or pg15491): ").strip()
    if not user_book_id:
        print("No ID provided — exiting.")
        exit()

    # Build URL
    link = make_gutenberg_link(user_book_id)
    print("\nFetching:", link)

    # Fetch book text
    try:
        resp = requests.get(link)
        resp.raise_for_status()
        text = resp.text
    except requests.RequestException as e:
        print("Error fetching book:", e)
        exit()

    # Extract metadata
    book_title, author_last = extract_title_and_author(text)
    print("\nDetected title:", book_title)
    print("Detected author last name:", author_last)

    # Make output filename

    # Ensure subdirectory exists
    output_dir = "wordCountFiles"
    os.makedirs(output_dir, exist_ok=True)

    # Build full path in that directory
    outfile = os.path.join(
        output_dir,
        f"word_counts_{author_last}_{book_title}.tsv"
        )
    print("Output file dir/name:", outfile)

    # Load stopwords
    stopwords = load_stopwords()

    # Ask for top_k
    top_k = get_top_k()
    print(f"\n✔ Will display top {top_k} words.\n")

    # Parse and analyze text
    parser = MyHTMLParser()
    parser.feed(text.lower())

    # Compute frequencies
    top_items = parser.frequency(
        5,
        stopwords=stopwords,
        outfile=outfile,
        top_k=top_k
    )


