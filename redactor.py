import re
import spacy
import argparse
import os
import glob
import sys
from collections import defaultdict
import warnings

# Ignore all warnings
warnings.filterwarnings("ignore")

def censor_text(text, entities, replacement_char='█'):
    for entity in entities:
        if isinstance(entity, str):
            text = text.replace(entity, replacement_char * len(entity))
        else:
            text = text.replace(entity.text, replacement_char * len(entity.text))
    return text

def process_file(file_path, output_directory, stats, entities_to_censor, concepts_to_censor):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        try:
            nlp = spacy.load("en_core_web_trf")
        except IOError:
            print("SpaCy model not found. Downloading...")
            spacy.cli.download("en_core_web_trf")
            nlp = spacy.load("en_core_web_trf")

        doc = nlp(text)

        names_pattern = re.compile(r'([a-zA-Z0-9_.+-]+)@')
        months_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|' \
                  r'Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)'
        phone_number_pattern = re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b')
        address_pattern = re.compile(
                                r'\b\d{1,6}\s+[A-Za-z0-9\s]+\s(?:St(?:reet)?|Ave(?:nue)?|Rd(?:oad)?|Blvd(?:oulevard)?|'
                                r'Ln(?:ane)?|Dr(?:ive)?|Sq(?:uare)?|Pl(?:ace)?|Trl(?:ail)?|Ct(?:ourt)?'
                                r'Way|Pkwy(?:arkway)?|Ter(?:race)?|Lp(?:oop)?)\s*'
                                r'(?:Apt|Suite|Ste|#)?\s*\d*\s*'
                                r'(?:,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5})?\b'
                            )
        
        date_pattern = re.compile(
            r'(?:^|\b)(?:'
            r'(\d{1,2})(?:st|nd|rd|th)?[-/\s](' + months_pattern + r')[-/\s](\d{2,4})|'  # e.g., 28th July 2024
            r'(\d{4})[-/\s](\d{1,2})[-/\s](\d{1,2})|'                                    # e.g., 2024/07/28 or 2024-07-28
            r'(' + months_pattern + r')\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})|'       # e.g., July 28th, 2024
            r'(\d{1,2})\s+(' + months_pattern + r')\s+(\d{4})|'                          # e.g., 28 July 2024
            r'(\d{1,2})[/\s](\d{1,2})[/\s](\d{4})|'                                     # e.g., 01/11/2001 or 28/07/2024
            r'(' + months_pattern + r')\s+(\d{4})|'                                      # e.g., July 2024
            r'(\d{1,2})[-/\s](\d{1,2})[-/\s](\d{2})|'
            r'(' + months_pattern + r')|'
            r')(?:\b|$)',
            re.IGNORECASE
        )

        names = []
        names_in_email = []
        dates = []
        date_matches = []
        phones = []
        phone_numbers = []
        addresses = []
        addresses_hf = []
        address_list = []


        if("CONCEPT" in entities_to_censor):
            try:
                nlp2 = spacy.load("en_core_web_lg")
            except IOError:
                print("SpaCy model not found. Downloading...")
                spacy.cli.download("en_core_web_lg")
                nlp2 = spacy.load("en_core_web_lg")
            redacted_sentences = []
            doc = nlp2(text)
            concept_docs = [nlp2(concept) for concept in concepts_to_censor]  # Processing concepts once

            for sent in doc.sents:  # Iterate over each sentence
                for token in sent:  # Iterate over each token in the sentence
                    for concept_doc in concept_docs:  # Iterate over processed concepts
                        # Calculate cosine similarity between token's doc and concept's doc
                        if token.similarity(concept_doc) > 0.75:  # Choose a threshold for similarity
                            redacted_sentences.append(sent.text)
                            break  # Stop checking other tokens if a match is found

            for sentence in redacted_sentences:
                text = text.replace(sentence, '█' * len(sentence))  # Redact the sentence

        # Extract entities based on flags
        if ("PERSON" in entities_to_censor):
            names = [ent for ent in doc.ents if ent.label_ == 'PERSON']
            names_in_email = re.findall(names_pattern, text)
        if ("DATE" in entities_to_censor):
            dates = [ent for ent in doc.ents if ent.label_ == 'DATE']
            date_matches = [" ".join(filter(None, match)) for match in re.findall(date_pattern, text)]
        if ("PHONE" in entities_to_censor):
            phones = [ent for ent in doc.ents if ent.label_ == 'PHONE']
            phone_numbers = re.findall(phone_number_pattern, text)
        # addresses = [ent for ent in doc.ents if ent.label_ == 'ADDRESS']
        if ("ADDRESS" in entities_to_censor):
            addresses = [ent for ent in doc.ents if ent.label_ == 'GPE']
            address_list = re.findall(address_pattern, text)

        # Censor sensitive information
        censored_text = censor_text(text, names_in_email +  addresses + addresses_hf + address_list + names + dates + date_matches + phones + phone_numbers)

        # Save redacted file
        file_name = os.path.basename(file_path)
        output_path = os.path.join(output_directory, f"{file_name}.censored")
        with open(output_path, 'w', encoding='utf-8') as redacted_file:
            redacted_file.write(censored_text)

