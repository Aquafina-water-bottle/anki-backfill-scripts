from __future__ import annotations

import argparse
import re

import enum
from pathlib import Path
from os import PathLike
from dataclasses import dataclass
from typing import List

# ========================== from anki-connect =========================== #

# https://github.com/FooSoft/anki-connect#python
import json
import urllib.request


def request(action, **params):
    return {"action": action, "params": params, "version": 6}


def invoke(action, **params):
    requestJson = json.dumps(request(action, **params)).encode("utf-8")
    response = json.load(
        urllib.request.urlopen(
            urllib.request.Request("http://localhost:8765", requestJson)
        )
    )
    if len(response) != 2:
        raise Exception("response has an unexpected number of fields")
    if "error" not in response:
        raise Exception("response is missing required error field")
    if "result" not in response:
        raise Exception("response is missing required result field")
    if response["error"] is not None:
        raise Exception(response["error"])
    return response["result"]


# =========================================================================== #

rx_HTML = re.compile("<.*?>")


def remove_html(expression: str):
    return re.sub(rx_HTML, "", expression)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "file_name",
        type=str,
    )

    # behaves like grep's --context-before and --context-after
    parser.add_argument("--context-before", type=int, default=15)
    parser.add_argument("--context-after", type=int, default=5)
    parser.add_argument("--tag", type=str, default=None)
    parser.add_argument("--note-type", type=str, default="JP Mining Note")
    parser.add_argument("--context-field", type=str, default="AdditionalNotes")
    parser.add_argument("--query", type=str, default=None)

    # default is none as it should attempt to auto-detect based off of file ending
    parser.add_argument("--file-type", type=str, choices=["txt", "epub", "renji"], default=None)

    return parser.parse_args()


def construct_action(id: int, context):
    return {
        "action": "updateNoteFields",
        "version": 6,
        "params": {"note": {"id": id, "fields": {"AdditionalNotes": context}}},
    }


@dataclass
class SentenceInfo:
    note_id: int
    sentence: str
    bolded_text: str | None


class FileType(enum.Enum):
    txt = enum.auto()
    epub = enum.auto()
    #exstatic = enum.auto() # exstatic does not store lines!
    renji = enum.auto()


def query_notes(query) -> list[SentenceInfo]:

    # query = f'"note:JP Mining Note" "tag:{args.tag}" AdditionalNotes:'
    print(f"Querying Anki with: '{query}'")
    notes = invoke("findNotes", query=query)

    if len(notes) == 0:
        return []
    print(f"Query found {len(notes)} notes.")

    print("Getting note info...")
    notes_info = invoke("notesInfo", notes=notes)

    rx_BOLD = re.compile("<b>(.+?)</b>")

    sentence_info_list: list[SentenceInfo] = []

    for note_info in notes_info:
        note_id = note_info["noteId"]
        sentence = remove_html(note_info["fields"]["Sentence"]["value"])

        search_result = rx_BOLD.search(note_info["fields"]["Sentence"]["value"])
        bolded_text: str | None
        if search_result is not None:
            bolded_text = search_result.group(1)
        else:
            bolded_text = None

        sentence_info = SentenceInfo(note_id, sentence, bolded_text)
        sentence_info_list.append(sentence_info)

    return sentence_info_list


def load_lines(path: PathLike, file_type: FileType):
    if file_type == FileType.txt:
        return load_lines_txt(path)
    elif file_type == FileType.renji:
        return load_lines_renji(path)
    else:
        raise NotImplementedError(file_type)


def load_lines_txt(path: PathLike):
    with open(path) as f:
        lines = [x for x in f.read().splitlines() if x.strip()]
    return lines


def load_lines_renji(path: PathLike):
    lines = []
    with open(path) as f:
        json_data = json.load(f)
        for line_data in json_data["bannou-texthooker-lineData"]:
            lines.append(line_data["text"])
    return lines


def search_lines(
    lines: list[str],
    sentence_info_list: list[SentenceInfo],
    context_before: int,
    context_after: int,
    actions: list,
):
    print("Naive search...")

    for sentence_info in sentence_info_list:
        id = sentence_info.note_id
        s = sentence_info.sentence
        word = sentence_info.bolded_text

        for i in range(len(lines)):
            line = lines[i]

            if s in line:
                context_lst = lines[
                    max(0, i - context_before) : min(len(lines), i + context_after)
                ]
                context = "<br>".join(context_lst)
                if word is not None:
                    context = context.replace(word, "<b>" + word + "</b>")
                actions.append(construct_action(id, context))
                print(context)
                break


def main():
    args = get_args()
    path = Path(args.file_name)

    file_type_str = args.file_type
    if file_type_str is None:
        # attempt auto detect
        suffix = path.suffix
        if suffix == ".txt":
            file_type_str = "txt"
        elif suffix == ".epub":
            file_type_str = "epub"
        elif suffix == ".json":
            print("Found json file. Expecting this to be a json file exported from Renji's texthooker-ui.")
            file_type_str = "renji"

    # NOTE: this can error (and we expect it to error if it's an invalid file type)
    try:
        file_type = FileType[file_type_str]
    except KeyError:
        raise RuntimeError("Unable to automatically detect file type. Please specify a valid --file-type")

    lines = load_lines(path, file_type)

    # search for notes with Anki-Connect
    if args.query is not None:
        query = args.query
    else:
        # path.stem is file name without extension
        tag = args.tag
        if tag is None:
            tag = path.stem
        query = f'"note:{args.note_type}" "tag:{tag}" "{args.context_field}:"'

    sentence_info_list = query_notes(query)
    if len(sentence_info_list) == 0:
        print("Cannot find any notes to change. Exiting...")
        return

    # creates multi action to update multiple notes
    actions = []

    search_lines(lines, sentence_info_list, args.context_before, args.context_after, actions)

    print(len(actions))

    confirm = input("Type 'yes' to confirm:\n> ")
    if confirm != "yes":
        print("Reply was not 'yes'. Exiting...")
        return

    print("Updating notes within Anki...")
    invoke("multi", actions=actions)
    print("Done!")


if __name__ == "__main__":
    main()
