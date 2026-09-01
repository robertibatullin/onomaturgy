"""
Deduplication of name csv files, summing up frequencies of duplicate names and removing duplicates.
"""
import csv
import sys


def main():
    """
    Main function to deduplicate a csv file of names.
    """
    if len(sys.argv) != 3:
        print("Usage: python deduplicate.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    name_dict = {}

    with open(input_file, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        next(reader)  # skip header
        for row in reader:
            name, frequency = row[0], int(row[1])
            if name in name_dict:
                name_dict[name] += frequency
            else:
                name_dict[name] = frequency

    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['name', 'frequency'])
        for name, frequency in sorted(name_dict.items()):
            writer.writerow([name, frequency])

if __name__ == "__main__":
    main()
