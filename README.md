# Sensitive_Data_Redactor

This project is a data pipeline system designed to detect and censor sensitive information in plain text documents. It provides functionality to redact names, dates, phone numbers, addresses, and even concepts from input files.

## Features

- Redacts names, dates, phone numbers, and addresses
- Concept-based redaction
- Processes multiple files using glob patterns
- Generates statistics on redacted content
- Outputs censored files with .censored extension

## Installation

1. Clone this repository : git clone https://github.com/venkatlokesh99/cis6930fa24-project1.git
2. Ensure you have Python 3.x installed
3. Install pipenv if not already installed: pip install pipenv
4. Install project dependencies: pipenv install

Run the program using the following command structure:
```
pipenv run python redactor.py --input '<input_pattern>' 
--names --dates --phones --address 
--concept '<concept>' 
--output '<output_folder>' 
--stats <stats_output>
```

Example :
```
pipenv run python redactor.py --input 'test_folder/*.txt' --names --dates --phone --address --concept 'house' --output 'output/' --stats stderr
```

## Function Descriptions

### `censor_text(text, entities, replacement_char='█')`
Replaces specified entities in the text with a replacement character.
- `text`: The input text to be censored
- `entities`: List of entities to be censored
- `replacement_char`: Character used for censoring (default: '█')
- Returns: Censored text

### `process_file(file_path, output_directory, stats, entities_to_censor, concepts_to_censor)`
Processes a single file, censoring specified entities and concepts.
- `file_path`: Path to the input file
- `output_directory`: Directory to save the censored file
- `stats`: Dictionary to store censoring statistics
- `entities_to_censor`: List of entity types to censor
- `concepts_to_censor`: List of concepts to censor

- **File Reading**: 
   - Opens and reads the content of the file specified by `file_path`.

- **NLP Model Loading**:
   - Loads the SpaCy `en_core_web_trf` model for named entity recognition.
   - If the model is not found, it downloads and loads it.

- **Pattern Definitions**:
   - Defines regex patterns for names in emails, months, phone numbers, addresses, and dates.

- **Concept-based Redaction** (if applicable):
   - If "CONCEPT" is in `entities_to_censor`:
     - Loads the SpaCy `en_core_web_lg` model for word vectors.
     - Processes each sentence and token in the text.
     - Compares each token with the given concepts using cosine similarity.
     - Redacts entire sentences that have tokens similar to the specified concepts.

- **Entity Extraction and Redaction**:
   - **Names**: 
     - Extracts person names using SpaCy's named entity recognition.
     - Finds names in email addresses using regex.
   - **Dates**: 
     - Extracts dates using SpaCy's named entity recognition.
     - Uses regex to find additional date formats.
   - **Phone Numbers**: 
     - Extracts phone numbers using SpaCy's named entity recognition.
     - Uses regex to find additional phone number formats.
   - **Addresses**: 
     - Extracts geographical entities (GPE) using SpaCy.
     - Uses regex to find address patterns.

- **Text Censoring**:
   - Calls the `censor_text` function to replace all identified entities with the censoring character ('█').

- **Saving Redacted File**:
   - Saves the censored text to a new file with the `.censored` extension in the specified output directory.

- **Updating Statistics**:
   - Increments the total number of processed files.
   - Adds the path of the censored file to the list of censored files.
   - Updates the count of censored terms for each category (names, dates, phones, addresses, concepts).

- **Error Handling**:
   - Catches and reports any exceptions that occur during the processing of the file.


### `generate_stats(stats, redacted_texts, stats_output)`
Generates and writes statistics about the censoring process to a file.
- `stats`: Dictionary containing censoring statistics
- `redacted_texts`: List of censored texts
- `stats_output`: File path to write the statistics

### `main()`
Main function that parses command-line arguments and orchestrates the censoring process.
- Processes input files
- Applies censoring based on specified flags
- Generates and outputs statistics


## Test Case Descriptions

## 1. test_address.py

This test file focuses on verifying the address redaction functionality of the redactor.

Key aspects:
- Creates a temporary input file with a sample address.
- Processes the file using the `process_file` function.
- Checks if the specific address is censored in the output file.

## 2. test_concept.py
This test file is designed to test the concept-based redaction feature.

Key aspects:
- Creates an input file with text related to a specific concept.
- Processes the file with a given concept to censor.
- Verifies if sentences containing the concept are redacted.

