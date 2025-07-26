#!/usr/bin/env python3
"""
Example script demonstrating how to use the YAML processor module.
"""
from beangrid.core.processor import FormulaProcessor
from beangrid.core.yaml_processor import create_sample_workbook
from beangrid.core.yaml_processor import load_workbook_from_yaml
from beangrid.core.yaml_processor import save_workbook_to_yaml


def main():
    """Demonstrate YAML workbook processing."""
    print("Creating sample workbook...")
    workbook = create_sample_workbook()

    # Save to YAML file
    yaml_file = "sample_workbook.yaml"
    print(f"Saving workbook to {yaml_file}...")
    save_workbook_to_yaml(workbook, yaml_file)

    # Load from YAML file
    print(f"Loading workbook from {yaml_file}...")
    loaded_workbook = load_workbook_from_yaml(yaml_file)

    # Process the workbook with formulas
    print("Processing workbook with formulas...")
    processor = FormulaProcessor()
    processed_workbook = processor.process_workbook(loaded_workbook)

    # Display results
    print("\nProcessed workbook results:")
    for sheet in processed_workbook.sheets:
        print(f"\nSheet: {sheet.name}")
        print("-" * 40)

        # Create a simple grid display
        cell_dict = sheet.get_cell_dict()
        max_row = max(
            int(cell_id[1:]) for cell_id in cell_dict.keys() if cell_id[1:].isdigit()
        )
        max_col = max(
            ord(cell_id[0]) - ord("A") + 1
            for cell_id in cell_dict.keys()
            if cell_id[0].isalpha()
        )

        # Print header
        for col in range(max_col):
            col_letter = chr(ord("A") + col)
            print(f"{col_letter:>8}", end="")
        print()

        # Print rows
        for row in range(1, max_row + 1):
            print(f"{row:>4}", end="")
            for col in range(max_col):
                col_letter = chr(ord("A") + col)
                cell_id = f"{col_letter}{row}"
                cell = cell_dict.get(cell_id)
                if cell:
                    value = cell.value or "N/A"
                    print(f"{value:>8}", end="")
                else:
                    print(f"{'':>8}", end="")
            print()

    print(f"\nYAML file saved as: {yaml_file}")
    print("You can edit this file and reload it to test different scenarios.")


if __name__ == "__main__":
    main()
