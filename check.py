from fuzzywuzzy import fuzz

def fuzzy_similarity(str1, str2):
    return fuzz.ratio(str1, str2) / 100  # normalize 0..1

# Example
print(fuzzy_similarity("बामन्देह", "बामनदे"))