# Update statistics
        stats['total_files'] += 1
        stats['censored_files'].append(output_path)
        stats['censored_terms']['names'] += len(names)
        stats['censored_terms']['dates'] += len(dates)
        stats['censored_terms']['phones'] += len(phones)
        stats['censored_terms']['phones'] += len(phone_numbers)
        stats['censored_terms']['addresses'] += len(addresses)
        stats['censored_terms']['concept'] += len(redacted_sentences)

    except Exception as e:
        print(f"Error processing file {file_path}: {e}", file=sys.stderr)

def generate_stats(stats, redacted_texts, stats_output):
    with open(stats_output, 'w', encoding='utf-8') as stats_file:
        stats_file.write(f"Total processed files: {stats['total_files']}\n\n")
        stats_file.write("Censored Terms:\n")
        for term, count in stats['censored_terms'].items():
            stats_file.write(f"{term.capitalize()}: {count}\n")

        stats_file.write("\nCensored Files:\n")
        for censored_file in stats['censored_files']:
            if isinstance(censored_file, str):  # Check if it's a string
                stats_file.write(f"File: {censored_file}\n")
            else:
                stats_file.write(f"File: {censored_file['file_path']}\n")

def main():
    parser = argparse.ArgumentParser(description="Censor sensitive information in plain text documents.")
    parser.add_argument('--input', nargs='+', help="Input files using glob patterns.")
    parser.add_argument('--output', help="Output directory for censored files.")
    parser.add_argument('--names', action='store_true', help="Censor names.")
    parser.add_argument('--dates', action='store_true', help="Censor dates.")
    parser.add_argument('--phones', action='store_true', help="Censor phone numbers.")
    parser.add_argument('--address', action='store_true', help="Censor addresses.")
    parser.add_argument('--stats', type=str, default='stderr', help="Statistics output destination.")
    parser.add_argument('--concept', action='append', help='<Required> Set flag')

    args = parser.parse_args()
    print(args)

    if not args.input:
        print("Please provide input files using --input flag.")
        sys.exit(1)

    output_directory = args.output
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    entities_to_censor = []
    concepts_to_censor = []
    if args.names:
        entities_to_censor.append('PERSON')
    if args.dates:
        entities_to_censor.append('DATE')
    if args.phones:
        entities_to_censor.append('PHONE')
    if args.address:
        entities_to_censor.append('ADDRESS')
    if args.concept:
        entities_to_censor.append('CONCEPT')
        for concept in args.concept:
            concepts_to_censor.append(concept)

    stats = {'total_files': 0, 'censored_files': [], 'censored_terms': defaultdict(int)}

    redacted_texts = []
    for pattern in args.input:
        files = glob.glob(pattern)
        print("FILE", files)
        for file_path in files:
            redacted_text = process_file(file_path, args.output, stats, entities_to_censor,concepts_to_censor)
            redacted_texts.append(f"File: {file_path}\n{redacted_text}")

    if args.stats == 'stderr':
        print("Statistics:\n", stats, file=sys.stderr)
    elif args.stats == 'stdout':
        print("Statistics:\n", stats)
    else:
        generate_stats(stats, redacted_texts, args.stats)

if __name__ == "__main__":
    main()
