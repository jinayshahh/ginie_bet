import csv

def search_name_in_csv(name, csv_files):
    for csv_file in csv_files:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if name in row:
                    print(f"Name '{name}' found in {csv_file}")
                    return
    print(f"Name '{name}' not found in any of the CSV files.")

# Example usage
name_to_search = input("Enter a name to search: ")
csv_files = ['ginie_bet_enabled_basketball.csv', 'ginie_bet_enabled_cricket.csv', 'ginie_bet_enabled_football.csv']

search_name_in_csv(name_to_search, csv_files)
