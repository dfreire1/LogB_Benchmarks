# This script extracts all the energy-relevant values from Gaussian Files
# It creates an excel file with all the information extracted
# It performs calculations of ∆G and ∆H as needed or any other calculations
# It can be used on many files

import os
import re
import pandas as pd

def extract_context_around_patterns(lines, pattern, lines_above, lines_below):
    found_lines = []
    for idx, line in enumerate(lines):
        if pattern in line:
            start = max(0, idx - lines_above)
            end = min(len(lines), idx + lines_below + 1)
            found_lines.extend(lines[start:end])
    return found_lines

def extract_negative_number_from_line(line):
    """Extracts a negative number from a given line."""
    match = re.search(r"-\d+\.\d+", line)
    return match.group(0) if match else None

def extract_specific_data(context, line_number, start_index, end_index):
    if line_number < len(context):
        line = context[line_number]
        if start_index is not None and end_index is not None:
            # Extract substring based on start and end indices
            substring = line[start_index:end_index]
            # Search for a negative number in the substring
            match = re.search(r"-\d+\.\d+", substring)
            return match.group(0) if match else ""
        else:
            # If start_index or end_index is None, return the whole line
            return line
    return ""

def extract_pattern_data(file_path, pattern_config):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        extracted_data = {}
        for pattern_name, config in pattern_config.items():
            context = extract_context_around_patterns(lines, config['pattern'], config['lines_above'], config['lines_below'])
            for line in context:
                extracted_data[pattern_name] = extract_negative_number_from_line(line)
                if extracted_data[pattern_name]:
                    break  # Stop after the first match
        return extracted_data
    
def print_debug_info(debug_info):
    print("Debug Info:")
    for key, value in debug_info.items():
        print(f"{key}: {value}")

def list_out_files(directory):
    path = directory or os.getcwd()
    return [os.path.join(path, file) for file in os.listdir(path) if file.endswith(".out")]

def extract_number_from_filename(filename):
    match = re.search(r'\d+', filename)
    return match.group() if match else None

def format_file_number(num):
    return f"{int(num):02d}"

def calculate_delta_g(gibbs_values, g1, g1s, g2, g2s, g3, g3s):
    G1 = float(gibbs_values.get(g1, 0))
    G1S = float(gibbs_values.get(g1s, 0))
    G2 = float(gibbs_values.get(g2, 0))
    G2S = float(gibbs_values.get(g2s, 0))
    G3 = float(gibbs_values.get(g3, 0))
    G3S = float(gibbs_values.get(g3s, 0))

    delta_g_au = ((G3 - G1 - G2) + (G3S - G3)) - (G1S - G1) - (G2S - G2)
    return delta_g_au

def calculate_delta_h(enthalpy_values, h1, h1s, h2, h2s, h3, h3s):
    H1 = float(enthalpy_values.get(h1, 0))
    H1S = float(enthalpy_values.get(h1s, 0))
    H2 = float(enthalpy_values.get(h2, 0))
    H2S = float(enthalpy_values.get(h2s, 0))
    H3 = float(enthalpy_values.get(h3, 0))
    H3S = float(enthalpy_values.get(h3s, 0))

    delta_h_au = ((H3 - H1 - H2) + (H3S - H3)) - (H1S - H1) - (H2S - H2)
    return delta_h_au

def calculate_logb(delta_g_kcal):
    return -delta_g_kcal / (2.303 * 0.0019858775 * 298.15)

# Configuration

#data_directory = '/Users/dfreire/Documents/TCU/Green_Group/Projects/8_LogB_Benchmarks/Calculations/L08A_H/Conformers'
data_directory = '/Users/dfreire/Documents/TCU/Green_Group/Projects/8_LogB_Benchmarks/Calculations/03_Conformers/Zn/ZnL08b_Crest/F05'

#Different combinations of functionals and basis sets
# A = B3LYP, B = PBE1PBE, C = wB97XD, D = M06, E = M062x, F = M11
# 01 = 6-31+G(d,p), 02 = 6-311+G(2d,2p), 03 = LanL2DZ, 04 = LanL2MB, 05 = def2TZVP

codenames = [
    #"A02", "A03", "A05", "B02", "B03", "B05", "C02", "C03", "C05", "D02", "D03", "D05",
    #"E02", "E03", "E05", "F02", "F03", "F05", "F06", "H05"
    "F05"
]  # List of codenames

# Patterns to understand where is going to find the data in the file