## 3. test_phones.py
This test case checks the phone number redaction functionality.

Key aspects:
- Prepares an input file with various phone number formats.
- Runs the redaction process targeting phone numbers.
- Ensures all phone number formats are properly censored.

## 4. test_dates.py
This test file verifies the date redaction feature of the redactor.

Key aspects:
- Creates a file with different date formats.
- Processes the file to redact dates.
- Checks if various date formats are successfully censored.

## 5. test_names.py
This test case is focused on testing the name redaction functionality.

Key aspects:
- Prepares input text with various names and name formats.
- Runs the redaction process targeting personal names.
- Verifies if names are properly censored in the output.

These tests collectively ensure that the redactor correctly handles different types of sensitive information across various formats and contexts.

## Bugs and Assumptions

### Bugs
- **Model Loading**: Issues might arise when loading the SpaCy model (en_core_web_trf). If it isn't already installed, the code attempts to download it, which requires internet access.
- **Regex Matching**: The regex used for addresses, dates, and phone numbers may not capture all possible formats, especially those that are unusual or specific to certain regions.
- **Email Redaction Inconsistency**: The code redacts recognizable names within email IDs (e.g., kevin.M.Preto@enron.com will redact kevin.M.Preto), which may not always be accurate.
- **Incomplete Address Redaction**: Not all address formats, like specific pincode structures, may be redacted effectively. Only the formats covered by the implemented regex patterns will be redacted.
- **Concept Mention Redaction Limitation**: Redaction might not comprehensively cover all mentions of concepts. While specific concept terms (e.g., 'kids') are targeted, affiliated words or contextual mentions might not be consistently redacted due to model limitations.
- **Inconsistent Date Redaction**: Non-standard date formats may not be redacted. The patterns implemented primarily cover standard formats, and searching for terms like month names or days might lead to over-redaction of unrelated content.
- **Statistics Variability**: The effectiveness of the model impacts the redaction process, leading to variability in generated statistics. These statistics reflect the number of redacted characters, which may vary across different runs or models.

### Assumptions
- **Concept Matching**: Concepts are identified using exact word boundary regex searches. This simplistic approach may miss some contextual mentions of a concept. Multiple `--concept` flags can be used for different terms related to the same concept.
- **Entity Labels**: It is assumed that SpaCy accurately identifies entity labels such as PERSON for names and DATE for dates.
- **Single Character Redaction**: The redaction character is assumed to be a single character (█), which helps maintain readability in the redacted text.
- **In-place Modification**: The redacted text is created by modifying the original text in-place, requiring the text to be converted to a list before modification.
- **Statistics Structure**: Generated statistics include the count of redacted characters and their locations. This structure is designed for simplicity but may be expanded for more complex scenarios.
- **File Read/Write**: It is assumed that the input files are readable and the output directories are writable, without any permission issues.
- **Glob Patterns**: The `--input` flag uses glob patterns. It assumes that users provide valid glob patterns that correctly match the target files.
- **Mixed Entity Redaction**: Redacting names, dates, addresses, etc., in a single run assumes a sequential process without conflicts in overlapping text regions.
- **Model Assumption**: It assumes that the SpaCy models used are always available and up-to-date, noting that compatibility issues may occur with different versions.
- **Language**: The text is assumed to be in English, based on the use of the en_core_web_trf model.
- **Concept Redaction Scope**: By default, entire sentences containing the concept will be redacted. If a concept appears in multiple contexts, every instance will lead to the redaction of the corresponding sentence.
- **Email Name Detection**: The model attempts to identify and redact names within email addresses. For example, potter.harry@ufl.edu will have potter.harry redacted, but sgoza@ufl.edu will not have sgoza redacted as it is not recognized as a name.
- **Address Types**: Only the address formats covered by the implemented regex patterns will be redacted. Pincodes and other unrecognized formats may not be redacted.
- **Concept Affiliation**: The system targets exact concept words but may not comprehensively cover all affiliated mentions or similar concepts due to model variability.
- **Date Formats**: The model is effective for standard date formats. Non-standard formats may not be redacted, and there's a risk of over-redaction with terms like month names or days.
- **Stats Variability**: The redaction statistics can vary based on the model's performance, providing information on the number of redacted characters, which can differ with each run.
