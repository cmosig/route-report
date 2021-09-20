import pandas as pd
import metadata


all_codes = pd.read_csv("other_data/country_code_mapping.csv")["iso"].to_list()

metadata.download_and_preprocess_metadata(all_codes, redownload=False, reprocess=False, cleanup=True)
