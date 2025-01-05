import pandas as pd
from src.constants import *
from src.sqldb import SQLiteDB


def handle_bootstrap(db: SQLiteDB):

    """---------------------------------------------------INIT DB CHARTS --------------------------------------------"""
    # Init ZETA_POTENTIAL chart
    db.execute_query("""
          CREATE TABLE IF NOT EXISTS Zeta (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              formulation_id TEXT NOT NULL,
              calculated_value REAL NOT NULL
          )
          """)

    # Init TNS chart
    db.execute_query("""
          CREATE TABLE IF NOT EXISTS TNS (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              formulation_id TEXT NOT NULL,
              calculated_value REAL NOT NULL
          )
          """)

    """----------------------------------------------- INIT DIRS ----------------------------------------------------"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def handle_upload(db: SQLiteDB, file):

    # Process the file (you can customize this part)
    if file.filename.endswith(".csv"):
        data = handle_csv_file(os.path.join(UPLOAD_DIR, file.filename))
        experiment = "Zeta"

    else:  # filename endswith ".xlsx", ".xls" can be specified if more options are added
        data = handle_excel_file(os.path.join(UPLOAD_DIR, file.filename))
        experiment = "TNS"

    if data == ERROR:
        return ERROR
    else:
        # inserting data into the DB
        db.execute_query(f"INSERT INTO {experiment} (formulation_id, calculated_value) VALUES (?, ?)", data)
    return 0


def handle_csv_file(file):
    df = pd.read_csv(file, encoding="utf-8-sig")
    df = df.dropna(how="all")          # Drops rows where all elements are NaN
    df = df.dropna(axis=1, how="all")  # Drops columns where all values are NaN

    # Group the formulations triplets and avg their zeta potentials
    grouped_df = df.groupby(['Measurement Type', 'Sample Name']).mean()

    # Get the Zeta Potential of 'STD 1'
    std_1_zeta_potential = grouped_df.loc[("Zeta", "STD 1"), "Zeta Potential (mV)"]

    # Normalize the Zeta Potential with the STD and drop the std
    grouped_df["Zeta Potential (mV)"] = grouped_df["Zeta Potential (mV)"] / std_1_zeta_potential
    grouped_df = grouped_df.drop(("Zeta", "STD 1"))
    res = []
    # Adding (formulation_id,calc_val) tuples into result list
    for index, row in grouped_df.iterrows():
        calculated_value = float(row.iloc[-1])
        if calculated_value <= ZETA_THRESHOLD:
            return -1
        res.append((index[1], calculated_value))

    return res


def handle_excel_file(file):
    df = pd.read_excel(file)

    df = df.dropna(how="all")          # Drops rows where all elements are NaN
    df = df.dropna(axis=1, how="all")  # Drops columns where all values are NaN

    df = df.drop(df.columns[0], axis=1)  # Drop the first irrelevant column
    df = df[1:]                          # Drop the first irrelevant row
    formulation_id = 1
    res = []

    # Process each row in the DataFrame
    for row in df.itertuples(index=False):
        # Define the control group as the last three columns in the row
        control_res = sum(row[-3:])

        # Iterate through the remaining columns in groups of 3
        for i in range(0, len(row) - 3, 3):  # Exclude the control columns & jump on triplets
            formula_res = sum(row[i:i + 3])
            calculated_value = formula_res / control_res
            if calculated_value <= TNS_THRESHOLD:
                return -1

            res.append((f"FORMULATION{formulation_id}", calculated_value))
            formulation_id += 1

    return res
