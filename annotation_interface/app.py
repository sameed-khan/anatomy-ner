import os
import pandas as pd
import glob
import yaml

from typing import Tuple
from pathlib import Path
from dataclasses import dataclass
from pydantic import BaseModel
from litestar import Litestar, Controller, get, post
from litestar.datastructures import State
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig
from litestar.response import Template
from litestar.static_files import create_static_files_router
from pydantic import BaseModel
from datetime import datetime

# TODO: later move this to a config.yaml file or something similar
CSV_PREFIX = "eval_dataset_web"

@dataclass
class Annotation:
    sentence: str
    label: str
    labeled_rows: int
    progress: float

@dataclass
class UpdateRequest(BaseModel):
    action: str
    label: str = ""

class LabelingController(Controller):
    path = "/label"
    @get("/", sync_to_thread=True)
    async def get_sentence(self, state: State) -> Annotation:
        progress, labrows = calculate_progress(state)
        return Annotation (
            sentence = state.df[state.counter]["finding"],
            label = state.df[state.counter]["anatomic_classification"],
            labeled_rows = labrows,
            progress = progress
        )

    @post("/update", sync_to_thread=True)
    async def update_sentence(self, data: UpdateRequest, state: State) -> Annotation:
        if data.action == "correct":
            state.df[state.counter]["labeled"] = True
            state.counter += 1
            state.num_labeled_rows += 1
        elif data.action == "update":
            state.df[state.counter]["anatomic_classification"] = data.label
            state.df[state.counter]["labeled"] = True
            state.counter += 1
            state.num_labeled_rows += 1
        elif data.action == "delete":
            del state.df[state.counter]
        else:
            raise ValueError("Invalid action")

        progress, labrows = calculate_progress(state)
        return Annotation (
            sentence = state.df[state.counter]["finding"],
            label = state.df[state.counter]["anatomic_classification"],
            labeled_rows = labrows,
            progress = progress
        )

    @get("/undo", sync_to_thread=True)
    async def undo_annotation(self, state: State) -> Annotation:
        """ User presses Ctrl+Z to undo the last annotation """
        if state.counter == 0:
            progress, labrows = calculate_progress(state)
            return Annotation (
                sentence = state.df[state.counter]["finding"],
                label = state.df[state.counter]["anatomic_classification"],
                labeled_rows = labrows,
                progress = progress
            )

        state.counter -= 1
        state.df[state.counter]["anatomic_classification"] = ""
        state.df[state.counter]["labeled"] = False
        progress, labrows = calculate_progress(state)

        return Annotation (
            sentence = state.df[state.counter]["finding"],
            label = state.df[state.counter]["anatomic_classification"],
            labeled_rows = labrows,
            progress = progress
        )


    @get("/debug", sync_to_thread=True)
    async def get_state(self, state: State) -> None:
        print(pd.DataFrame(state.df[state.counter-5:state.counter+5])[["patient_id", "finding", "anatomic_classification", "labeled"]])

def on_shutdown(app: Litestar) -> None:
    timestamp = datetime.now().strftime("%m-%d-%Y__%H-%M")
    filename = f"../data/{CSV_PREFIX}_{timestamp}.csv"
    pd.DataFrame(app.state.df).to_csv(filename, sep="\t", index=False)
    print(f"Wrote file {filename} to disk")

    # Ensure removal of previous older files only if this file was successfully saved
    # TODO: add deletion behaviro to clean up older versions
    # if os.path.exists(filename):
    #     csv_files = [f for f in os.listdir(".") if f.startswith(CSV_PREFIX) and f.endswith(".csv")]
    #     csv_files.sort(reverse=True)

    #     if len(csv_files) > 2:
    #         oldest_file = csv_files[-1]
    #         os.remove(oldest_file)

@get("/", sync_to_thread=False)
def index(state: State) -> Template:
    progress, labeled_rows = calculate_progress(state)

    # Get label options from config.yaml
    with open("config.yaml", "r") as file:
        yaml_data = yaml.safe_load(file)
    
    label_keybindings = []
    for little_dict in yaml_data["keybindings"]:
        items = list(little_dict.items())
        label_keybindings.extend(items)
    return Template("index.html", context={"progress": progress, "labeled_rows": labeled_rows, "keybindings": label_keybindings})

def calculate_progress(state: State) -> Tuple[float, int]:
    """ For updating the progress bar """
    total_rows = len(state.df)
    progress = (state.num_labeled_rows / total_rows) * 100

    return progress, state.num_labeled_rows

def get_newest_csv_file():
    csv_files = glob.glob(f"../data/{CSV_PREFIX}*.csv")
    if csv_files:
        newest_file = max(csv_files, key=os.path.getctime)
        return newest_file
    else:
        return "../data/eval_dataset_05-11-2024.csv"

########### MAIN ###########
new_filename = get_newest_csv_file()
print(f"Reading in file at ../data/{new_filename}")
df = pd.read_csv(new_filename, sep="\t")
num_labeled_rows = len(df[df["labeled"]])
if (df['labeled'] == False).any():
    counter = (df[df["labeled"] == False]).index.min()
else:
    counter = None
df = df.to_dict("records")
print(counter)

app = Litestar(
    route_handlers=[
        index, 
        LabelingController,
        create_static_files_router(path="/static", directories=["static"])
    ], 
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine
    ),
    state=State({"df": df, "counter": counter, "num_labeled_rows": num_labeled_rows}), 
    on_shutdown=[on_shutdown],
    debug=True)