pattern_config = {
    "SCF": {"pattern": "SCF Done:  E(R", "lines_above": 0, "lines_below": 0, "line_number": 0, "start_index": None, "end_index": None},
    "Zero-point": {"pattern": "Sum of electronic and zero-point Energies", "lines_above": 0, "lines_below": 0, "line_number": 0, "start_index": 53, "end_index": 67},
    "Thermal": {"pattern": "Sum of electronic and thermal Energies", "lines_above": 0, "lines_below": 0, "line_number": 0, "start_index": 53, "end_index": 67},
    "Enthalpy": {"pattern": "Sum of electronic and thermal Enthalpies", "lines_above": 0, "lines_below": 0, "line_number": 0, "start_index": 53, "end_index": 67},
    "Gibbs": {"pattern": "Sum of electronic and thermal Free Energies", "lines_above": 0, "lines_below": 0, "line_number": 0, "start_index": 53, "end_index": 67}
}

#In case you need a later starting point to find the data in the file (when there's duplicate patterns)
start_point = None

# Extract data
extracted_data = {"Filename": []}
gibbs_values = {}
enthalpy_values = {}

# Initialize dictionary for storing extracted data to write to Excel
extracted_data = {"Filename": [], "SCF": [], "Zero-point": [], "Thermal": [], "Enthalpy": [], "Gibbs": []}

# Extract data for each file and store in dictionaries
for file in list_out_files(data_directory):
    file_name = os.path.splitext(os.path.basename(file))[0]
    data_from_file = extract_pattern_data(file, pattern_config)
    
    # Store data for Excel
    extracted_data["Filename"].append(file_name)
    for key in ["SCF", "Zero-point", "Thermal", "Enthalpy", "Gibbs"]:
        extracted_value = data_from_file.get(key, "")
        extracted_data[key].append(extracted_value)
        if key == "Gibbs":
            gibbs_values[file_name] = extracted_value
        elif key == "Enthalpy":
            enthalpy_values[file_name] = extracted_value

# Prepare DataFrame for ΔG and ΔH calculations
delta_g_h_data = {"Codename": [], "Combination": [], "ΔG(a.u)": [], "ΔG(kcal/mol)": [], "ΔH(a.u)": [], "ΔH(kcal/mol)": [], "LogB": []}

# For debugging purposes
example_values = {}


# Number of ligand conformers (x) and complexes (y)
for codename in codenames:
    for x in range(1, 39):  # Modify range if needed
        formatted_x = format_file_number(x)
        for y in range(1, 4):  # Modify range if needed
            formatted_y = format_file_number(y)
            combination = f"L{formatted_x}_ML{formatted_y}"

            # Construct file names with codename
            files = [
                f"ZnI_{codename}_of", f"ZnI_{codename}_smd_of",
                f"L08C_{codename}_conf{formatted_x}", f"L08C_{codename}_smd_conf{formatted_x}",
                f"ZnL08Cb_{codename}_conf{formatted_y}", f"ZnL08Cb_{codename}_smd_conf{formatted_y}"
            ]

            # Debugging for A02 L08A_ML08A
            if codename == "F02" or "F03" or "F05" and combination == "L01_ML01":
                example_values = {file: enthalpy_values.get(file, None) for file in files}

            # Calculate ΔG and ΔH
            delta_h_au = calculate_delta_h(enthalpy_values, *files)
            delta_h_kcal = delta_h_au * 627.5
            delta_g_au = calculate_delta_g(gibbs_values, *files)
            delta_g_kcal = delta_g_au * 627.5
            logb = calculate_logb(delta_g_kcal)

            # Append results to delta_g_h_data
            delta_g_h_data["Codename"].append(codename)
            delta_g_h_data["Combination"].append(combination)
            delta_g_h_data["ΔG(a.u)"].append(delta_g_au)
            delta_g_h_data["ΔG(kcal/mol)"].append(delta_g_kcal)
            delta_g_h_data["ΔH(a.u)"].append(delta_h_au)
            delta_g_h_data["ΔH(kcal/mol)"].append(delta_h_kcal)
            delta_g_h_data["LogB"].append(logb)

# Write extracted data to Excel
df_extracted_data = pd.DataFrame(extracted_data)
df_extracted_data.sort_values(by="Filename", inplace=True)

# Write calculations to Excel
df_delta_g_h = pd.DataFrame(delta_g_h_data)
df_delta_g_h.sort_values(by=["Codename", "Combination"], inplace=True)

# Save to Excel file
with pd.ExcelWriter(os.path.join(data_directory or os.getcwd(), "ZnL08_F05_Model1.xlsx"), engine='xlsxwriter') as writer:
    df_extracted_data.to_excel(writer, sheet_name='Extracted Data', index=False)
    df_delta_g_h.to_excel(writer, sheet_name='Calculations', index=False)

# Print debug information
print_debug_info(example_values)
print("Data extraction and calculation completed successfully!")

