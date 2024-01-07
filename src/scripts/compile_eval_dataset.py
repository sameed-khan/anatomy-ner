# compile_eval_dataset.py
# Simple script to compile a small evaluation dataset from the mimic-cxr data
# Finds the 50 longest CXR reports that have a "FINDINGS" section, grabs their reports and 
# compiles it into a CSV for easy viewing and hand-labeling.

import os
import re

import pandas as pd

from tqdm.auto import tqdm

def process_file(filepath):
    """
    Process a single file, returning the report text separated by periods
    """
    with open(filepath, "r") as f:
        # Read the entire file as a single string
        content = f.read()

        # Find the start and end of the desired section
        start = content.find("FINDINGS:") + len("FINDINGS:")
        match = re.search(r'[A-Z]+:', content[start:])
        if match:
            end = start + match.start()
        else:
            end = len(content)

        # Extract the desired section, strip leading and trailing whitespace
        section = content[start:end].strip().replace("\n", " ")

    sentences = re.split(r'\.\s+', section)
    rows = []
    for row in sentences:
        if len(row.strip()) == 0:
            continue
        
        finding = row.strip()
        autofinding, all_findings = rough_classify_finding(finding)
        rows.append({
            "filename": filepath,
            "patient_id": filepath.split("/")[-2],
            "finding": row.strip(),
            "anatomic_classification": autofinding,
            "possible_secondary": ";".join(all_findings) 
        })
    return rows

def rough_classify_finding(finding):
    """
    Use naive text matching to roughly classify the finding into one of the anatomic categories.
    """
    MATCH_WORDS = {
        ("lung", "pleur", "pneumothora"):"LUNG/PLEURA/LARGE AIRWAYS",
        ("aort", "vessel", "vasc"):"VESSELS",
        ("mitr", "tricusp", "cardiac silhouette", "heart", "atrium", "atria", "ventricle", "ventric", "ventricular"):"HEART",
        ("mediastin", "hila", "hilum", "hilar", ):"MEDIASTINUM AND HILA",
        ("chest wall",):"CHEST WALL AND LOWER NECK",
        ("hepatic", "hepato"):"LIVER",
        ("choledocho",):"BILE DUCTS",
        ("chole",):"GALLBLADDER",
        ("pancreato",):"PANCREAS",
        ("spleno",):"SPLEEN",
        ("adreno", "adrena"):"ADRENAL GLANDS",
        ("reno", "rena", "renal"):"KIDNEYS AND URETERS",
        ("vesico", "vesica"):"BLADDER",
        ("repro", "repra"):"REPRODUCTIVE ORGANS",
        ("entero",):"BOWEL",
        ("periton", "retroperiton", "lympha", "lymph"):"PERITONEUM/RETROPERITONEUM/LYMPH NODES",
        ("osseous", "ossif", "bone", "osteo"):"BONE AND SOFT TISSUE",
    }

    first_finding = None
    all_findings = []
    for match_list in MATCH_WORDS.keys():
        if any([word in finding.lower() for word in match_list]):
            if first_finding is None:
                first_finding = MATCH_WORDS[match_list]
            all_findings.append(MATCH_WORDS[match_list])
    
    return first_finding, all_findings

if __name__ == "__main__":
    BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
    with open(os.path.join(BASE_DIR, "data", "longest_reports_paths.txt"), "r") as f:
        paths = f.read().splitlines()

    dfrows = []
    for path in tqdm(paths):
        dfrows.extend(process_file(path))

    df = pd.DataFrame(dfrows)
    df.to_csv(os.path.join(BASE_DIR, "data", "eval_dataset.csv"), index=False)